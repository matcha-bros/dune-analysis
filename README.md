# Dune Liquidity Coverage Analysis

Reproducible analysis repo for deciding whether Tycho catch-up can be reduced to under 10 hours while preserving most major executable liquidity.

The first pass uses Dune SQL for onchain aggregation and Python with Polars for local normalization, scoring, and reports.

## Setup

```bash
uv sync
cp .env.example .env
```

Set `DUNE_API_KEY` in `.env`.

Optional variables:

- `ETH_RPC_URL` for later quote/slippage validation.
- `TYCHO_URL=http://localhost:4242` for comparing against a local Tycho instance.

## Workflow

1. Validate Dune auth:

   ```bash
   uv run tycho-liquidity validate-auth
   ```

2. Run targeted Dune queries from `queries/` and cache the results under `data/raw/`.

3. Normalize cached outputs to Parquet under `data/processed/`.

4. Generate reports:

   ```bash
   uv run tycho-liquidity build-reports
   ```

## Outputs

- `reports/protocol_coverage.md`
- `reports/top_pools.csv`
- `reports/indexing_strategy.md`
- `reports/start_blocks.yaml`

