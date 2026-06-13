import polars as pl

from tycho_liquidity_analysis.scoring import protocol_volume_share, score_pools


def test_protocol_volume_share_sums_to_one() -> None:
    protocols = pl.DataFrame(
        {
            "protocol": ["uniswap_v4", "uniswap_v3"],
            "volume_7d_usd": [25.0, 75.0],
            "volume_30d_usd": [10.0, 90.0],
        }
    )

    result = protocol_volume_share(protocols)

    assert result.select(pl.col("share_7d").sum()).item() == 1.0
    assert result.select(pl.col("share_30d").sum()).item() == 1.0


def test_score_pools_orders_by_relevance() -> None:
    pools = pl.DataFrame(
        {
            "protocol": ["uniswap_v4", "uniswap_v3"],
            "pool_id": ["0xnew", "0xold"],
            "volume_7d_usd": [100.0, 10.0],
            "volume_30d_usd": [200.0, 1000.0],
        }
    )

    result = score_pools(pools)

    assert result["pool_id"][0] == "0xnew"
