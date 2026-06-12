{{ config(materialized='table') }}

with base as (
    select
        run_id,
        match_id,
        player_id,
        opponent_player_id,
        strategy_name,
        strategy_type,
        count(*) as n_rounds,
        sum(payoff) as total_score,
        avg(payoff) as avg_score_per_round,
        avg(cooperation_flag) as cooperation_rate,
        avg(defection_flag) as defection_rate,
        sum(case when was_betrayed_previous_round then 1 else 0 end) as betrayal_events,
        sum(case when returned_to_cooperation then 1 else 0 end) as forgiveness_events
    from {{ ref('silver_player_rounds') }}
    group by
        run_id,
        match_id,
        player_id,
        opponent_player_id,
        strategy_name,
        strategy_type
)
select
    b.run_id,
    b.match_id,
    b.player_id,
    b.opponent_player_id,
    b.strategy_name,
    b.strategy_type,
    opponent.strategy_name as opponent_strategy_name,
    opponent.strategy_type as opponent_strategy_type,
    b.n_rounds,
    b.total_score,
    opponent.total_score as opponent_total_score,
    opponent.cooperation_rate as opponent_cooperation_rate,
    b.avg_score_per_round,
    b.cooperation_rate,
    b.defection_rate,
    b.betrayal_events,
    b.forgiveness_events,
    case
        when b.betrayal_events = 0 then 0.0
        else b.forgiveness_events::double / b.betrayal_events
    end as forgiveness_rate,
    case
        when b.total_score > opponent.total_score then 'win'
        when b.total_score < opponent.total_score then 'loss'
        else 'draw'
    end as match_result
from base b
left join base opponent
  on b.run_id = opponent.run_id
 and b.match_id = opponent.match_id
 and b.opponent_player_id = opponent.player_id
 and b.player_id = opponent.opponent_player_id
