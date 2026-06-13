from pathlib import Path

import polars as pl
import typer

from tycho_liquidity_analysis import dune
from tycho_liquidity_analysis.config import PROCESSED_DATA_DIR, REPORTS_DIR
from tycho_liquidity_analysis.reports import (
    write_protocol_coverage,
    write_start_blocks,
    write_top_pools,
)

app = typer.Typer(no_args_is_help=True)


@app.command()
def validate_auth() -> None:
    """Run a tiny Dune query to validate API credentials."""
    dune.validate_auth()
    typer.echo("Dune auth OK")


@app.command()
def build_reports(
    protocols_path: Path = PROCESSED_DATA_DIR / "protocol_volumes.parquet",
    pools_path: Path = PROCESSED_DATA_DIR / "top_pools.parquet",
    reports_dir: Path = REPORTS_DIR,
) -> None:
    """Generate Markdown/CSV/YAML reports from processed Parquet inputs."""
    reports_dir.mkdir(parents=True, exist_ok=True)

    protocols = pl.read_parquet(protocols_path)
    pools = pl.read_parquet(pools_path)

    write_protocol_coverage(protocols, reports_dir / "protocol_coverage.md")
    write_top_pools(pools, reports_dir / "top_pools.csv")
    write_start_blocks({}, reports_dir / "start_blocks.yaml")
    (reports_dir / "indexing_strategy.md").write_text(
        "# Indexing Strategy\n\nTODO: fill from scored pool/protocol outputs.\n",
        encoding="utf-8",
    )
    typer.echo(f"Wrote reports to {reports_dir}")

