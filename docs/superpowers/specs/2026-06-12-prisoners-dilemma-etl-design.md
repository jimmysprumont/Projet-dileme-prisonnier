# Prisoners Dilemma ETL Design

## Context

The project must build a complete local data engineering pipeline around the iterative prisoners dilemma. It must generate original simulation data, transform it into analytical datasets, and expose Gold-level aggregates that allow a data analyst to compare cooperation, betrayal, strategy performance, behavioral drift, and forgiveness.

The source assignment requires:

- A reproducible GitHub repository.
- No generated data committed to the repository.
- Local Parquet datasets.
- A complete Extract/Generate, Load, Transform, and Gold aggregation flow.
- A generative AI dimension using local agents.
- A reflection on multiple runs and versioned snapshots.

The chosen stack is:

- Python for simulation and vLLM calls.
- vLLM local CPU, without Docker, for lightweight local AI agents.
- Parquet as the storage format for Bronze, Silver, and Gold data.
- DuckDB as the local analytical engine.
- dbt-duckdb for Bronze to Silver to Gold transformations.
- Dagster for orchestration.

## Goals

- Generate a reproducible tournament dataset for the iterative prisoners dilemma.
- Compare coded strategies and local AI profiles.
- Store raw and transformed data in a local data lake layout.
- Use dbt for analytical transformations instead of embedding all SQL in Python.
- Use Dagster to make the pipeline observable and easy to run.
- Keep the default run realistic on a CPU-only machine.
- Make the project reproducible from the README without committing data.

## Non-Goals

- The project will not use cloud services.
- The project will not use Docker.
- The project will not assume a GPU.
- The project will not commit generated Bronze, Silver, or Gold data.
- The project will not make every match depend on vLLM, because CPU inference would make the pipeline too slow.

## Architecture

The project is a local data lake orchestrated by Dagster.

```text
Dagster
  -> Python simulation
       -> coded strategies
       -> vLLM local CPU agents
       -> Bronze Parquet

  -> dbt-duckdb
       -> Silver Parquet
       -> Gold Parquet

  -> quality checks and optional analysis exports
```

Data is partitioned by `run_id` so that multiple executions can coexist without overwriting earlier results.

```text
data/
  bronze/run_id=<run_id>/
  silver/run_id=<run_id>/
  gold/run_id=<run_id>/
```

Each run records its parameters: seed, payoff matrix, selected strategies, vLLM model, number of coded rounds, number of AI rounds, and timestamp.

## Repository Structure

```text
README.md
Makefile
pyproject.toml
.gitignore
configs/
  default.yaml
src/
  prisoners_dilemma/
    simulation/
    strategies/
    ai_agents/
    io/
dagster_project/
  definitions.py
  assets.py
dbt_prisoners/
  dbt_project.yml
  profiles.yml.example
  models/
    sources.yml
    silver/
    gold/
docs/
  architecture.md
  superpowers/specs/
```

## Simulation Design

The simulation includes two families of players.

Coded strategies:

- `always_cooperate`
- `always_defect`
- `tit_for_tat`
- `random`
- `grim_trigger`
- `generous_tit_for_tat`

AI profiles through vLLM:

- `empathic_ai`: tries to cooperate unless exploitation is repeated.
- `calculator_ai`: maximizes expected score from the recent pattern.
- `resentful_ai`: cooperates initially but forgives slowly after betrayal.
- `opportunist_ai`: adapts aggressively to recent opponent behavior.

The payoff matrix is configurable. The default matrix is:

| Player A | Player B | A payoff | B payoff |
| --- | --- | ---: | ---: |
| C | C | 3 | 3 |
| C | D | 0 | 5 |
| D | C | 5 | 0 |
| D | D | 1 | 1 |

The default run uses many coded rounds and fewer AI rounds:

- Coded strategy matches: high-volume, for example 2,000 rounds.
- AI profile matches: smaller, for example 50 to 200 rounds.

This keeps the pipeline realistic on a CPU-only machine while still satisfying the generative AI requirement.

## vLLM Local CPU Design

vLLM is used as a local OpenAI-compatible server. The simulator calls:

```text
http://localhost:8000/v1/chat/completions
```

The recommended lightweight model is `Qwen/Qwen1.5-0.5B-Chat-GPTQ-Int4`. If that model is not suitable on the user's machine, the README may document a fallback such as `TheBloke/TinyLlama-1.1B-Chat-v1.0-GPTQ`.

The project runs without Docker. On macOS arm64, vLLM installation is documented as a native local setup, with CPU as the target device.

AI prompts include a compact state, not the full match history:

```text
profile
round_index
last_my_choices
last_opponent_choices
my_score
opponent_score
```

The model must answer with strict JSON:

```json
{
  "choice": "C",
  "reasoning": "short explanation"
}
```

If vLLM is unavailable, times out, or returns invalid JSON, the simulator records a fallback decision. The Bronze row keeps this explicit with:

- `decision_source = "vllm"` when the local model answered correctly.
- `decision_source = "fallback"` when deterministic fallback logic was used.

The fallback strategy is documented and deterministic, based on `tit_for_tat`. This preserves reproducibility and avoids a hard failure during correction.

