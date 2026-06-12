{{ config(materialized='table') }}

select
    run_id,
    strategy_name as strategy_a,
    opponent_strategy_name as strategy_b,
    avg(total_score) as avg_score_a,
    avg(opponent_total_score) as avg_score_b,
    avg(cooperation_rate) as cooperation_rate_a,
    avg(opponent_cooperation_rate) as cooperation_rate_b,
    count(*) as n_matches
from {{ ref('silver_player_match_stats') }}
group by run_id, strategy_name, opponent_strategy_name
