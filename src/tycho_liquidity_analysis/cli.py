from pathlib import Path

import polars as pl
import typer

from tycho_liquidity_analysis import dune, dune_cli
from tycho_liquidity_analysis.config import PROCESSED_DATA_DIR, REPORTS_DIR, Settings
from tycho_liquidity_analysis.lifi_topology import (
    DEFAULT_SENDER,
    USDC,
    WETH,
    TopologyArgs,
    analyze_lifi_topology,
)
from tycho_liquidity_analysis.reports import (
    recommended_start_block_overrides,
    recommended_start_blocks,
    write_all_venue_coverage,
    write_indexing_strategy,
    write_protocol_coverage,
    write_start_blocks,
    write_top_pools,
)
from tycho_liquidity_analysis.tycho_logs import parse_tycho_inputs

app = typer.Typer(no_args_is_help=True)
dune_app = typer.Typer(no_args_is_help=True)
app.add_typer(dune_app, name="dune")


@app.command()
def validate_auth() -> None:
    """Run a tiny Dune query to validate API credentials."""
    dune.validate_auth()
    typer.echo("Dune auth OK")


@dune_app.command("validate")
def dune_validate() -> None:
    """Validate authenticated Dune CLI access."""
    result = dune_cli.validate_cli()
    handle = result.get("whoami", {}).get("handle") or result.get("whoami", {}).get("Handle")
    typer.echo(f"Dune CLI auth OK{f' for {handle}' if handle else ''}")


@dune_app.command("publish")
def dune_publish() -> None:
    """Create or update saved Dune queries, visualizations, and dashboard."""
    manifest = dune_cli.publish_all()
    typer.echo(f"Published dashboard: {manifest['dashboard']['url']}")


@dune_app.command("export")
def dune_export(normalize: bool = True) -> None:
    """Run saved Dune queries from the manifest and cache their results."""
    paths = dune_cli.export_saved_queries()
    typer.echo(f"Exported {len(paths)} Dune query results")
    if normalize:
        outputs = dune_cli.normalize_exports()
        typer.echo(f"Wrote {len(outputs)} processed Parquet files")


@app.command()
def build_reports(
    protocols_path: Path = PROCESSED_DATA_DIR / "protocol_volumes.parquet",
    pools_path: Path = PROCESSED_DATA_DIR / "top_pools.parquet",
    all_venue_path: Path = PROCESSED_DATA_DIR / "all_venue_coverage.parquet",
    non_tycho_path: Path = PROCESSED_DATA_DIR / "non_tycho_venue_breakdown.parquet",
    aggregator_path: Path = PROCESSED_DATA_DIR / "aggregator_orderflow_breakdown.parquet",
    tycho_estimates_path: Path = PROCESSED_DATA_DIR / "tycho_indexing_estimates.parquet",
    reports_dir: Path = REPORTS_DIR,
) -> None:
    """Generate Markdown/CSV/YAML reports from processed Parquet inputs."""
    reports_dir.mkdir(parents=True, exist_ok=True)

    protocols = pl.read_parquet(protocols_path)
    pools = pl.read_parquet(pools_path)
    all_venue = pl.read_parquet(all_venue_path) if all_venue_path.exists() else pl.DataFrame()
    non_tycho = pl.read_parquet(non_tycho_path) if non_tycho_path.exists() else pl.DataFrame()
    aggregator = pl.read_parquet(aggregator_path) if aggregator_path.exists() else pl.DataFrame()
    estimates = (
        pl.read_parquet(tycho_estimates_path) if tycho_estimates_path.exists() else pl.DataFrame()
    )

    write_protocol_coverage(protocols, reports_dir / "protocol_coverage.md")
    write_top_pools(pools, reports_dir / "top_pools.csv")
    if not all_venue.is_empty() and not non_tycho.is_empty() and not aggregator.is_empty():
        write_all_venue_coverage(
            all_venue,
            non_tycho,
            aggregator,
            reports_dir / "all_venue_coverage.md",
        )
    if not estimates.is_empty():
        write_indexing_strategy(protocols, estimates, reports_dir / "indexing_strategy.md")
        write_start_blocks(
            {
                "configured_core": recommended_start_blocks(estimates),
                "ten_hour_overrides": recommended_start_block_overrides(estimates),
            },
            reports_dir / "start_blocks.yaml",
        )
    else:
        write_start_blocks({}, reports_dir / "start_blocks.yaml")
        (reports_dir / "indexing_strategy.md").write_text(
            "# Indexing Strategy\n\nNo Tycho indexing estimates were available.\n",
            encoding="utf-8",
        )
    typer.echo(f"Wrote reports to {reports_dir}")


@app.command()
def parse_tycho_logs(
    simulation_dir: Path | None = None,
    output_dir: Path = PROCESSED_DATA_DIR,
) -> None:
    """Parse sibling Tycho extractor config/logs into processed Parquet inputs."""
    settings = Settings()
    simulation_dir = simulation_dir or settings.tycho_simulation_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    frames = parse_tycho_inputs(simulation_dir)
    outputs = {
        "configs": output_dir / "tycho_extractor_configs.parquet",
        "progress": output_dir / "tycho_sync_progress.parquet",
        "estimates": output_dir / "tycho_indexing_estimates.parquet",
    }
    for key, frame in frames.items():
        frame.write_parquet(outputs[key])
    typer.echo(f"Wrote Tycho indexing data to {output_dir}")


@app.command()
def lifi_topology(
    amount: int = typer.Option(1_000_000_000, help="Raw input amount. Default is 1000 USDC."),
    from_token: str = typer.Option(USDC, help="Input token address."),
    to_token: str = typer.Option(WETH, help="Output token address."),
    sender: str = typer.Option(DEFAULT_SENDER, help="Simulation sender with enough input balance."),
    slippage: str = typer.Option("0.005", help="LI.FI quote slippage."),
    gas: int = typer.Option(8_000_000, help="Tenderly swap simulation gas limit."),
    save_prefix: str = typer.Option("", help="Optional prefix for saved quote and bundle JSON."),
) -> None:
    """Fetch a LI.FI quote, simulate it, and print realized swap topology."""
    analyze_lifi_topology(
        TopologyArgs(
            from_token=from_token,
            to_token=to_token,
            amount=amount,
            sender=sender,
            slippage=slippage,
            gas=gas,
            save_prefix=save_prefix,
        )
    )
