{{ config(materialized='table') }}

select
    run_id,
    strategy_name,
    strategy_type,
    sum(total_score) as total_score,
    sum(total_score)::double / nullif(sum(n_rounds), 0) as avg_score_per_round,
    avg(cooperation_rate) as cooperation_rate,
    avg(defection_rate) as defection_rate,
    sum(case when match_result = 'win' then 1 else 0 end) as wins,
    sum(case when match_result = 'loss' then 1 else 0 end) as losses,
    sum(case when match_result = 'draw' then 1 else 0 end) as draws,
    rank() over (
        partition by run_id
        order by sum(total_score) desc, avg(cooperation_rate) desc
    ) as rank
from {{ ref('silver_player_match_stats') }}
group by run_id, strategy_name, strategy_type
