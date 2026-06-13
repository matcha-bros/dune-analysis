-- Estimate competitor route topology by joining aggregator-level trades to
-- underlying venue trades in the same Ethereum transaction.
--
-- Purpose:
--   Find pairs and size buckets where aggregator orderflow is mostly executed
--   through Tycho-simulatable AMMs versus RFQ/solver/native liquidity.
--
-- Notes:
--   - This is not a calldata decoder.
--   - This is not a per-quote simulator.
--   - It is a transaction-level historical classifier using Dune decoded trade
--     tables. Use Tenderly/debug simulation for individual quote validation.

with params as (
    select
        date_trunc('day', current_date - interval '30' day) as start_date
),
target_aggregator_trades as (
    select
        block_time,
        block_date,
        tx_hash,
        project as aggregator_project,
        version as aggregator_version,
        token_pair,
        token_sold_symbol,
        token_bought_symbol,
        amount_usd,
        case
            when amount_usd < 1000 then '000001k_lt_1k'
            when amount_usd < 10000 then '001k_010k'
            when amount_usd < 100000 then '010k_100k'
            when amount_usd < 1000000 then '100k_1m'
            else '1m_plus'
        end as size_bucket
    from dex_aggregator.trades
    where blockchain = 'ethereum'
      and block_date >= (select start_date from params)
      and amount_usd is not null
      and project in ('lifi', 'kyberswap', '1inch', 'odos', 'paraswap', '0x')
      and (
          token_pair in ('USDC-WETH', 'WETH-USDC', 'USDT-WETH', 'WETH-USDT', 'WBTC-WETH', 'WETH-WBTC')
          or (
              token_sold_symbol in ('USDC', 'USDT', 'WETH', 'WBTC')
              and token_bought_symbol in ('USDC', 'USDT', 'WETH', 'WBTC')
          )
      )
),
underlying_venue_trades as (
    select
        tx_hash,
        project as venue_project,
        version as venue_version,
        token_pair as venue_token_pair,
        amount_usd as venue_amount_usd,
        case
            when (project = 'uniswap' and version in ('2', '3', '4'))
              or (project = 'sushiswap' and version = '2')
              or (project = 'pancakeswap' and version in ('2', '3'))
              or project = 'ekubo'
              or project = 'curve'
              or (project = 'balancer' and version = '2')
                then 'tycho_simulatable_amm'
            when project in ('native', '1inch-LOP', '0x-API')
                then 'rfq_solver_orderflow'
            else 'other_or_unclassified_venue'
        end as venue_category
    from dex.trades
    where blockchain = 'ethereum'
      and block_date >= (select start_date from params)
      and amount_usd is not null
),
joined as (
    select
        a.aggregator_project,
        a.aggregator_version,
        a.token_pair as aggregator_pair,
        a.token_sold_symbol,
        a.token_bought_symbol,
        a.size_bucket,
        a.tx_hash,
        a.amount_usd as aggregator_amount_usd,
        u.venue_category,
        u.venue_project,
        u.venue_version,
        u.venue_token_pair,
        u.venue_amount_usd
    from target_aggregator_trades a
    left join underlying_venue_trades u
        on a.tx_hash = u.tx_hash
),
tx_classification as (
    select
        aggregator_project,
        aggregator_version,
        aggregator_pair,
        token_sold_symbol,
        token_bought_symbol,
        size_bucket,
        tx_hash,
        max(aggregator_amount_usd) as aggregator_amount_usd,
        sum(case when venue_category = 'tycho_simulatable_amm' then venue_amount_usd else 0 end)
            as tycho_amm_venue_usd,
        sum(case when venue_category = 'rfq_solver_orderflow' then venue_amount_usd else 0 end)
            as rfq_solver_venue_usd,
        sum(case when venue_category = 'other_or_unclassified_venue' then venue_amount_usd else 0 end)
            as other_venue_usd,
        count_if(venue_category = 'tycho_simulatable_amm') as tycho_amm_trade_rows,
        count_if(venue_category = 'rfq_solver_orderflow') as rfq_solver_trade_rows,
        count_if(venue_category = 'other_or_unclassified_venue') as other_trade_rows,
        array_join(array_sort(array_distinct(array_agg(
            coalesce(venue_project || ':' || coalesce(venue_version, ''), 'no_underlying_dex_row')
        ))), ', ') as observed_venues,
        case
            when count_if(venue_category = 'rfq_solver_orderflow') > 0 then 'rfq_solver_involved'
            when count_if(venue_category = 'tycho_simulatable_amm') > 1 then 'multi_amm_or_split'
            when count_if(venue_category = 'tycho_simulatable_amm') = 1 then 'single_tycho_amm'
            when count(*) = 1 and max(venue_project) is null then 'no_underlying_dex_row'
            else 'other_or_unclassified'
        end as topology_class
    from joined
    group by 1, 2, 3, 4, 5, 6, 7
)
select
    aggregator_project,
    aggregator_version,
    aggregator_pair,
    token_sold_symbol,
    token_bought_symbol,
    size_bucket,
    topology_class,
    count(*) as tx_count,
    sum(aggregator_amount_usd) as aggregator_volume_usd,
    sum(aggregator_amount_usd) / sum(sum(aggregator_amount_usd)) over (
        partition by aggregator_project, aggregator_pair, size_bucket
    ) as share_in_project_pair_bucket,
    sum(tycho_amm_venue_usd) as tycho_amm_venue_usd,
    sum(rfq_solver_venue_usd) as rfq_solver_venue_usd,
    sum(other_venue_usd) as other_venue_usd,
    max(observed_venues) as example_observed_venues
from tx_classification
group by 1, 2, 3, 4, 5, 6, 7
order by aggregator_volume_usd desc
limit 500;
