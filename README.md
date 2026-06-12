# Prisoners Dilemma ETL/ELT

Projet local de data engineering autour du dilemme du prisonnier iteratif.

Le pipeline genere ses propres donnees, les stocke en Parquet, les transforme avec dbt + DuckDB, puis orchestre l'ensemble avec Dagster.

## Stack

- Python pour la simulation.
- vLLM local CPU, via API OpenAI-compatible.
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

Sur Mac Apple Silicon, les wheels Linux `manylinux_aarch64` ne sont pas compatibles. Il faut construire vLLM depuis les sources. Depuis le `.venv` du projet:

```bash
xcode-select --install
pip install uv
cd /tmp
git clone https://github.com/vllm-project/vllm.git
cd vllm
uv pip install -r requirements/cpu.txt --index-strategy unsafe-best-match
uv pip install -e .
```

Si tu avais deja clone vLLM dans `/tmp/vllm`, reprends simplement ici:

```bash
cd /tmp/vllm
uv pip install -r requirements/cpu.txt --index-strategy unsafe-best-match
uv pip install -e .
```

```bash
vllm --help
```

Sur une machine sans GPU, lancer ensuite un petit modele via vLLM CPU:

```bash
make vllm-serve
```

Par defaut, le Makefile limite vLLM pour un MacBook Air 8 Go:

```text
VLLM_DTYPE=bfloat16
VLLM_MEMORY_UTILIZATION=0.25
VLLM_MAX_MODEL_LEN=2048
```

Sur le backend CPU, le flag vLLM `--gpu-memory-utilization` controle en pratique la fraction de memoire CPU reservee. Si le serveur refuse encore de demarrer par manque de RAM, ferme des applications ou baisse encore:

```bash
make vllm-serve VLLM_MEMORY_UTILIZATION=0.15 VLLM_MAX_MODEL_LEN=1024
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

Les donnees generees ne sont pas versionnees dans git mais sont historisées via run_id.

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
