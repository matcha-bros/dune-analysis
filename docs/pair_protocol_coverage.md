# Hosted Tycho Pair Coverage Research

## Goal

Find token pairs where a significant share of market volume is from protocols we
can simulate accurately with Tycho.

For the MVP, the realistic liquidity universe is:

- Existing mainnet protocols available from the hosted Tycho API.
- Our own protocol from our own custom Tycho instance.

We should not assume we can self-index all existing mainnet protocols in time
for the MVP. The router should merge two clients:

```text
hosted Tycho mainnet client -> existing supported protocols
custom Tycho/local client   -> our protocol
route search layer          -> compares and combines both liquidity universes
```

## Data Source

The pair and protocol volume conclusions come from this Dune analysis project in
`reports` and `data/processed`.

Relevant files:

- `reports/all_venue_coverage.md`
- `reports/protocol_coverage.md`
- `reports/indexing_strategy.md`
- `data/processed/token_pair_coverage.parquet`
- `data/processed/non_tycho_venue_breakdown.parquet`

## Current Hosted Tycho Coverage

The current hosted Tycho Fynd plan allows these protocol systems:

- `uniswap_v2`
- `sushiswap_v2`
- `pancakeswap_v2`
- `uniswap_v3`
- `pancakeswap_v3`
- `uniswap_v4`
- `ekubo_v2`
- `ekubo_v3`
- `fluid_v1`

The current plan does not allow:

- `vm:curve`
- `vm:balancer_v2`

This means our MVP should avoid headline benchmark pairs where Curve, Balancer,
or Fluid dominate unless we have confirmed that the hosted API and our scanner
can simulate those venues for that pair.

## Key Finding

The best MVP benchmark pairs are high-volume non-pegged pairs where the current
hosted Tycho core protocols already cover most observed volume.

These pairs let us price with high accuracy using protocols available through
hosted Tycho, then add our custom protocol as an additional liquidity source.

## Recommended MVP Benchmark Pairs

These pairs have large 30d volume and high coverage from the current hosted
Tycho core set, excluding Curve/Balancer and excluding Fluid-dominant pegged
routes:

| Pair | Approx 30d volume | Approx hosted-core coverage | Notes |
| --- | ---: | ---: | --- |
| `USDC-WETH` | `$5.18B` | `98.19%` | Best primary benchmark pair. Deep Uniswap V3/V4 coverage. |
| `USDT-WETH` | `$2.27B` | `97.51%` | Strong secondary ETH-stable route. |
| `WBTC-WETH` | `$878M` | `98.35%` | Strong volatile blue-chip pair. |
| `USDT-WBTC` | `$743M` | `95.38%` | Useful BTC-stable route. |
| `USDC-WBTC` | `$261M` | `93.23%` | Useful BTC-stable route. |
| `LINK-WETH` | `$105M` | `100.00%` | Good volatile alt benchmark. |
| `DAI-WETH` | `$80M` | `99.20%` | Useful stable-to-ETH route without heavy Curve dependence in this dataset. |
| `AAVE-USDC` | `$37M` | `100.00%` | Good protocol-token route. |
| `AAVE-WETH` | `$25M` | `100.00%` | Good protocol-token route. |
| `UNI-WETH` | `$13M` | `100.00%` | Good protocol-token route. |

Fee note: fees are pool-level, not pair-level. The Dune reports do not include
fee tiers, but hosted Tycho component metadata exposes Uniswap V3 fee tiers for
the dominant pools. Common dominant fees observed:

| Pair | Dominant observed fee tiers |
| --- | --- |
| `USDC-WETH` | Uniswap V3 `0.05%`, `0.01%`, `0.30%`; Pancake V3 also present. |
| `USDT-WETH` | Uniswap V3 `0.30%`, `0.01%`, `0.05%`. |
| `WBTC-WETH` | Uniswap V3 `0.05%`, `0.01%`, `0.30%`; Sushi V2 `~0.30%` also present. |
| `USDT-WBTC` | Uniswap V3 `0.05%`, `0.30%`; V4 also present. |
| `USDC-WBTC` | Uniswap V3 `0.30%`, `0.05%`; V4 also present. |
| `LINK-WETH` | Uniswap V3 `0.30%`, `0.05%`; Uniswap V2 `~0.30%` also present. |
| `DAI-WETH` | Sushi V2 `~0.30%`, Uniswap V3 `0.05%` and `0.30%`, Uniswap V2 `~0.30%`. |
| `AAVE-USDC` | V4 dominant in Dune; smaller Uniswap V3 `0.30%`. |
| `AAVE-WETH` | Uniswap V3 `0.30%`, `0.05%`. |
| `UNI-WETH` | Uniswap V3 `0.30%`; Uniswap V2 `~0.30%`. |

## Top Covered Protocols By Pair

The table below shows the top three protocols from the hosted-Tycho-coverable
set for each recommended benchmark pair. Percentages are share of total pair
volume in the Dune target-protocol dataset, not share of only the covered
subset.

