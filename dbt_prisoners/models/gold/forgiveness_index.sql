{{ config(materialized='table') }}

select
    run_id,
    strategy_name,
    strategy_type,
    sum(betrayal_events) as betrayal_events,
    sum(forgiveness_events) as forgiveness_events,
    case
        when sum(betrayal_events) = 0 then 0.0
        else sum(forgiveness_events)::double / sum(betrayal_events)
    end as forgiveness_rate
from {{ ref('silver_player_match_stats') }}
group by run_id, strategy_name, strategy_type