## Bronze Data

Bronze data is the generated raw layer. It records what happened during each run with minimal transformation.

Tables:

```text
runs
  run_id
  started_at
  seed
  payoff_matrix
  n_rounds_coded
  n_rounds_ai
  vllm_model
  config_hash

players
  run_id
  player_id
  strategy_name
  strategy_type
  profile_prompt

matches
  run_id
  match_id
  player_a_id
  player_b_id
  n_rounds
  match_type

rounds
  run_id
  match_id
  round_index
  player_a_choice
  player_b_choice
  player_a_payoff
  player_b_payoff
  player_a_cumulative_score
  player_b_cumulative_score
  player_a_reasoning
  player_b_reasoning
  player_a_decision_source
  player_b_decision_source
```

Bronze files are written as Parquet and partitioned by `run_id`.

## Silver Transformations

dbt-duckdb reads Bronze Parquet sources and builds Silver models. Silver is clean, normalized, and enriched.

Core Silver models:

```text
silver_rounds
silver_player_rounds
silver_player_match_stats
```

Silver enrichment includes:

- Standardized choices: `C` and `D`.
- One row per player per round in `silver_player_rounds`.
- Current payoff and cumulative score.
- Opponent choice.
- Previous own choice.
- Previous opponent choice.
- Whether the player was betrayed in the previous round.
- Whether the player returned to cooperation after betrayal.
- Cooperation and defection flags.
- Round bucket for behavioral drift analysis.

Invalid choices are either corrected when safely inferable or excluded with a documented reason. Quality checks ensure that analytical models only use valid `C` and `D` choices.

## Gold Transformations

Gold models contain only aggregates and analytical views. They do not expose raw round rows.

Required Gold models:

```text
tournament_summary
  run_id
  strategy_name
  strategy_type
  total_score
  avg_score_per_round
  cooperation_rate
  defection_rate
  wins
  losses
  draws
  rank

matchup_matrix
  run_id
  strategy_a
  strategy_b
  avg_score_a
  avg_score_b
  cooperation_rate_a
  cooperation_rate_b
  n_matches

behavioral_drift
  run_id
  strategy_name
  round_bucket
  cooperation_rate
  defection_rate
  avg_score

forgiveness_index
  run_id
  strategy_name
  betrayal_events
  forgiveness_events
  forgiveness_rate
```

Optional Gold model:

```text
run_comparison
  compares metrics across two or more run_ids
```

Gold outputs are stored as Parquet so a data analyst can query them directly with DuckDB, Python, or BI tools.

## Dagster Orchestration

Dagster defines the pipeline as assets.

Assets:

```text
simulation_config
  Loads and validates run parameters.

bronze_simulation
  Runs the tournament simulation and writes Bronze Parquet.

dbt_silver_gold
  Executes dbt build for Silver and Gold transformations.

gold_quality_checks
  Checks that Gold tables exist and contain valid metric ranges.

analysis_exports
  Optionally exports small CSV or PNG summaries for exploratory analysis.
```

Dagster is responsible for execution order, logs, observability, and reproducibility. dbt remains responsible for SQL transformations.

## Commands

The README will expose simple commands.

```bash
make install
make vllm-serve
make dagster
make run
make dbt-build
make clean-data
```

The default path for a full run is:

```bash
make run
```

This command will generate Bronze data, run dbt transformations, and validate Gold outputs through Dagster.

## Quality And Testing

The project includes lightweight tests and checks:

- Unit tests for payoff calculation.
- Unit tests for coded strategies.
- Unit tests for vLLM response parsing and fallback behavior.
- dbt tests for accepted values `C` and `D`.
- dbt tests for non-null keys.
- dbt tests for metric ranges between 0 and 1.
- Dagster asset checks for expected Gold outputs.

The minimum successful verification is:

```bash
pytest
dbt build --project-dir dbt_prisoners
make run
```

## Reproducibility

Generated data is not committed. The repository commits only code and documentation.

`.gitignore` excludes:

```text
data/bronze/
data/silver/
data/gold/
*.duckdb
.venv/
```

The README explains how to regenerate all data locally.

Each run gets a unique `run_id`, timestamp, seed, and config hash. This allows the user to compare multiple snapshots without overwriting previous runs.

## Main Trade-Offs

Using vLLM without GPU makes AI inference slow. The design addresses this by limiting AI match volume while keeping coded strategy matches large enough for meaningful analysis.

Using dbt adds structure and documentation to transformations, but it requires a little more setup than pure Python. This is acceptable because the assignment is about ETL and ELT architecture.

Using Dagster adds orchestration overhead, but it makes the pipeline easier to explain and inspect during evaluation.

Avoiding Docker reduces portability but matches the user's local constraints.

## Success Criteria

The project is successful when:

- A fresh clone can reproduce the pipeline from the README.
- No generated data is required in the repository.
- Bronze, Silver, and Gold Parquet datasets are generated locally.
- dbt performs the Silver and Gold transformations.
- Dagster orchestrates the pipeline.
- vLLM local CPU agents contribute decisions to at least part of the tournament.
- Gold outputs allow comparison of strategies, behavioral drift analysis, matchup analysis, and forgiveness analysis.
