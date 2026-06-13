-- Dashboard headline counters.
with protocol_volumes as (
    select * from (
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
                amount_usd,
                block_date
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
        )
        select
            protocol,
            sum(if(block_date >= current_date - interval '7' day, amount_usd, 0)) as volume_7d_usd,
            sum(amount_usd) as volume_30d_usd
        from mapped_trades
        where protocol is not null
        group by 1
    )
)
select
    sum(volume_7d_usd) as total_volume_7d_usd,
    sum(volume_30d_usd) as total_volume_30d_usd,
    sum(if(protocol in ('uniswap_v4', 'ekubo_v2'), volume_7d_usd, 0)) / sum(volume_7d_usd) as v4_ekubo_share_7d,
    sum(if(protocol in ('uniswap_v4', 'ekubo_v2'), volume_30d_usd, 0)) / sum(volume_30d_usd) as v4_ekubo_share_30d,
    current_timestamp as generated_at
from protocol_volumes;
