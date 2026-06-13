-- Protocol-level 7d/30d DEX volume.
-- TODO: replace source tables with the confirmed Dune Spellbook tables for each target protocol.
with trades as (
    select
        project as protocol,
        amount_usd,
        block_time
    from dex.trades
    where blockchain = 'ethereum'
      and project in (
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
      and block_time >= now() - interval '30' day
)
select
    protocol,
    sum(case when block_time >= now() - interval '7' day then amount_usd else 0 end) as volume_7d_usd,
    sum(amount_usd) as volume_30d_usd
from trades
group by 1
order by volume_30d_usd desc;

