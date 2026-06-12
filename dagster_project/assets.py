import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from dagster import AssetExecutionContext, MetadataValue, asset, materialize

from prisoners_dilemma.config import ProjectConfig, load_config
from prisoners_dilemma.simulation import simulate_tournament
from prisoners_dilemma.storage import (
    export_dbt_tables_to_parquet,
    validate_gold_parquet_exports,
    write_bronze_parquet,
)


DEFAULT_CONFIG_PATH = "configs/default.yaml"
DBT_PROJECT_DIR = "dbt_prisoners"
DBT_PROFILES_DIR = "dbt_prisoners"
DUCKDB_PATH = "data/prisoners.duckdb"


@asset
def simulation_config(context: AssetExecutionContext) -> ProjectConfig:
    config_path = os.environ.get("PRISONERS_CONFIG", DEFAULT_CONFIG_PATH)
    config = load_config(config_path)
    context.add_output_metadata({"config_path": MetadataValue.path(config_path)})
    return config


@asset
def bronze_simulation(
    context: AssetExecutionContext,
    simulation_config: ProjectConfig,
) -> dict[str, Any]:
    result = simulate_tournament(simulation_config)
    paths = write_bronze_parquet(result, data_dir=simulation_config.run.data_dir)
    context.add_output_metadata(
        {
            "run_id": result.run_id,
            "rounds": len(result.rounds),
            "bronze_dir": MetadataValue.path(
                str(Path(simulation_config.run.data_dir) / "bronze" / f"run_id={result.run_id}")
            ),
        }
    )
    return {
        "run_id": result.run_id,
        "data_dir": simulation_config.run.data_dir,
        "paths": {name: str(path) for name, path in paths.items()},
    }


@asset
def dbt_silver_gold(
    context: AssetExecutionContext,
    bronze_simulation: dict[str, Any],
) -> dict[str, Any]:
    command = [
        _dbt_executable(),
        "build",
        "--project-dir",
        DBT_PROJECT_DIR,
        "--profiles-dir",
        DBT_PROFILES_DIR,
    ]
    context.log.info("Running dbt: %s", " ".join(command))
    subprocess.run(command, check=True)
    context.add_output_metadata({"duckdb_path": MetadataValue.path(DUCKDB_PATH)})
    return {
        "run_id": bronze_simulation["run_id"],
        "database_path": DUCKDB_PATH,
        "data_dir": bronze_simulation["data_dir"],
    }


@asset
def parquet_exports(
    context: AssetExecutionContext,
    dbt_silver_gold: dict[str, Any],
) -> dict[str, str]:
    paths = export_dbt_tables_to_parquet(
        database_path=dbt_silver_gold["database_path"],
        data_dir=dbt_silver_gold["data_dir"],
        run_id=dbt_silver_gold["run_id"],
    )
    context.add_output_metadata(
        {
            "run_id": dbt_silver_gold["run_id"],
            "export_count": len(paths),
            "gold_dir": MetadataValue.path(
                str(Path(dbt_silver_gold["data_dir"]) / "gold" / f"run_id={dbt_silver_gold['run_id']}")
            ),
        }
    )
    return {name: str(path) for name, path in paths.items()}


@asset
def gold_quality_checks(
    context: AssetExecutionContext,
    parquet_exports: dict[str, str],
) -> dict[str, int]:
    counts = validate_gold_parquet_exports(
        {name: Path(path) for name, path in parquet_exports.items()}
    )
    context.add_output_metadata({name: count for name, count in counts.items()})
    return counts


def run_pipeline(config_path: str = DEFAULT_CONFIG_PATH) -> None:
    os.environ["PRISONERS_CONFIG"] = config_path
    result = materialize(
        [
            simulation_config,
            bronze_simulation,
            dbt_silver_gold,
            parquet_exports,
            gold_quality_checks,
        ]
    )
    if not result.success:
        raise RuntimeError("Dagster materialization failed")


def _dbt_executable() -> str:
    venv_dbt = Path(sys.executable).with_name("dbt")
    if venv_dbt.exists():
        return str(venv_dbt)
    found = shutil.which("dbt")
    if found:
        return found
    raise FileNotFoundError("dbt executable not found. Run `make install` first.")
