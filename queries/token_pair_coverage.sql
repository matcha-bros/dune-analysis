-- Token-pair coverage for first-pass target universe.
with trades as (
    select
        project as protocol,
        least(token_bought_symbol, token_sold_symbol) as token0_symbol,
        greatest(token_bought_symbol, token_sold_symbol) as token1_symbol,
        amount_usd,
        block_time
    from dex.trades
    where blockchain = 'ethereum'
      and block_time >= now() - interval '30' day
)
select
    token0_symbol,
    token1_symbol,
    protocol,
    sum(case when block_time >= now() - interval '7' day then amount_usd else 0 end) as volume_7d_usd,
    sum(amount_usd) as volume_30d_usd
from trades
where token0_symbol in ('WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'wstETH', 'cbBTC', 'USDe', 'sUSDe', 'weETH', 'ezETH', 'rsETH', 'BAL', 'UNI', 'LINK', 'AAVE')
  and token1_symbol in ('WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'wstETH', 'cbBTC', 'USDe', 'sUSDe', 'weETH', 'ezETH', 'rsETH', 'BAL', 'UNI', 'LINK', 'AAVE')
group by 1, 2, 3
order by volume_30d_usd desc;

