# Tycho Pricing API Dependency

Some analysis commands compare Python/Dune output against the Rust quote API in
the sibling Tycho fork:

```text
../tycho-mainnet-simulation
```

Keep implementation work for the quote engine in that repo. Keep Python,
notebooks, Dune SQL, competitor API analysis, and benchmark reports in this
`dune-analysis` repo.

## Start The Rust Quote API

From `../tycho-mainnet-simulation`:

```bash
set -a
. ./.env
set +a

DIRECT_SWAP_API_BIND=127.0.0.1:8099 \
TYCHO_URL=tycho-fynd-ethereum.propellerheads.xyz \
TOKEN_MIN_QUALITY=100 \
MAX_DAYS_SINCE_LAST_TRADE=3 \
TVL_GT=10 \
SCAN_PROTOCOLS=uniswap_v2,uniswap_v3,sushiswap_v2,pancakeswap_v2,pancakeswap_v3,uniswap_v4,ekubo_v2 \
cargo run -q -p tycho-simulation --example direct_swap_search_api
```

The Rust API exposes:

```text
POST http://127.0.0.1:8099/quote/direct
```

Example request:

```bash
curl -sS http://127.0.0.1:8099/quote/direct \
  -H 'content-type: application/json' \
  -d '{
    "sellToken":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "buyToken":"0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "amountIn":"1000000000"
  }'
```

## Run Python Analysis Against The API

From this `dune-analysis` repo, set:

```bash
TYCHO_DIRECT_URL=http://127.0.0.1:8099/quote/direct
```

Current commands:

```bash
scripts/compare-no-key-quotes.sh
uv run tycho-liquidity lifi-topology --amount 10000000000
uv run tycho-liquidity dune export
uv run tycho-liquidity build-reports
```

`lifi-topology` does not require the Tycho quote API; it uses LI.FI plus
Tenderly simulation. Pair/protocol validation and future benchmark commands
that compare our Rust router against competitors should use
`TYCHO_DIRECT_URL`.

`scripts/compare-no-key-quotes.sh` does require the Rust quote API. Useful
environment variables:

```bash
TYCHO_DIRECT_URL=http://127.0.0.1:8099/quote/direct
SELL_TOKEN=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
BUY_TOKEN=0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
AMOUNT_IN=1000000000
FROM_ADDRESS=0x0000000000000000000000000000000000000001
PROBE_LOCKED_PROVIDERS=0
```

## Boundary

- Tycho repo: Rust pricing API, simulator, protocol integrations, execution
  code.
- Dune analysis repo: Python analysis, Dune SQL, notebooks, competitor API
  comparisons, Tenderly/debug route topology analysis, benchmark reports.