| Pair | Top covered protocols by 30d volume |
| --- | --- |
| `USDC-WETH` | `uniswap_v3` `$4.79B` (`92.46%`), `uniswap_v4` `$175.6M` (`3.39%`), `pancakeswap_v3` `$53.6M` (`1.03%`) |
| `USDT-WETH` | `uniswap_v3` `$2.02B` (`88.87%`), `uniswap_v4` `$88.2M` (`3.88%`), `pancakeswap_v3` `$71.9M` (`3.16%`) |
| `WBTC-WETH` | `uniswap_v3` `$846.5M` (`96.45%`), `sushiswap_v2` `$7.5M` (`0.86%`), `ekubo_v2` `$6.4M` (`0.73%`) |
| `USDT-WBTC` | `uniswap_v3` `$670.0M` (`90.16%`), `uniswap_v4` `$31.8M` (`4.28%`), `ekubo_v2` `$6.9M` (`0.93%`) |
| `USDC-WBTC` | `uniswap_v4` `$136.3M` (`52.22%`), `uniswap_v3` `$107.0M` (`40.98%`), `uniswap_v2` `$0.1M` (`0.02%`) |
| `LINK-WETH` | `uniswap_v3` `$104.9M` (`99.49%`), `uniswap_v2` `$0.3M` (`0.29%`), `sushiswap_v2` `$0.2M` (`0.22%`) |
| `DAI-WETH` | `sushiswap_v2` `$40.1M` (`49.87%`), `uniswap_v3` `$30.5M` (`37.99%`), `uniswap_v2` `$9.1M` (`11.33%`) |
| `AAVE-USDC` | `uniswap_v4` `$35.9M` (`97.88%`), `uniswap_v3` `$0.8M` (`2.12%`), `pancakeswap_v2` `<$0.1M` (`0.00%`) |
| `AAVE-WETH` | `uniswap_v3` `$25.3M` (`99.90%`), `uniswap_v2` `<$0.1M` (`0.10%`), `sushiswap_v2` `<$0.1M` (`0.00%`) |
| `UNI-WETH` | `uniswap_v3` `$10.9M` (`85.64%`), `uniswap_v2` `$1.6M` (`12.58%`), `sushiswap_v2` `$0.2M` (`1.77%`) |

The corresponding notebook visualization is in
`notebooks/04_hosted_tycho_pair_coverage.ipynb`.

Recommended initial benchmark set:

```text
USDC-WETH
USDT-WETH
WBTC-WETH
USDT-WBTC
USDC-WBTC
LINK-WETH
DAI-WETH
AAVE-WETH
UNI-WETH
```

## Pairs To Avoid As Headline MVP Benchmarks

Avoid these for the first public/decision-making benchmark unless we have
Curve/Balancer/full Fluid coverage wired and tested:

```text
USDC-USDT
USDe-USDT
USDS-USDT
sUSDe-USDT
WETH-wstETH
weETH-WETH
cbBTC-WBTC
DAI-USDC
GHO-USDC
```

Reason: these are stable, synthetic-dollar, LST, or wrapped-BTC near-pegged
routes. The Dune analysis shows Fluid, Curve, and Balancer matter much more in
this category. Missing those venues would make our router look worse for reasons
unrelated to route-search quality.

## Fluid V1 Note

Fluid V1 is not 1inch SwapVM. In the sibling Tycho repo it is a native Tycho
integration:

- Simulation: `../tycho-mainnet-simulation/crates/tycho-simulation/src/evm/protocol/fluid/v1.rs`
- Decoder/VM state: `../tycho-mainnet-simulation/crates/tycho-simulation/src/evm/protocol/fluid/`
- Execution encoder: `../tycho-mainnet-simulation/crates/tycho-execution/src/encoding/evm/swap_encoder/fluid_v1.rs`
- Executor contract: `../tycho-mainnet-simulation/crates/tycho-execution/contracts/src/executors/FluidV1Executor.sol`
- Substream: `../tycho-mainnet-simulation/protocols/substreams/ethereum-fluid/`

Fluid is not technically limited to pegged assets, but the Dune data shows its
volume is heavily concentrated there:

- Total Fluid 30d volume in the analyzed universe: about `$4.94B`.
- Near/pegged pairs: about `$4.51B`, or `91.3%`.
- Non-near pairs: about `$429M`, or `8.7%`.

So Fluid matters a lot for stable, LST, wrapped BTC, and synthetic-dollar
routes. It matters much less for the recommended volatile MVP benchmark set.

## Practical Benchmark Rule

For MVP claims, report results only on pairs where:

1. Hosted Tycho provides most of the relevant existing mainnet liquidity.
2. Our custom protocol is included through our own Tycho/local client.
3. Missing Curve/Balancer/Fluid does not dominate the pair's observed volume.
4. The pair has enough 30d volume to be economically meaningful.

This keeps the benchmark honest: we are testing whether our route-search
algorithm and custom protocol improve execution over a liquidity universe we can
actually simulate accurately.
