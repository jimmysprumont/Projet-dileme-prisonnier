# Prisoners Dilemma ETL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible local ETL/ELT project for the iterative prisoners dilemma using Python simulation, local vLLM-compatible AI agents, Parquet storage, dbt-duckdb transformations, and Dagster orchestration.

**Architecture:** Python generates Bronze Parquet datasets partitioned by `run_id`. dbt-duckdb reads Bronze sources, transforms them into Silver and Gold analytical models, and DuckDB exports those models to Parquet. Dagster orchestrates the simulation, dbt build, export, and validation assets.

**Tech Stack:** Python 3.11+, pandas, pyarrow, requests, PyYAML, DuckDB, dbt-duckdb, Dagster, dagster-dbt, pytest, vLLM served locally through its OpenAI-compatible HTTP API.

---

## File Structure

- `pyproject.toml`: package metadata, dependencies, console scripts, pytest config.
- `.gitignore`: ignore generated data, virtualenv, dbt targets, DuckDB files.
- `Makefile`: reproducible commands for install, vLLM serve, simulation, dbt, Dagster, tests.
- `README.md`: end-to-end reproduction guide.
- `configs/default.yaml`: default run parameters.
- `src/prisoners_dilemma/config.py`: load and validate YAML configuration.
- `src/prisoners_dilemma/domain.py`: shared dataclasses, payoff function, constants.
- `src/prisoners_dilemma/strategies.py`: coded strategies.
- `src/prisoners_dilemma/vllm_client.py`: local vLLM OpenAI-compatible client, strict JSON parser, fallback handling.
- `src/prisoners_dilemma/simulation.py`: tournament simulation engine.
- `src/prisoners_dilemma/storage.py`: Parquet writing and dbt export helpers.
- `src/prisoners_dilemma/cli.py`: command line entry points.
- `tests/`: behavior tests for scoring, strategies, vLLM parsing, simulation output.
- `dbt_prisoners/`: dbt-duckdb project with Bronze sources, Silver models, Gold models, and tests.
- `dagster_project/`: Dagster assets and definitions.
- `docs/architecture.md`: concise architecture documentation for the report.

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `Makefile`
- Create: `configs/default.yaml`
- Create: package directories under `src/`, `tests/`, `dbt_prisoners/`, and `dagster_project/`

- [ ] Add package metadata and dependencies.
- [ ] Add commands for install, tests, simulation, dbt, Dagster, and vLLM serve.
- [ ] Add default config with local CPU-friendly parameters.
- [ ] Run: `python3 -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"`
- [ ] Expected: dependencies install successfully.
- [ ] Commit scaffolding.

## Task 2: Domain And Strategies With TDD

**Files:**
- Create: `src/prisoners_dilemma/domain.py`
- Create: `src/prisoners_dilemma/strategies.py`
- Create: `tests/test_domain.py`
- Create: `tests/test_strategies.py`

- [ ] Write tests for the standard payoff matrix.
- [ ] Run tests and verify they fail before implementation.
- [ ] Implement `Choice`, `PayoffMatrix`, `score_round`, and strategy classes.
- [ ] Write tests for `always_cooperate`, `always_defect`, `tit_for_tat`, `grim_trigger`, and deterministic `random`.
- [ ] Run tests and verify they pass.
- [ ] Commit domain and strategy implementation.

## Task 3: vLLM Client And Fallback With TDD

**Files:**
- Create: `src/prisoners_dilemma/vllm_client.py`
- Create: `tests/test_vllm_client.py`

- [ ] Write tests for parsing valid JSON model responses.
- [ ] Write tests for invalid response fallback to deterministic `tit_for_tat` behavior.
- [ ] Run tests and verify they fail before implementation.
- [ ] Implement `VLLMClient`, `parse_ai_decision`, and `fallback_decision`.
- [ ] Run tests and verify they pass.
- [ ] Commit vLLM client implementation.

## Task 4: Simulation Engine And Parquet Storage

**Files:**
- Create: `src/prisoners_dilemma/config.py`
- Create: `src/prisoners_dilemma/simulation.py`
- Create: `src/prisoners_dilemma/storage.py`
- Create: `src/prisoners_dilemma/cli.py`
- Create: `tests/test_simulation.py`
- Create: `tests/test_storage.py`

- [ ] Write tests for a small deterministic tournament.
- [ ] Write tests for expected Bronze tables and columns.
- [ ] Run tests and verify they fail before implementation.
- [ ] Implement config loading, simulation, Parquet writing, and CLI commands.
- [ ] Run tests and verify they pass.
- [ ] Run a small simulation into `data/bronze`.
- [ ] Commit simulation and storage implementation.

## Task 5: dbt DuckDB Transformations

**Files:**
- Create: `dbt_prisoners/dbt_project.yml`
- Create: `dbt_prisoners/profiles.yml`
- Create: `dbt_prisoners/models/sources.yml`
- Create: `dbt_prisoners/models/silver/*.sql`
- Create: `dbt_prisoners/models/gold/*.sql`
- Create: `dbt_prisoners/models/schema.yml`

- [ ] Define Bronze Parquet sources with `external_location`.
- [ ] Implement `silver_rounds`, `silver_player_rounds`, and `silver_player_match_stats`.
- [ ] Implement `tournament_summary`, `matchup_matrix`, `behavioral_drift`, `forgiveness_index`, and `run_comparison`.
- [ ] Add dbt tests for non-null keys, accepted values, and metric ranges.
- [ ] Run `dbt build --project-dir dbt_prisoners --profiles-dir dbt_prisoners`.
- [ ] Commit dbt project.

## Task 6: Dagster Orchestration

**Files:**
- Create: `dagster_project/assets.py`
- Create: `dagster_project/definitions.py`
- Create: `dagster_project/__init__.py`
- Modify: `src/prisoners_dilemma/storage.py`
- Modify: `Makefile`

- [ ] Implement assets: `simulation_config`, `bronze_simulation`, `dbt_silver_gold`, `parquet_exports`, `gold_quality_checks`.
- [ ] Make `make run` execute Dagster materialization in process.
- [ ] Make `make dagster` start the local Dagster UI.
- [ ] Run `make run`.
- [ ] Commit Dagster orchestration.

## Task 7: Documentation And Verification

**Files:**
- Create: `README.md`
- Create: `docs/architecture.md`
- Modify: `.gitignore`

- [ ] Document setup, vLLM native local usage without Docker, pipeline commands, and expected outputs.
- [ ] Document that generated data is excluded from Git.
- [ ] Run `pytest`.
- [ ] Run a small `make run`.
- [ ] Run `git status --short` and verify generated data is ignored.
- [ ] Commit docs and final verification fixes.

## Self-Review

- Spec coverage: The plan covers local generation, vLLM local agents, Bronze/Silver/Gold Parquet, dbt transformations, Dagster orchestration, tests, README reproduction, and ignored generated data.
- Placeholder scan: No intentionally unresolved implementation placeholders remain.
- Scope check: The work is broad but cohesive as one project scaffold; each task produces a testable layer.
