from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from tycho_liquidity_analysis.config import RAW_DATA_DIR, REPO_ROOT


MANIFEST_PATH = REPO_ROOT / "data" / "dune_manifest.json"
DASHBOARD_NAME = "Tycho Liquidity Coverage Analysis"
DASHBOARD_SLUG = "tycho-liquidity-coverage-analysis"


@dataclass(frozen=True)
class VisualizationSpec:
    key: str
    query_key: str
    name: str
    type: str
    options: dict[str, Any]


@dataclass(frozen=True)
class QuerySpec:
    key: str
    name: str
    sql_path: Path
    description: str


QUERY_SPECS = [
    QuerySpec(
        key="dashboard_summary",
        name="Tycho Liquidity Coverage - Summary",
        sql_path=REPO_ROOT / "queries" / "dashboard_summary.sql",
        description="Headline 7d/30d DEX volume and Uniswap V4 + Ekubo share.",
    ),
    QuerySpec(
        key="protocol_volume",
        name="Tycho Liquidity Coverage - Protocol Volume",
        sql_path=REPO_ROOT / "queries" / "protocol_volume_7d_30d.sql",
        description="7d/30d volume share by Dune protocol mapping for Tycho target protocols.",
    ),
    QuerySpec(
        key="protocol_version_breakdown",
        name="Tycho Liquidity Coverage - Dune Version Breakdown",
        sql_path=REPO_ROOT / "queries" / "protocol_version_breakdown.sql",
        description="Raw Dune project/version breakdown used to validate Tycho protocol mapping.",
    ),
    QuerySpec(
        key="top_pools",
        name="Tycho Liquidity Coverage - Top Pools",
        sql_path=REPO_ROOT / "queries" / "top_pools_by_pair_protocol.sql",
        description="Top target-token contracts/pools by 7d/30d DEX volume.",
    ),
    QuerySpec(
        key="token_pair_coverage",
        name="Tycho Liquidity Coverage - Token Pair Coverage",
        sql_path=REPO_ROOT / "queries" / "token_pair_coverage.sql",
        description="Target-token pair coverage by protocol.",
    ),
    QuerySpec(
        key="indexing_inputs",
        name="Tycho Liquidity Coverage - Indexing Inputs",
        sql_path=REPO_ROOT / "queries" / "indexing_strategy_inputs.sql",
        description="Dune volume inputs joined to Tycho extractor start-block metadata.",
    ),
    QuerySpec(
        key="all_venue_coverage",
        name="Tycho Liquidity Coverage - All Venue Coverage",
        sql_path=REPO_ROOT / "queries" / "all_venue_coverage.sql",
        description="Coverage of current Tycho target protocols against all Dune dex.trades target-token venues.",
    ),
    QuerySpec(
        key="non_tycho_venue_breakdown",
        name="Tycho Liquidity Coverage - Non-Tycho Venue Breakdown",
        sql_path=REPO_ROOT / "queries" / "non_tycho_venue_breakdown.sql",
        description="Largest non-Tycho venue/project/pair buckets in Dune dex.trades.",
    ),
    QuerySpec(
        key="aggregator_orderflow_breakdown",
        name="Tycho Liquidity Coverage - Aggregator Orderflow",
        sql_path=REPO_ROOT / "queries" / "aggregator_orderflow_breakdown.sql",
        description="Aggregator/orderflow layer volume, distinct from underlying DEX venue liquidity.",
    ),
    QuerySpec(
        key="aggregator_route_topology_by_size",
        name="Tycho Liquidity Coverage - Aggregator Route Topology By Size",
        sql_path=REPO_ROOT / "queries" / "aggregator_route_topology_by_size.sql",
        description="Aggregator transactions classified by underlying Tycho AMM, RFQ, or other venue rows.",
    ),
]


