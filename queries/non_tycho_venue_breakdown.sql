-- Largest non-Tycho Dune dex.trades venue/project/pair buckets.
with trades as (
    select
        project,
        version,
        token_pair,
        amount_usd
    from dex.trades
    where blockchain = 'ethereum'
      and block_date >= current_date - interval '30' day
      and amount_usd is not null
      and (
        token_bought_symbol in ('WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'wstETH', 'cbBTC', 'USDe', 'sUSDe', 'weETH', 'ezETH', 'rsETH', 'BAL', 'UNI', 'LINK', 'AAVE')
        or token_sold_symbol in ('WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'wstETH', 'cbBTC', 'USDe', 'sUSDe', 'weETH', 'ezETH', 'rsETH', 'BAL', 'UNI', 'LINK', 'AAVE')
      )
),
non_tycho as (
    select
        project,
        version,
        token_pair,
        amount_usd,
        case
            when project in ('1inch-LOP', '0x-API', 'native')
                then 'rfq_intent_orderflow_or_api'
            else 'other_onchain_defi_venue'
        end as category
    from trades
    where not (
        (project = 'uniswap' and version in ('2', '3', '4'))
        or project = 'ekubo'
        or project = 'curve'
        or (project = 'balancer' and version = '2')
        or (project = 'sushiswap' and version = '2')
        or (project = 'pancakeswap' and version in ('2', '3'))
    )
)
select
    category,
    project,
    version,
    token_pair,
    sum(amount_usd) as volume_30d_usd,
    sum(amount_usd) / sum(sum(amount_usd)) over () as share_of_non_tycho
from non_tycho
group by 1, 2, 3, 4
order by volume_30d_usd desc
limit 100;
