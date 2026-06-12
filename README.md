# Prisoners Dilemma ETL/ELT

Projet local de data engineering autour du dilemme du prisonnier iteratif.

Le pipeline genere ses propres donnees, les stocke en Parquet, les transforme avec dbt + DuckDB, puis orchestre l'ensemble avec Dagster.

## Stack

- Python pour la simulation.
- vLLM local CPU, sans Docker, via API OpenAI-compatible.
- Parquet pour Bronze, Silver et Gold.
- DuckDB comme moteur analytique local.
- dbt-duckdb pour transformer Bronze vers Silver puis Gold.
- Dagster pour orchestrer le pipeline.

## Installation

```bash
make install
```

## Lancer vLLM localement

Le projet n'utilise pas le cloud et n'utilise pas Docker.

`make install` n'installe pas vLLM, car son installation CPU native depend fortement de la machine. Installe vLLM separement en suivant la documentation officielle CPU/macOS, puis verifie que la commande suivante repond:

```bash
vllm --help
```

Sur une machine sans GPU, lancer ensuite un petit modele via vLLM CPU:

```bash
make vllm-serve
```

Le modele par defaut est:

```text
Qwen/Qwen1.5-0.5B-Chat-GPTQ-Int4
```

Si vLLM n'est pas lance, le pipeline reste reproductible: les agents IA utilisent un fallback deterministe de type `tit_for_tat`, et la colonne `decision_source` indique `fallback`.

Cette decision est volontaire: le correcteur peut executer tout le pipeline sans GPU ni serveur IA, mais le projet sait utiliser vLLM local si le serveur est disponible.

## Execution

Generation Bronze seule:

```bash
make simulate
```

Pipeline complet orchestre par Dagster:

```bash
make run
```

Interface Dagster:

```bash
make dagster
```

Transformations dbt seules:

```bash
make dbt-build
```

Tests:

```bash
make test
```

## Donnees

Les donnees generees ne sont pas versionnees.

```text
data/bronze/run_id=<run_id>/
data/silver/run_id=<run_id>/
data/gold/run_id=<run_id>/
```

Bronze contient les sorties brutes de simulation. Silver contient les lignes nettoyees et enrichies. Gold contient uniquement les agregats prets pour analyse:

- `tournament_summary`
- `matchup_matrix`
- `behavioral_drift`
- `forgiveness_index`
- `run_comparison`

## Nettoyage

```bash
make clean-data
```
