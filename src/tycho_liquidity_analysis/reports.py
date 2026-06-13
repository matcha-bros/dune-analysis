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


def write_indexing_strategy(
    protocol_volumes: pl.DataFrame,
    indexing_estimates: pl.DataFrame,
    path: Path,
) -> None:
    coverage = protocol_volume_share(protocol_volumes)
    joined = indexing_estimates.join(
        coverage.select("protocol", "volume_30d_usd", "share_30d"),
        on="protocol",
        how="left",
    ).sort("volume_30d_usd", descending=True)

    under_10 = joined.filter(pl.col("estimated_hours_from_config_start") <= 10)
    new_protocols = joined.filter(pl.col("protocol").is_in(["uniswap_v4", "ekubo_v2"]))

    lines = [
        "# Indexing Strategy",
        "",
        "This report combines Dune liquidity coverage with observed Tycho `SyncProgress` log speed.",
        "Estimated hours are directional and should be treated as an observed catch-up model.",
        "",
        "## Recommendation",
        "",
    ]

    if new_protocols.height:
        share = new_protocols.select(pl.col("share_30d").sum()).item()
        max_hours = new_protocols.select(pl.col("estimated_hours_from_config_start").max()).item()
        proposed = new_protocols.select(pl.col("proposed_start_block_for_10h").min()).item()
        lines.extend(
            [
                "- Start the first router demo with `uniswap_v4` and `ekubo_v2` as the core reduced set.",
                f"- That set accounts for approximately {share:.2%} of target 30d Dune volume.",
                f"- Observed catch-up estimate from configured start blocks is up to {max_hours:.1f} hours.",
                f"- To target 10h, override core protocol start blocks to no earlier than approximately {proposed}.",
                "- Seed older must-have pools separately if route quality depends on pools created before the override.",
                "",
            ]
        )

    if under_10.height:
        protocols = ", ".join(under_10["protocol"].to_list())
        lines.extend(["## Protocols Estimated Under 10h", "", protocols, ""])

    lines.extend(
        [
            "## Observed Estimates",
            "",
            joined.select(
                "protocol",
                "start_block",
                "observed_blocks_per_minute",
                "estimated_hours_from_config_start",
                "proposed_start_block_for_10h",
                "volume_30d_usd",
                "share_30d",
            ).write_csv(),
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def recommended_start_blocks(
    indexing_estimates: pl.DataFrame,
) -> dict[str, int]:
    if indexing_estimates.is_empty():
        return {}
    selected = indexing_estimates.filter(pl.col("protocol").is_in(["uniswap_v4", "ekubo_v2"]))
    return dict(
        zip(selected["protocol"].to_list(), selected["start_block"].to_list(), strict=False)
    )


def recommended_start_block_overrides(indexing_estimates: pl.DataFrame) -> dict[str, int]:
    if (
        indexing_estimates.is_empty()
        or "proposed_start_block_for_10h" not in indexing_estimates.columns
    ):
        return {}
    selected = indexing_estimates.filter(pl.col("protocol").is_in(["uniswap_v4", "ekubo_v2"]))
    return dict(
        zip(
            selected["protocol"].to_list(),
            selected["proposed_start_block_for_10h"].to_list(),
            strict=False,
        )
    )
