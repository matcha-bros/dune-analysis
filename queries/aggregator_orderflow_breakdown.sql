-- Aggregator/orderflow layer. This is separate from underlying DEX venue liquidity.
select
    project,
    version,
    count(*) as trades,
    sum(amount_usd) as volume_30d_usd,
    sum(amount_usd) / sum(sum(amount_usd)) over () as share_30d
from dex_aggregator.trades
where blockchain = 'ethereum'
  and block_date >= current_date - interval '30' day
  and amount_usd is not null
  and (
    token_bought_symbol in ('WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'wstETH', 'cbBTC', 'USDe', 'sUSDe', 'weETH', 'ezETH', 'rsETH', 'BAL', 'UNI', 'LINK', 'AAVE')
    or token_sold_symbol in ('WETH', 'USDC', 'USDT', 'DAI', 'WBTC', 'wstETH', 'cbBTC', 'USDe', 'sUSDe', 'weETH', 'ezETH', 'rsETH', 'BAL', 'UNI', 'LINK', 'AAVE')
  )
group by 1, 2
order by volume_30d_usd desc
limit 50;
