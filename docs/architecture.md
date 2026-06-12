# Architecture

```text
Dagster
  -> Python simulation
       -> coded strategies
       -> local vLLM-compatible AI agents
       -> data/bronze/*.parquet

  -> dbt-duckdb
       -> Silver analytical tables
       -> Gold aggregate tables

  -> DuckDB export
       -> data/silver/*.parquet
       -> data/gold/*.parquet
```

The repository contains code and documentation only. Generated datasets are excluded from Git so the project can be reproduced from the README.

## Run Versioning

Each execution receives a `run_id`. Bronze, Silver, and Gold data are partitioned by this identifier, which allows several snapshots to coexist locally.

## AI Integration

The simulator calls a local vLLM OpenAI-compatible endpoint when available. If the endpoint is unavailable or returns invalid JSON, the decision falls back to deterministic `tit_for_tat` behavior and records `decision_source = "fallback"`.

## Transformations

dbt reads Bronze Parquet files through DuckDB external sources. Silver models normalize rounds into one row per player per round and calculate behavioral indicators. Gold models expose only aggregates for analysis.
