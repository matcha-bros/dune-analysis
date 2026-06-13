from tycho_liquidity_analysis.dune_cli import extract_id


def test_extract_id_finds_nested_query_id() -> None:
    payload = {"query": {"query_id": 12345}}

    assert extract_id(payload, "query_id", "id") == 12345


def test_extract_id_accepts_top_level_id() -> None:
    payload = {"id": "67890"}

    assert extract_id(payload, "dashboard_id", "id") == 67890
