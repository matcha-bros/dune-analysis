# Dune Liquidity Coverage Analysis

Research repo for deciding which Ethereum liquidity Tycho should index or query
for the router MVP, and where Tycho-backed routing is likely to compete with
hosted aggregators.

This repo is for analysis only: Dune SQL, Python/Polars pipelines, notebooks,
competitor API research, and generated reports. Rust simulator, protocol, and
quote-engine implementation work belongs in the sibling Tycho repo.

## Current Takeaways

- Current Tycho target protocols cover about `79%` of all 30d target-token
  Dune `dex.trades` venue volume.
- The largest non-Tycho venue gap is other onchain DeFi, especially Fluid, not
  primarily private market-maker flow.
- RFQ/intent/API-style venue rows are meaningful but smaller, about `4%` of the
  all-venue target-token sample.
- Starting Tycho from late override blocks is not currently acceptable. Late
  start blocks in reports are timing-only estimates, not valid state configs.
- Best MVP benchmark pairs are high-volume non-pegged pairs where hosted Tycho
  already covers most routeable liquidity, especially `USDC-WETH`, `USDT-WETH`,
  and `WBTC-WETH`.

## Where To Start

| Question | Start here |
| --- | --- |
| What share of liquidity does Tycho cover? | `reports/all_venue_coverage.md`, `reports/protocol_coverage.md` |
| Which pairs are good MVP benchmarks? | `docs/pair_protocol_coverage.md`, `notebooks/04_hosted_tycho_pair_coverage.ipynb` |
| Where do competitors actually route? | `docs/competitor_route_topology.md`, `queries/aggregator_route_topology_by_size.sql` |
| How do we compare quotes against LI.FI/Uniswap/1inch? | `docs/competitor_quote_api_research.md`, `scripts/compare-no-key-quotes.sh` |
| What Rust quote API is required? | `docs/tycho_pricing_api_dependency.md` |
| How do we update the Dune dashboard? | `uv run tycho-liquidity dune publish` |

The public Dune dashboard is:

https://dune.com/leovigna/tycho-liquidity-coverage-analysis

## Repo Map

```text
queries/                         Dune SQL, one query per dataset/dashboard widget
src/tycho_liquidity_analysis/     Python CLI, Dune publishing/export, scoring, log parsing
notebooks/                        Internal analysis notebooks
docs/                             Research notes and interpretation
reports/                          Generated Markdown/CSV/YAML outputs
data/raw/                         Cached Dune JSON exports, gitignored
data/processed/                   Normalized Parquet outputs, gitignored
scripts/                          Small comparison/smoke-test scripts
```

Generated files under `data/` and most generated files under `reports/` are
intentionally ignored. Regenerate them locally with the commands below.

## Setup

```bash
uv sync
cp .env.example .env
```

Set `DUNE_API_KEY` in `.env`, or authenticate the Dune CLI with `dune auth`.

Optional variables:

- `ETH_RPC_URL` for quote/slippage validation.
- `TYCHO_URL=http://localhost:4242` for local Tycho comparisons.
- `TYCHO_DIRECT_URL=http://127.0.0.1:8099/quote/direct` for Rust direct quote
  API comparisons.
- `LIFI_API_KEY`, `UNISWAP_API_KEY`, `ONEINCH_API_KEY` for hosted aggregator
  quote comparisons. LI.FI has a no-key path for basic smoke tests.

## Main Workflow

Validate Dune access:

```bash
uv run tycho-liquidity dune validate
```

Publish or update saved Dune queries, visualizations, and the dashboard:

```bash
uv run tycho-liquidity dune publish
```

Export saved Dune query results and normalize to Parquet:

```bash
uv run tycho-liquidity dune export
```

Parse local Tycho indexing logs from the sibling simulation repo:

```bash
uv run tycho-liquidity parse-tycho-logs
```

Generate reports:

```bash
uv run tycho-liquidity build-reports
```

Open notebooks:

```bash
uv run jupyter lab notebooks
```

## Research Tracks

### 1. Liquidity And Indexing Coverage

Use this track to understand how much executable liquidity current Tycho
protocol coverage captures, which protocols dominate, and why late start blocks
are not yet valid.

Key files:

```text
queries/all_venue_coverage.sql
queries/non_tycho_venue_breakdown.sql
queries/protocol_volume_7d_30d.sql
queries/indexing_strategy_inputs.sql
notebooks/01_dune_data_quality.ipynb
notebooks/02_liquidity_scoring.ipynb
notebooks/03_indexing_strategy.ipynb
reports/all_venue_coverage.md
reports/indexing_strategy.md
```

### 2. Pair And Protocol Coverage

Use this track to choose benchmark pairs where Tycho can simulate a large share
of relevant liquidity.

Key files:

```text
docs/pair_protocol_coverage.md
notebooks/04_hosted_tycho_pair_coverage.ipynb
queries/token_pair_coverage.sql
queries/top_pools_by_pair_protocol.sql
reports/hosted_tycho_validation.md
```

### 3. Competitor Route Topology

Use Dune for historical route-topology distribution and Tenderly simulation for
exact fresh quote topology.

```bash
uv run tycho-liquidity lifi-topology --amount 10000000000
```

Key files:

```text
docs/competitor_route_topology.md
docs/competitor_quote_api_research.md
queries/aggregator_orderflow_breakdown.sql
queries/aggregator_route_topology_by_size.sql
src/tycho_liquidity_analysis/lifi_topology.py
```

### 4. Tycho Rust Quote API Dependency

Analysis that compares against our router depends on the Rust quote API in the
sibling Tycho fork.

Key file:

```text
docs/tycho_pricing_api_dependency.md
```

## Public Safety

Do not commit `.env`, Dune result caches, generated Parquet, local dashboard
manifests, or API responses with private credentials. The committed notebooks
and SQL should be reproducible from public Dune tables plus your local API
credentials.

Saved Dune object IDs are stored in `data/dune_manifest.json`, which is
intentionally ignored by Git.
