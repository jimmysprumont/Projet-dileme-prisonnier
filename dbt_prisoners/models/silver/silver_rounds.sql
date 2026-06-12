{{ config(materialized='table') }}

select
    cast(run_id as varchar) as run_id,
    cast(match_id as varchar) as match_id,
    cast(round_index as integer) as round_index,
    cast(player_a_id as varchar) as player_a_id,
    cast(player_b_id as varchar) as player_b_id,
    upper(cast(player_a_choice as varchar)) as player_a_choice,
    upper(cast(player_b_choice as varchar)) as player_b_choice,
    cast(player_a_payoff as integer) as player_a_payoff,
    cast(player_b_payoff as integer) as player_b_payoff,
    cast(player_a_cumulative_score as integer) as player_a_cumulative_score,
    cast(player_b_cumulative_score as integer) as player_b_cumulative_score,
    cast(player_a_reasoning as varchar) as player_a_reasoning,
    cast(player_b_reasoning as varchar) as player_b_reasoning,
    cast(player_a_decision_source as varchar) as player_a_decision_source,
    cast(player_b_decision_source as varchar) as player_b_decision_source
from {{ source('bronze', 'rounds') }}
where upper(cast(player_a_choice as varchar)) in ('C', 'D')
  and upper(cast(player_b_choice as varchar)) in ('C', 'D')
