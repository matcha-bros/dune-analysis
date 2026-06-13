-- Raw Dune project/version breakdown for mapping validation.
select
    project,
    version,
    count(*) as trades_7d,
    sum(amount_usd) as volume_7d_usd
from dex.trades
where blockchain = 'ethereum'
  and block_date >= current_date - interval '7' day
  and amount_usd is not null
  and (
    (project = 'uniswap' and version in ('2', '3', '4'))
    or project = 'ekubo'
    or project = 'curve'
    or (project = 'balancer' and version in ('2', '3'))
    or (project = 'sushiswap' and version = '2')
    or (project = 'pancakeswap' and version in ('2', '3'))
  )
group by 1, 2
order by volume_7d_usd desc;