VISUALIZATION_SPECS = [
    VisualizationSpec(
        key="total_30d_counter",
        query_key="dashboard_summary",
        name="Total 30d Volume",
        type="counter",
        options={
            "counterColName": "total_volume_30d_usd",
            "rowNumber": 1,
            "stringDecimal": 0,
            "stringPrefix": "$",
            "stringSuffix": "",
            "counterLabel": "30d target-set volume",
            "coloredPositiveValues": False,
            "coloredNegativeValues": False,
        },
    ),
    VisualizationSpec(
        key="v4_ekubo_share_counter",
        query_key="dashboard_summary",
        name="V4 + Ekubo 30d Share",
        type="counter",
        options={
            "counterColName": "v4_ekubo_share_30d",
            "rowNumber": 1,
            "stringDecimal": 2,
            "stringPrefix": "",
            "stringSuffix": "",
            "counterLabel": "Uniswap V4 + Ekubo share",
            "coloredPositiveValues": False,
            "coloredNegativeValues": False,
        },
    ),
    VisualizationSpec(
        key="protocol_30d_share",
        query_key="protocol_volume",
        name="30d Volume Share by Protocol",
        type="chart",
        options={
            "globalSeriesType": "pie",
            "sortX": True,
            "showDataLabels": True,
            "columnMapping": {"protocol": "x", "volume_30d_usd": "y"},
            "seriesOptions": {"volume_30d_usd": {"type": "pie", "yAxis": 0, "zIndex": 0}},
        },
    ),
    VisualizationSpec(
        key="protocol_volume_table",
        query_key="protocol_volume",
        name="Protocol 7d/30d Coverage",
        type="table",
        options={
            "itemsPerPage": 25,
            "columns": [
                {
                    "name": "protocol",
                    "title": "Protocol",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "volume_7d_usd",
                    "title": "7d Volume",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
                {
                    "name": "share_7d",
                    "title": "7d Share",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
                {
                    "name": "volume_30d_usd",
                    "title": "30d Volume",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
                {
                    "name": "share_30d",
                    "title": "30d Share",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
            ],
        },
    ),
    VisualizationSpec(
        key="version_breakdown_table",
        query_key="protocol_version_breakdown",
        name="Dune Project/Version Breakdown",
        type="table",
        options={
            "itemsPerPage": 25,
            "columns": [
                {
                    "name": "project",
                    "title": "Dune Project",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "version",
                    "title": "Version",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "trades_7d",
                    "title": "7d Trades",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
                {
                    "name": "volume_7d_usd",
                    "title": "7d Volume",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
            ],
        },
    ),
    VisualizationSpec(
        key="top_pools_table",
        query_key="top_pools",
        name="Top Target-Token Pools",
        type="table",
        options={
            "itemsPerPage": 25,
            "columns": [
                {
                    "name": "protocol",
                    "title": "Protocol",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "pool_id",
                    "title": "Contract/Pool",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "token_pair",
                    "title": "Pair",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "volume_7d_usd",
                    "title": "7d Volume",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
                {
                    "name": "volume_30d_usd",
                    "title": "30d Volume",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
            ],
        },
    ),
    VisualizationSpec(
        key="token_pair_table",
        query_key="token_pair_coverage",
        name="Target Token-Pair Coverage",
        type="table",
        options={
            "itemsPerPage": 25,
            "columns": [
                {
                    "name": "token0_symbol",
                    "title": "Token 0",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "token1_symbol",
                    "title": "Token 1",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "protocol",
                    "title": "Protocol",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "volume_7d_usd",
                    "title": "7d Volume",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
                {
                    "name": "volume_30d_usd",
                    "title": "30d Volume",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
            ],
        },
    ),
    VisualizationSpec(
        key="indexing_inputs_table",
        query_key="indexing_inputs",
        name="Indexing Strategy Inputs",
        type="table",
        options={
            "itemsPerPage": 25,
            "columns": [
                {
                    "name": "protocol",
                    "title": "Protocol",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "coverage_class",
                    "title": "Class",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "tycho_start_block",
                    "title": "Tycho Start Block",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
                {
                    "name": "volume_7d_usd",
                    "title": "7d Volume",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
                {
                    "name": "volume_30d_usd",
                    "title": "30d Volume",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
            ],
        },
    ),
    VisualizationSpec(
        key="all_venue_coverage_table",
        query_key="all_venue_coverage",
        name="All Dune Venue Coverage",
        type="table",
        options={
            "itemsPerPage": 10,
            "columns": [
                {
                    "name": "category",
                    "title": "Category",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "volume_30d_usd",
                    "title": "30d Volume",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
                {
                    "name": "share_30d",
                    "title": "30d Share",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
            ],
        },
    ),
    VisualizationSpec(
        key="non_tycho_venue_table",
        query_key="non_tycho_venue_breakdown",
        name="Largest Non-Tycho Venue Buckets",
        type="table",
        options={
            "itemsPerPage": 25,
            "columns": [
                {
                    "name": "category",
                    "title": "Category",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "project",
                    "title": "Project",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "version",
                    "title": "Version",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "token_pair",
                    "title": "Pair",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "volume_30d_usd",
                    "title": "30d Volume",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
            ],
        },
    ),
    VisualizationSpec(
        key="aggregator_orderflow_table",
        query_key="aggregator_orderflow_breakdown",
        name="Aggregator / Orderflow Layer",
        type="table",
        options={
            "itemsPerPage": 25,
            "columns": [
                {
                    "name": "project",
                    "title": "Project",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "version",
                    "title": "Version",
                    "type": "normal",
                    "alignContent": "left",
                    "isHidden": False,
                },
                {
                    "name": "trades",
                    "title": "Trades",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
                {
                    "name": "volume_30d_usd",
                    "title": "30d Volume",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
                {
                    "name": "share_30d",
                    "title": "30d Share",
                    "type": "normal",
                    "alignContent": "right",
                    "isHidden": False,
                },
            ],
        },
    ),
]


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"queries": {}, "visualizations": {}, "dashboard": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(manifest: dict[str, Any], path: Path = MANIFEST_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_dune(args: list[str], timeout: int = 600, attempts: int = 4) -> dict[str, Any]:
    completed: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, attempts + 1):
        completed = subprocess.run(
            ["dune", *args],
            cwd=REPO_ROOT,
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        if completed.returncode == 0:
            break
        msg = completed.stderr.strip() or completed.stdout.strip()
        if "429" not in msg and "Too many requests" not in msg:
            raise RuntimeError(f"dune {' '.join(args)} failed: {msg}")
        if attempt < attempts:
            time.sleep(10 * attempt)
    if completed is None or completed.returncode != 0:
        msg = "" if completed is None else completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"dune {' '.join(args)} failed: {msg}")
    output = completed.stdout.strip()
    if not output:
        return {}
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Dune command did not return JSON: {output}") from exc


def extract_id(payload: dict[str, Any], *keys: str) -> int:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return int(value)
    for value in payload.values():
        if isinstance(value, dict):
            try:
                return extract_id(value, *keys)
            except KeyError:
                pass
    raise KeyError(f"Could not find any ID key {keys} in {payload}")


def validate_cli() -> dict[str, Any]:
    whoami = run_dune(["whoami", "-o", "json"], timeout=60)
    result = run_dune(["query", "run-sql", "--sql", "select 1 as ok", "-o", "json"], timeout=120)
    rows = result.get("result", {}).get("rows", [])
    if not rows or rows[0].get("ok") != 1:
        msg = f"Unexpected Dune validation result: {result}"
        raise RuntimeError(msg)
    return {"whoami": whoami, "auth_check": result}


def publish_queries(manifest: dict[str, Any]) -> dict[str, Any]:
    manifest.setdefault("queries", {})
    for spec in QUERY_SPECS:
        sql = spec.sql_path.read_text(encoding="utf-8")
        existing = manifest["queries"].get(spec.key, {})
        query_id = existing.get("id")
        if query_id:
            run_dune(
                [
                    "query",
                    "update",
                    str(query_id),
                    "--name",
                    spec.name,
                    "--description",
                    spec.description,
                    "--sql",
                    sql,
                    "-o",
                    "json",
                ]
            )
        else:
            payload = run_dune(
                [
                    "query",
                    "create",
                    "--name",
                    spec.name,
                    "--description",
                    spec.description,
                    "--sql",
                    sql,
                    "-o",
                    "json",
                ]
            )
            query_id = extract_id(payload, "query_id", "id")
        manifest["queries"][spec.key] = {
            "id": int(query_id),
            "name": spec.name,
            "sql_path": str(spec.sql_path.relative_to(REPO_ROOT)),
        }
    return manifest


def publish_visualizations(manifest: dict[str, Any]) -> dict[str, Any]:
    manifest.setdefault("visualizations", {})
    for spec in VISUALIZATION_SPECS:
        query_id = manifest["queries"][spec.query_key]["id"]
        options = json.dumps(spec.options, separators=(",", ":"))
        existing = manifest["visualizations"].get(spec.key, {})
        viz_id = existing.get("id")
        if viz_id:
            run_dune(
                [
                    "visualization",
                    "update",
                    str(viz_id),
                    "--name",
                    spec.name,
                    "--type",
                    spec.type,
                    "--options",
                    options,
                    "-o",
                    "json",
                ]
            )
        else:
            payload = run_dune(
                [
                    "visualization",
                    "create",
                    "--query-id",
                    str(query_id),
                    "--name",
                    spec.name,
                    "--type",
                    spec.type,
                    "--options",
                    options,
                    "-o",
                    "json",
                ]
            )
            viz_id = extract_id(payload, "visualization_id", "id")
        manifest["visualizations"][spec.key] = {
            "id": int(viz_id),
            "name": spec.name,
            "query_key": spec.query_key,
        }
    return manifest


def publish_dashboard(manifest: dict[str, Any]) -> dict[str, Any]:
    viz_ids = [str(manifest["visualizations"][spec.key]["id"]) for spec in VISUALIZATION_SPECS]
    text_widgets = json.dumps(
        [
            {
                "text": (
                    "# Tycho Liquidity Coverage Analysis\n"
                    "Public Dune dashboard for protocol coverage, top target-token pools, "
                    "and indexing strategy inputs. Python notebooks in the repo perform "
                    "internal scoring and Tycho log analysis."
                )
            }
        ],
        separators=(",", ":"),
    )
    dashboard_id = manifest.get("dashboard", {}).get("id")
    if dashboard_id:
        payload = run_dune(
            [
                "dashboard",
                "update",
                str(dashboard_id),
                "--name",
                DASHBOARD_NAME,
                "--slug",
                DASHBOARD_SLUG,
                "--text-widgets",
                text_widgets,
                "--visualization-widgets",
                json.dumps(
                    [{"visualization_id": int(viz_id)} for viz_id in viz_ids],
                    separators=(",", ":"),
                ),
                "--columns-per-row",
                "2",
                "-o",
                "json",
            ]
        )
    else:
        payload = run_dune(
            [
                "dashboard",
                "create",
                "--name",
                DASHBOARD_NAME,
                "--text-widgets",
                text_widgets,
                "--visualization-ids",
                ",".join(viz_ids),
                "--columns-per-row",
                "2",
                "-o",
                "json",
            ]
        )
        dashboard_id = extract_id(payload, "dashboard_id", "id")
    manifest["dashboard"] = {
        "id": int(dashboard_id),
        "name": DASHBOARD_NAME,
        "slug": DASHBOARD_SLUG,
        "url": f"https://dune.com/leovigna/{DASHBOARD_SLUG}",
    }
    return manifest


def publish_all() -> dict[str, Any]:
    manifest = load_manifest()
    manifest = publish_queries(manifest)
    save_manifest(manifest)
    manifest = publish_visualizations(manifest)
    save_manifest(manifest)
    manifest = publish_dashboard(manifest)
    save_manifest(manifest)
    return manifest


def export_saved_queries(
    manifest: dict[str, Any] | None = None,
    output_dir: Path = RAW_DATA_DIR,
    limit: int = 0,
) -> dict[str, Path]:
    manifest = manifest or load_manifest()
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for key, query in manifest.get("queries", {}).items():
        payload = run_dune(
            [
                "query",
                "run",
                str(query["id"]),
                "--limit",
                str(limit),
                "--timeout",
                "600",
                "-o",
                "json",
            ],
            timeout=700,
        )
        rows = payload.get("result", {}).get("rows", [])
        path = output_dir / f"{key}.json"
        path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths[key] = path
    return paths


def normalize_exports(raw_dir: Path = RAW_DATA_DIR) -> dict[str, Path]:
    from tycho_liquidity_analysis.config import PROCESSED_DATA_DIR

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}
    aliases = {
        "aggregator_orderflow_breakdown": "aggregator_orderflow_breakdown",
        "all_venue_coverage": "all_venue_coverage",
        "protocol_volume": "protocol_volumes",
        "non_tycho_venue_breakdown": "non_tycho_venue_breakdown",
        "top_pools": "top_pools",
        "token_pair_coverage": "token_pair_coverage",
        "indexing_inputs": "indexing_inputs",
    }
    for raw_path in sorted(raw_dir.glob("*.json")):
        rows = json.loads(raw_path.read_text(encoding="utf-8"))
        df = pl.DataFrame(rows) if rows else pl.DataFrame()
        name = aliases.get(raw_path.stem, raw_path.stem)
        output_path = PROCESSED_DATA_DIR / f"{name}.parquet"
        df.write_parquet(output_path)
        outputs[name] = output_path
    return outputs
