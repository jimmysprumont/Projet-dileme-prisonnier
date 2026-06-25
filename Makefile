PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
DBT ?= .venv/bin/dbt
DAGSTER ?= .venv/bin/dagster
VLLM_BIN ?= vllm
VLLM_MODEL ?= HuggingFaceTB/SmolLM2-135M-Instruct
VLLM_DTYPE ?= float32
VLLM_MEMORY_UTILIZATION ?= 0.145
VLLM_MAX_MODEL_LEN ?= 128
VLLM_EXTRA_ARGS ?= --enforce-eager

.PHONY: install test simulate dbt-build run dagster dashboard vllm-serve clean-data

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

dashboard:
	$(PYTHON) -m streamlit run dashboard/app.py

vllm-serve:
	env -u VLLM_BIN -u VLLM_MODEL -u VLLM_DTYPE -u VLLM_MEMORY_UTILIZATION -u VLLM_MAX_MODEL_LEN -u VLLM_EXTRA_ARGS VLLM_TARGET_DEVICE=cpu $(VLLM_BIN) serve $(VLLM_MODEL) --host 127.0.0.1 --port 8000 --dtype $(VLLM_DTYPE) --gpu-memory-utilization $(VLLM_MEMORY_UTILIZATION) --max-model-len $(VLLM_MAX_MODEL_LEN) $(VLLM_EXTRA_ARGS)

clean-data:
	$(PYTHON) -m prisoners_dilemma.cli clean-data
