{{ config(materialized='table') }}

select
    run_id,
    strategy_name,
    strategy_type,
    round_bucket,
    avg(cooperation_flag) as cooperation_rate,
    avg(defection_flag) as defection_rate,
    avg(payoff) as avg_score
from {{ ref('silver_player_rounds') }}
group by run_id, strategy_name, strategy_type, round_bucket
