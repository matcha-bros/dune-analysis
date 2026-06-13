# Competitor Quote API Research

Goal: compare our Tycho-backed direct quote/search API against major hosted routing APIs:
LI.FI, Uniswap, and 1inch.

Do not extract, reuse, or depend on client-side credentials from third-party apps. Use official
developer keys, partner keys, or no-key public limits where the provider explicitly supports them.

## API Access

| Provider | Key path | Auth | Quote endpoint to start with | Notes |
| --- | --- | --- | --- | --- |
| LI.FI | Partner portal: https://portal.li.fi/ | Optional `x-lifi-api-key` header | `GET https://li.quest/v1/quote` | Official docs say all endpoints work without an API key, but keys get higher limits and partner features. Good first adapter because we can smoke-test without waiting for approval. |
| Uniswap | Uniswap Developer Portal / API docs | `x-api-key: $UNISWAP_API_KEY` | `POST https://trade-api.gateway.uniswap.org/v1/quote` | Trading API quote responses are the right comparison target. The local Uniswap AI reference also documents this endpoint and header. |
| 1inch | 1inch Developer Portal: https://portal.1inch.dev/ | `Authorization: Bearer $ONEINCH_API_KEY` | Classic Swap quote under `https://api.1inch.dev` / `https://api.1inch.com` depending SDK/doc path | API key is required for production usage. Use the official SDK/openapi examples to avoid stale route names. |

Suggested `.env` names:

```bash
LIFI_API_KEY=              # optional for basic quote smoke tests
UNISWAP_API_KEY=
ONEINCH_API_KEY=

LIFI_API_URL=https://li.quest/v1
UNISWAP_API_URL=https://trade-api.gateway.uniswap.org/v1
ONEINCH_API_URL=https://api.1inch.dev
```

## Cached References

Fetched with `opensrc path`:

| Provider | Local reference |
| --- | --- |
| LI.FI | `/home/leovigna/.opensrc/repos/github.com/lifinance/lifi-agent-skills/main` |
| Uniswap | `/home/leovigna/.opensrc/repos/github.com/uniswap/uniswap-ai/main` |
| Uniswap routing source | `/home/leovigna/.opensrc/repos/github.com/Uniswap/routing-api/main` |
| 1inch Go SDK | `/home/leovigna/.opensrc/repos/github.com/1inch/1inch-sdk-go/main` |

Useful files:

| Provider | Files |
| --- | --- |
| LI.FI | `skills/lifi/SKILL.md`, `skills/lifi/references/REFERENCE.md` |
| Uniswap | `docs/skills/swap-integration.md`, plus routing source `README.md` and `scripts/get_quote.ts` |
| 1inch | `README.md`, `sdk-clients/aggregation/examples/quote/main.go`, `internal/http-executor/http.go` |

## Normalized Quote Model

For benchmark comparisons, normalize every provider response into:

```json
{
  "provider": "tycho|lifi|uniswap|oneinch",
  "chainId": 1,
  "tokenIn": "0x...",
  "tokenOut": "0x...",
  "amountIn": "1000000",
  "amountOut": "raw integer output",
  "amountOutMin": "raw integer minimum if available",
  "gasEstimate": "raw gas units if available",
  "gasAdjustedAmountOut": "raw integer if provider returns it",
  "routeSummary": "human-readable protocol/route metadata",
  "raw": {}
}
```

Compare raw `amountOut` first. Separately track gas-adjusted output where the hosted API returns it.
Our current Tycho prototype only searches direct, full-amount routes and ignores gas, while hosted
aggregators may use multihop and split routes.

## Initial Pair Set

Use the pair set we already validated as meaningful for Tycho-hosted coverage:

| Pair |
| --- |
| USDC/WETH |
| USDT/WETH |
| WBTC/WETH |
| USDT/WBTC |
| USDC/WBTC |
| LINK/WETH |
| DAI/WETH |
| AAVE/USDC |
| AAVE/WETH |
| UNI/WETH |

## Implementation Notes

Start with exact-in quotes on Ethereum mainnet. Use one deterministic taker/swapper address for all
providers, even for quote-only requests, because some APIs require it to account for permit,
approval, and gas assumptions.

Do not claim we beat a hosted aggregator until we compare like-for-like search scope. A direct-only
Tycho quote can beat a provider on a particular amount/pair, but the fair next comparison is:

1. Tycho direct-only vs hosted raw output.
2. Tycho direct + multihop vs hosted raw output.
3. Tycho direct + multihop + split routing + gas model vs hosted gas-adjusted output.

## No-Key Smoke Test

Use this path when we only want competitor quotes that work without adding provider keys.

Start the local Tycho direct quote API:

```bash
set -a; . ./.env; set +a

DIRECT_SWAP_API_BIND=127.0.0.1:8099 \
TYCHO_URL=tycho-fynd-ethereum.propellerheads.xyz \
TOKEN_MIN_QUALITY=100 \
MAX_DAYS_SINCE_LAST_TRADE=3 \
TVL_GT=10 \
SCAN_PROTOCOLS=uniswap_v2,uniswap_v3,sushiswap_v2,pancakeswap_v2,pancakeswap_v3,uniswap_v4,ekubo_v2 \
cargo run -q -p tycho-simulation --example direct_swap_search_api
```

