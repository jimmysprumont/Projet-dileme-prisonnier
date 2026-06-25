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

Sur Mac Apple Silicon, les wheels Linux `manylinux_aarch64` ne sont pas compatibles. Il faut construire vLLM depuis les sources.

Important: le chemin de ce projet contient des espaces. Torch/Inductor peut echouer pendant le warmup vLLM si vLLM est installe dans ce `.venv`. Installe donc vLLM dans un environnement separe dont le chemin ne contient pas d'espace:

```bash
xcode-select --install
python3 -m venv /tmp/vllm-env
/tmp/vllm-env/bin/python -m pip install --upgrade pip uv
cd /tmp
git clone https://github.com/vllm-project/vllm.git
cd vllm
/tmp/vllm-env/bin/uv pip install --python /tmp/vllm-env/bin/python -r requirements/cpu.txt --index-strategy unsafe-best-match
/tmp/vllm-env/bin/uv pip install --python /tmp/vllm-env/bin/python -e .
```

Si tu avais deja clone vLLM dans `/tmp/vllm`, reprends simplement ici:

```bash
cd /tmp/vllm
/tmp/vllm-env/bin/uv pip install --python /tmp/vllm-env/bin/python -r requirements/cpu.txt --index-strategy unsafe-best-match
/tmp/vllm-env/bin/uv pip install --python /tmp/vllm-env/bin/python -e .
```

```bash
/tmp/vllm-env/bin/vllm --help
```

Sur une machine sans GPU, lancer ensuite un petit modele via vLLM CPU:

```bash
make vllm-serve VLLM_BIN=/tmp/vllm-env/bin/vllm
```

Par defaut, le Makefile limite vLLM pour un MacBook Air 8 Go:

```text
VLLM_DTYPE=float32
VLLM_MEMORY_UTILIZATION=0.145
VLLM_MAX_MODEL_LEN=128
VLLM_EXTRA_ARGS=--enforce-eager
```

Sur le backend CPU, le flag vLLM `--gpu-memory-utilization` controle en pratique la fraction de memoire CPU reservee. Sur le MacBook Air 8 Go teste, `0.145` demarre avec environ 1.17 GiB de RAM disponible, alors que `0.20` peut deja demander trop de RAM libre. Garde donc la valeur par defaut et ferme des applications si le serveur refuse encore de demarrer.

```bash
make vllm-serve VLLM_BIN=/tmp/vllm-env/bin/vllm
```

Le modele par defaut est:

```text
HuggingFaceTB/SmolLM2-135M-Instruct
```

Ce modele est volontairement tres petit pour rester coherent avec une machine sans GPU. Le client IA demande une reponse d'un seul caractere (`C` ou `D`) afin de limiter la generation vLLM CPU.

Le modele GPTQ `Qwen/Qwen1.5-0.5B-Chat-GPTQ-Int4` peut echouer sur macOS CPU avec un kernel manquant (`cpu_gemm_wna16`). `Qwen/Qwen2.5-0.5B-Instruct` demarre parfois, mais il peut rester bloque pendant la generation sur un MacBook Air 8 Go. Le modele 135M ci-dessus est donc le choix par defaut.

Si vLLM n'est pas lance, le pipeline reste reproductible: les agents IA utilisent un fallback deterministe de type `tit_for_tat`, et la colonne `decision_source` indique `fallback`.

Cette decision est volontaire: le correcteur peut executer tout le pipeline sans GPU ni serveur IA, mais le projet sait utiliser vLLM local si le serveur est disponible.

## Agents IA

Les agents appeles via vLLM ont chacun leur fichier de prompt:

```text
agents/empathic_ai.md
agents/calculator_ai.md
```

Ils sont references dans `configs/default.yaml` avec `prompt_file`. Cela permet de modifier le comportement d'un agent sans toucher au code Python:

```yaml
ai_profiles:
  - name: empathic_ai
    prompt_file: agents/empathic_ai.md
```

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

## Dashboard Streamlit

Apres avoir genere les donnees avec `make run`, lancer le dashboard:

```bash
make dashboard
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
