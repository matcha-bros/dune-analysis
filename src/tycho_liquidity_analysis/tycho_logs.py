from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import polars as pl
from ruamel.yaml import YAML


SYNC_RE = re.compile(
    r'extractor_id="(?P<protocol>[^"]+)".*?'
    r'blocks_per_minute="(?P<blocks_per_minute>[0-9.]+)".*?'
    r"blocks_processed=(?P<blocks_processed>[0-9]+).*?"
    r"height=(?P<height>[0-9]+).*?"
    r"estimated_current=(?P<estimated_current>[0-9]+).*?"
    r'time_remaining="(?P<time_remaining>[^"]+)"'
)


@dataclass(frozen=True)
class ExtractorConfig:
    protocol: str
    start_block: int
    implementation_type: str


def normalize_protocol_name(name: str) -> str:
    return name.removeprefix("vm:")


def read_extractor_configs(path: Path) -> pl.DataFrame:
    yaml = YAML(typ="safe")
    data = yaml.load(path.read_text(encoding="utf-8"))
    rows = []
    for key, value in data.get("extractors", {}).items():
        rows.append(
            {
                "extractor_key": key,
                "protocol": normalize_protocol_name(value["name"]),
                "start_block": int(value["start_block"]),
                "implementation_type": value.get("implementation_type", ""),
            }
        )
    return pl.DataFrame(rows)


def parse_sync_progress(log_dir: Path) -> pl.DataFrame:
    rows = []
    for path in sorted(log_dir.glob("*.log")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = SYNC_RE.search(line)
            if not match:
                continue
            row = match.groupdict()
            rows.append(
                {
                    "log_file": path.name,
                    "protocol": normalize_protocol_name(row["protocol"]),
                    "blocks_per_minute": float(row["blocks_per_minute"]),
                    "blocks_processed": int(row["blocks_processed"]),
                    "height": int(row["height"]),
                    "estimated_current": int(row["estimated_current"]),
                    "time_remaining": row["time_remaining"],
                }
            )
    if not rows:
        return pl.DataFrame(
            schema={
                "log_file": pl.String,
                "protocol": pl.String,
                "blocks_per_minute": pl.Float64,
                "blocks_processed": pl.Int64,
                "height": pl.Int64,
                "estimated_current": pl.Int64,
                "time_remaining": pl.String,
            }
        )
    return pl.DataFrame(rows)


def latest_sync_by_protocol(progress: pl.DataFrame) -> pl.DataFrame:
    if progress.is_empty():
        return progress
    return progress.group_by("protocol").tail(1)


def estimate_indexing_times(configs: pl.DataFrame, progress: pl.DataFrame) -> pl.DataFrame:
    latest = latest_sync_by_protocol(progress)
    if latest.is_empty():
        return configs.with_columns(
            [
                pl.lit(None, dtype=pl.Float64).alias("observed_blocks_per_minute"),
                pl.lit(None, dtype=pl.Float64).alias("estimated_hours_from_config_start"),
            ]
        )

    joined = configs.join(
        latest.select("protocol", "blocks_per_minute", "estimated_current"),
        on="protocol",
        how="left",
    )
    return joined.with_columns(
        [
            pl.col("blocks_per_minute").alias("observed_blocks_per_minute"),
            (
                (pl.col("estimated_current") - pl.col("start_block"))
                / pl.col("blocks_per_minute")
                / 60
            ).alias("estimated_hours_from_config_start"),
            (pl.col("estimated_current") - (pl.col("blocks_per_minute") * 60 * 10))
            .ceil()
            .cast(pl.Int64)
            .alias("proposed_start_block_for_10h"),
        ]
    ).drop("blocks_per_minute")


def parse_tycho_inputs(simulation_dir: Path) -> dict[str, pl.DataFrame]:
    config_path = simulation_dir / "local-extractors.yaml"
    log_dir = simulation_dir / "logs"
    configs = read_extractor_configs(config_path)
    progress = parse_sync_progress(log_dir)
    estimates = estimate_indexing_times(configs, progress)
    return {"configs": configs, "progress": progress, "estimates": estimates}