From `../dune-analysis`, run the comparison:

```bash
scripts/compare-no-key-quotes.sh
```

Optionally prove that 1inch and Uniswap are locked without keys:

```bash
PROBE_LOCKED_PROVIDERS=1 scripts/compare-no-key-quotes.sh
```

Observed on 2026-06-13 for `1 USDC -> WETH`:

```text
tycho-direct   status=200   amountOut=597772095503508   formatted=0.000597772096   protocol=uniswap_v3   pool=0xe0554a476a092703abdb3ef35c80e0d76d32939f   candidates=11
lifi-no-key    status=200   amountOut=595435679471858   amountOutMin=592458501074499   tool=nordstern   gas=573878
1inch-no-key   status=401   Missing or invalid authorization
uniswap-no-key status=401   Unauthenticated api key or session
```

Conclusion: LI.FI is usable immediately without a competitor key. 1inch and Uniswap need legitimate
provider keys before they can be part of the benchmark harness.

## LI.FI Negative Ex-Fee Edge Route Inspection

Question: when Tycho direct loses after backing out LI.FI's public included fee, is LI.FI winning
because it uses protocols we do not simulate, or because it uses multihop/split routing?

Method:

1. Pulled raw LI.FI quote JSON for `USDC -> WETH` sizes where Tycho had negative estimated ex-fee
   edge.
2. Saved the raw responses under `logs/lifi-routes/usdc-weth-<amount>.json`.
3. Inspected `includedSteps`, `estimate.feeCosts`, `transactionRequest.to`, calldata selector, and
   known address occurrences inside calldata.

The LI.FI transaction selector was:

```text
0x5fd9ae2e = swapTokensMultipleV3ERC20ToERC20(bytes32,string,string,address,uint256,(address,address,address,address,uint256,bytes,bool)[])
```

So the executable route is a LI.FI multi-swap wrapper call to the LI.FI contract
`0x1231DEB6f5749EF6cE6943a275A1D3E7486F4EaE`, with one top-level fee collection step and one
external swap step.

Fresh aligned run on 2026-06-13:

| Input | Tycho Direct | LI.FI Net | LI.FI Est. Ex-Fee | Tycho Edge Ex-Fee | Tycho Best | LI.FI Tool | LI.FI Steps | Route Hints In Calldata |
| ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| 100 USDC | 0.059751264293 WETH | 0.059796742484 WETH | 0.060006766166 WETH | -0.4258% | `uniswap_v3` `0xe055...2939f` | `sushiswap` | `feeCollection,sushiswap` | `USDT`, Sushi RouteProcessor |
| 1,000 USDC | 0.597477740128 WETH | 0.596133684513 WETH | 0.597627753897 WETH | -0.0251% | `uniswap_v3` `0x88e6...5640` | `nordstern` | `feeCollection,nordstern` | `USDT`, Nordstern router |
| 10,000 USDC | 5.974314609836 WETH | 5.960937146083 WETH | 5.975876838178 WETH | -0.0261% | `uniswap_v3` `0x88e6...5640` | `kyberswap` | `feeCollection,kyberswap` | `USDT`, Kyber router, Uniswap V3 `0xe055...2939f` |
| 100,000 USDC | 59.696901693852 WETH | 59.588452384770 WETH | 59.737796876962 WETH | -0.0685% | `uniswap_v3` `0x88e6...5640` | `kyberswap` | `feeCollection,kyberswap` | Kyber router, Uniswap V3 `0x88e6...5640` |

Interpretation:

- These are not simple LI.FI direct-pool quotes. They route through external aggregator tools:
  Sushi Aggregator, Nordstern, and KyberSwap.
- At least three of the four inspected calldata payloads contain `USDT`, so LI.FI is likely using
  a multihop path such as `USDC -> USDT -> WETH` or an aggregator path containing a USDT leg.
- The Kyber payloads also include Uniswap V3 pool addresses that Tycho can simulate, so some of
  LI.FI's advantage is not necessarily unavailable liquidity. It may be using the same major pools
  through Kyber's route construction, possibly with multihop or split execution.
- The LI.FI quote response does not expose pool-level splits for Kyber/Nordstern/Sushi in a clean
  normalized field. To prove exact pool weights, we need provider-specific calldata decoding or
  direct access to those aggregator quote APIs.

Actionable takeaway:

- The next Tycho router iteration should prioritize multihop before exotic protocol coverage.
  `USDC/USDT/WETH` paths are visible in LI.FI calldata and are easy to model with our current
  Tycho-supported AMMs.
- Split routing is probably the second priority. The large Kyber calldata payloads and high gas
  estimates suggest more complex routes than a single direct pool, but the LI.FI response alone does
  not prove the split weights.
- Protocol coverage still matters, but these examples do not prove that missing non-Tycho protocols
  are the main cause. They prove our current direct-only search is too narrow.

### Broader Competitor Topology Analysis

Detailed LI.FI/Tenderly topology simulation and Dune distribution analysis live
beside this document:

```text
docs/competitor_route_topology.md
src/tycho_liquidity_analysis/lifi_topology.py
queries/aggregator_route_topology_by_size.sql
```
