# Competitor Route Topology

## Goal

Measure where competitor aggregator volume is actually executed:

- Tycho-simulatable AMMs, such as Uniswap V2/V3/V4, Pancake V2/V3, Sushi V2,
  Ekubo, Curve, and Balancer V2.
- RFQ / solver / native orderflow venues that Tycho AMM graph search will not
  reproduce directly.
- Other or unclassified venues.

This directly supports the main routing goal: find pairs and size buckets where
a significant share of competitor volume is from protocols we can simulate with
Tycho, and separate those from cases where competitors win through external
RFQ/solver liquidity.

## Simulation Versus Dune

Tenderly/debug simulation answers exact per-quote topology:

```text
Given this fresh LI.FI quote, what token transfers and venue calls actually
happen if this exact transaction is executed?
```

Dune answers historical distribution:

```text
Across the last 30 days, for this aggregator, pair, and size bucket, how much
executed volume landed on Tycho-simulatable AMMs versus RFQ/native/other venues?
```

Both are needed. Simulation validates individual competitive quotes. Dune tells
us whether those quote patterns are common enough to shape the router roadmap.

## Query

The query is:

```text
queries/aggregator_route_topology_by_size.sql
```

It joins `dex_aggregator.trades` to `dex.trades` by `tx_hash`, then classifies
the underlying venue rows into:

- `single_tycho_amm`
- `multi_amm_or_split`
- `rfq_solver_involved`
- `other_or_unclassified`
- `no_underlying_dex_row`

It also buckets by notional size:

- `<1k`
- `1k-10k`
- `10k-100k`
- `100k-1m`
- `1m+`

## How To Run

From this `dune-analysis` repo:

```bash
uv run tycho-liquidity dune publish
uv run tycho-liquidity dune export
```

The new query is registered in the Dune publisher as:

```text
aggregator_route_topology_by_size
```

For exact fresh LI.FI quote topology, run:

```bash
uv run tycho-liquidity lifi-topology --amount 10000000000
```

This command fetches a LI.FI quote, simulates `approve + swap` with Tenderly,
and infers the realized topology from ERC20 transfer logs plus call trace
addresses. It loads Tenderly credentials from this repo's `.env` or from the
sibling `../tycho-mainnet-simulation/.env`.

## Interpretation

Use the result to prioritize router work:

- High `single_tycho_amm` or `multi_amm_or_split` share means Tycho graph search
  should be able to compete by adding multihop and split routing.
- High `rfq_solver_involved` share means AMM-only Tycho routing will likely miss
  a real competitor source. That should be benchmarked separately as RFQ/solver
  liquidity, not treated as a Tycho AMM search failure.
- High `no_underlying_dex_row` means Dune did not expose a matching venue row;
  validate representative transactions with Tenderly/debug simulation before
  drawing conclusions.

## Current Simulation Evidence

The LI.FI simulations showed:

- `1,000 USDC -> WETH`: LI.FI/Kyber executed through a Uniswap V3 pool.
- `10,000 USDC -> WETH`: a fresh run executed a split-like path through
  NativeRouter V3 / Native CreditVault plus a smaller Uniswap V3 `USDC/WETH
  0.01%` leg.
- `100,000 USDC -> WETH`: LI.FI/Kyber executed through NativeRouter V3 /
  Native CreditVault.

That suggests the `10k-100k` band can contain both AMM and RFQ/native
liquidity inside the same competitor route. Tycho AMM graph search can compete
on the AMM part, but Native/CreditVault liquidity needs separate treatment.
