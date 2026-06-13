from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = REPO_ROOT / "data" / "processed"
REPORTS_DIR = REPO_ROOT / "reports"


class Settings(BaseSettings):
    dune_api_key: str | None = None
    eth_rpc_url: str | None = None
    tycho_url: str = "http://localhost:4242"

    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

