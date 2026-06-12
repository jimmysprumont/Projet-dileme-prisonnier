{{ config(materialized='table') }}

select
    run_id,
    strategy_name,
    strategy_type,
    total_score,
    avg_score_per_round,
    cooperation_rate,
    forgiveness_rate,
    rank
from {{ ref('tournament_summary') }}
left join {{ ref('forgiveness_index') }} using (run_id, strategy_name, strategy_type)
