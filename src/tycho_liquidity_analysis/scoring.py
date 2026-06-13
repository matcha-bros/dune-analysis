import polars as pl


def score_pools(pools: pl.DataFrame) -> pl.DataFrame:
    required = {"protocol", "pool_id", "volume_7d_usd", "volume_30d_usd"}
    missing = required - set(pools.columns)
    if missing:
        msg = f"pool table missing required columns: {sorted(missing)}"
        raise ValueError(msg)

    max_7d = pools.select(pl.col("volume_7d_usd").max()).item() or 1
    max_30d = pools.select(pl.col("volume_30d_usd").max()).item() or 1

    return pools.with_columns(
        [
            (pl.col("volume_7d_usd") / max_7d).alias("volume_7d_share_of_top"),
            (pl.col("volume_30d_usd") / max_30d).alias("volume_30d_share_of_top"),
            (
                ((pl.col("volume_7d_usd").fill_null(0) / max_7d) * 0.65)
                + ((pl.col("volume_30d_usd").fill_null(0) / max_30d) * 0.35)
            ).alias("relevance_score"),
        ]
    ).sort("relevance_score", descending=True)


def protocol_volume_share(protocols: pl.DataFrame) -> pl.DataFrame:
    required = {"protocol", "volume_7d_usd", "volume_30d_usd"}
    missing = required - set(protocols.columns)
    if missing:
        msg = f"protocol table missing required columns: {sorted(missing)}"
        raise ValueError(msg)

    totals = protocols.select(
        pl.col("volume_7d_usd").sum().alias("total_7d"),
        pl.col("volume_30d_usd").sum().alias("total_30d"),
    ).row(0, named=True)

    return protocols.with_columns(
        [
            (pl.col("volume_7d_usd") / totals["total_7d"]).alias("share_7d"),
            (pl.col("volume_30d_usd") / totals["total_30d"]).alias("share_30d"),
        ]
    ).sort("volume_30d_usd", descending=True)
