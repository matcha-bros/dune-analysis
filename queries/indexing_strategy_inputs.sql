-- Dune-side indexing strategy inputs. Observed Tycho speeds are added locally.
with start_blocks(protocol, tycho_start_block, coverage_class) as (
    values
        ('uniswap_v4', 21688329, 'newer_protocol'),
        ('ekubo_v2', 22048334, 'newer_protocol'),
        ('uniswap_v3', 12369621, 'legacy_major'),
        ('curve', 9906598, 'legacy_major'),
        ('balancer_v2', 12272146, 'legacy_major'),
        ('uniswap_v2', 10008300, 'legacy_secondary'),
        ('sushiswap_v2', 10794229, 'legacy_secondary'),
        ('pancakeswap_v2', 15614590, 'legacy_secondary'),
        ('pancakeswap_v3', 16950686, 'legacy_secondary'),
        ('balancer_v3_uncovered', null, 'adjacent_uncovered')
),
volumes as (
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
        sum(if(block_date >= current_date - interval '7' day, amount_usd, 0)) as volume_7d_usd,
        sum(amount_usd) as volume_30d_usd
    from dex.trades
    where blockchain = 'ethereum'
      and block_date >= current_date - interval '30' day
      and amount_usd is not null
      and (
        (project = 'uniswap' and version in ('2', '3', '4'))
        or project = 'ekubo'
        or project = 'curve'
        or (project = 'balancer' and version in ('2', '3'))
        or (project = 'sushiswap' and version = '2')
        or (project = 'pancakeswap' and version in ('2', '3'))
      )
    group by 1
)
select
    s.protocol,
    s.coverage_class,
    s.tycho_start_block,
    coalesce(v.volume_7d_usd, 0) as volume_7d_usd,
    coalesce(v.volume_30d_usd, 0) as volume_30d_usd
from start_blocks s
left join volumes v on v.protocol = s.protocol
order by volume_30d_usd desc;
