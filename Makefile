PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
DBT ?= .venv/bin/dbt
DAGSTER ?= .venv/bin/dagster
VLLM_MODEL ?= Qwen/Qwen1.5-0.5B-Chat-GPTQ-Int4

.PHONY: install test simulate dbt-build run dagster vllm-serve clean-data

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest

simulate:
	$(PYTHON) -m prisoners_dilemma.cli simulate --config configs/default.yaml

dbt-build:
	$(DBT) build --project-dir dbt_prisoners --profiles-dir dbt_prisoners

run:
	$(PYTHON) -m prisoners_dilemma.cli run --config configs/default.yaml

dagster:
	$(DAGSTER) dev -f dagster_project/definitions.py

vllm-serve:
	VLLM_TARGET_DEVICE=cpu vllm serve $(VLLM_MODEL) --host 127.0.0.1 --port 8000 --dtype float32

clean-data:
	$(PYTHON) -m prisoners_dilemma.cli clean-data
