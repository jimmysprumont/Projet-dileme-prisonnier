{{ config(materialized='table') }}

with player_rows as (
    select
        run_id,
        match_id,
        round_index,
        player_a_id as player_id,
        player_b_id as opponent_player_id,
        player_a_choice as choice,
        player_b_choice as opponent_choice,
        player_a_payoff as payoff,
        player_b_payoff as opponent_payoff,
        player_a_cumulative_score as cumulative_score,
        player_b_cumulative_score as opponent_cumulative_score,
        player_a_reasoning as reasoning,
        player_a_decision_source as decision_source,
        'A' as seat
    from {{ ref('silver_rounds') }}

    union all

    select
        run_id,
        match_id,
        round_index,
        player_b_id as player_id,
        player_a_id as opponent_player_id,
        player_b_choice as choice,
        player_a_choice as opponent_choice,
        player_b_payoff as payoff,
        player_a_payoff as opponent_payoff,
        player_b_cumulative_score as cumulative_score,
        player_a_cumulative_score as opponent_cumulative_score,
        player_b_reasoning as reasoning,
        player_b_decision_source as decision_source,
        'B' as seat
    from {{ ref('silver_rounds') }}
),
with_history as (
    select
        *,
        lag(choice) over (
            partition by run_id, match_id, player_id
            order by round_index
        ) as previous_choice,
        lag(opponent_choice) over (
            partition by run_id, match_id, player_id
            order by round_index
        ) as previous_opponent_choice
    from player_rows
)
select
    h.run_id,
    h.match_id,
    h.round_index,
    h.player_id,
    h.opponent_player_id,
    p.strategy_name,
    p.strategy_type,
    h.choice,
    h.opponent_choice,
    h.payoff,
    h.opponent_payoff,
    h.cumulative_score,
    h.opponent_cumulative_score,
    h.reasoning,
    h.decision_source,
    h.seat,
    h.previous_choice,
    h.previous_opponent_choice,
    case when h.previous_opponent_choice = 'D' then true else false end as was_betrayed_previous_round,
    case
        when h.previous_opponent_choice = 'D' and h.choice = 'C' then true
        else false
    end as returned_to_cooperation,
    case when h.choice = 'C' then 1 else 0 end as cooperation_flag,
    case when h.choice = 'D' then 1 else 0 end as defection_flag,
    cast(floor((h.round_index - 1) / {{ var('round_bucket_size', 25) }}) + 1 as integer) as round_bucket
from with_history h
left join {{ source('bronze', 'players') }} p
  on h.run_id = p.run_id
 and h.player_id = p.player_id
