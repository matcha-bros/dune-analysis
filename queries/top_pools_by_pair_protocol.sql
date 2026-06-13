-- Top contracts/pools by pair and protocol for the first-pass target token universe.
with mapped_trades as (
    select
        case
            when project = 'uniswap' and version = '4' then 'uniswap_v4'
            when project = 'ekubo' then 'ekubo_v2'
            when project = 'uniswap' and version = '3' then 'uniswap_v3'
            when project = 'curve' then 'curve'
            when project = 'balancer' and version = '2' then 'balancer_v2'
            when project = 'balancer' and version = '3' then 'balancer_v3_uncovered'
            when project = 'uniswap' and version = '2' then 'uniswap_v2'
            when project = 'sushiswap' and version = '2' then 'sushiswap_v2'
            when project = 'pancakeswap' and version = '2' then 'pancakeswap_v2'
            when project = 'pancakeswap' and version = '3' then 'pancakeswap_v3'
        end as protocol,
        cast(project_contract_address as varchar) as pool_id,
        token_pair,
        token_bought_symbol,
        token_sold_symbol,
        amount_usd,
        block_date
    from dex.trades
    where blockchain = 'ethereum'
      and block_date >= current_date - interval '30' day
      and amount_usd is not null
      and project_contract_address is not null
      and (
        (project = 'uniswap' and version in ('2', '3', '4'))
        or project = 'ekubo'
        or project = 'curve'
        or (project = 'balancer' and version in ('2', '3'))
        or (project = 'sushiswap' and version = '2')
        or (project = 'pancakeswap' and version in ('2', '3'))
      )
)
select
    protocol,
    pool_id,
    token_pair,
    sum(if(block_date >= current_date - interval '7' day, amount_usd, 0)) as volume_7d_usd,
    sum(amount_usd) as volume_30d_usd
from mapped_trades
where protocol is not null
  and (
    token_bought_symbol in ('WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'wstETH', 'cbBTC', 'USDe', 'sUSDe', 'weETH', 'ezETH', 'rsETH', 'BAL', 'UNI', 'LINK', 'AAVE')
    or token_sold_symbol in ('WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'wstETH', 'cbBTC', 'USDe', 'sUSDe', 'weETH', 'ezETH', 'rsETH', 'BAL', 'UNI', 'LINK', 'AAVE')
  )
group by 1, 2, 3
order by volume_30d_usd desc
limit 1000;
