from dune_client.client import DuneClient
from dune_client.query import QueryBase

from tycho_liquidity_analysis.config import Settings


def client(settings: Settings | None = None) -> DuneClient:
    settings = settings or Settings()
    if not settings.dune_api_key:
        msg = "DUNE_API_KEY is required"
        raise RuntimeError(msg)
    return DuneClient(api_key=settings.dune_api_key)


def validate_auth() -> None:
    query = QueryBase(name="tycho_liquidity_analysis_auth_check", query_sql="select 1 as ok")
    result = client().run_query(query)
    rows = result.result.rows if result.result else []
    if not rows or rows[0].get("ok") != 1:
        msg = f"Unexpected Dune auth check result: {rows}"
        raise RuntimeError(msg)
