from pathlib import Path

from tycho_liquidity_analysis.tycho_logs import parse_sync_progress, read_extractor_configs


def test_parse_sync_progress(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "run.log").write_text(
        '2026-06-13T05:59:19Z INFO extractor_id="uniswap_v4" '
        'blocks_per_minute="2302.50" blocks_processed=2763 height=21703000 '
        'estimated_current=25306617 time_remaining="26h05m" name="SyncProgress"\n',
        encoding="utf-8",
    )

    result = parse_sync_progress(log_dir)

    assert result.height == 1
    assert result["protocol"][0] == "uniswap_v4"
    assert result["blocks_per_minute"][0] == 2302.5


def test_read_extractor_configs_normalizes_vm_prefix(tmp_path: Path) -> None:
    config = tmp_path / "local-extractors.yaml"
    config.write_text(
        """
extractors:
  vm:curve:
    name: "vm:curve"
    chain: "ethereum"
    implementation_type: "Vm"
    start_block: 9906598
""",
        encoding="utf-8",
    )

    result = read_extractor_configs(config)

    assert result["protocol"][0] == "curve"
    assert result["start_block"][0] == 9906598
