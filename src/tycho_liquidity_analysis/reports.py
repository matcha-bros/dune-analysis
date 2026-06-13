from pathlib import Path

import polars as pl
from ruamel.yaml import YAML

from tycho_liquidity_analysis.scoring import protocol_volume_share, score_pools


def write_protocol_coverage(protocols: pl.DataFrame, path: Path) -> None:
    coverage = protocol_volume_share(protocols)
    v4_ekubo = coverage.filter(pl.col("protocol").is_in(["uniswap_v4", "ekubo_v2"]))

    lines = [
        "# Protocol Coverage",
        "",
        "## Volume Share",
        "",
        coverage.select(
            "protocol",
            "volume_7d_usd",
            "share_7d",
            "volume_30d_usd",
            "share_30d",
        ).write_csv(),
        "## Uniswap V4 + Ekubo",
        "",
        f"- 7d share: {v4_ekubo.select(pl.col('share_7d').sum()).item():.2%}",
        f"- 30d share: {v4_ekubo.select(pl.col('share_30d').sum()).item():.2%}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_top_pools(pools: pl.DataFrame, path: Path) -> None:
    score_pools(pools).write_csv(path)


def write_start_blocks(start_blocks: dict[str, int], path: Path) -> None:
    yaml = YAML()
    yaml.default_flow_style = False
    with path.open("w", encoding="utf-8") as output:
        yaml.dump({"start_blocks": start_blocks}, output)

