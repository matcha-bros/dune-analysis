-- Top pools by token pair and protocol for the first-pass target universe.
with trades as (
    select
        project as protocol,
        coalesce(pool_address, project_contract_address) as pool_id,
        token_bought_symbol,
        token_sold_symbol,
        amount_usd,
        block_time
    from dex.trades
    where blockchain = 'ethereum'
      and block_time >= now() - interval '30' day
)
select
    protocol,
    cast(pool_id as varchar) as pool_id,
    least(token_bought_symbol, token_sold_symbol) as token0_symbol,
    greatest(token_bought_symbol, token_sold_symbol) as token1_symbol,
    sum(case when block_time >= now() - interval '7' day then amount_usd else 0 end) as volume_7d_usd,
    sum(amount_usd) as volume_30d_usd
from trades
where protocol in (
    'uniswap_v4',
    'ekubo_v2',
    'uniswap_v3',
    'curve',
    'balancer_v2',
    'uniswap_v2',
    'sushiswap_v2',
    'pancakeswap_v2',
    'pancakeswap_v3'
)
and (
    token_bought_symbol in ('WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'wstETH', 'cbBTC', 'USDe', 'sUSDe', 'weETH', 'ezETH', 'rsETH', 'BAL', 'UNI', 'LINK', 'AAVE')
    or token_sold_symbol in ('WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'wstETH', 'cbBTC', 'USDe', 'sUSDe', 'weETH', 'ezETH', 'rsETH', 'BAL', 'UNI', 'LINK', 'AAVE')
)
group by 1, 2, 3, 4
order by volume_30d_usd desc
limit 1000;

