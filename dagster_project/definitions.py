from dagster import Definitions

from dagster_project.assets import (
    bronze_simulation,
    dbt_silver_gold,
    gold_quality_checks,
    parquet_exports,
    simulation_config,
)


defs = Definitions(
    assets=[
        simulation_config,
        bronze_simulation,
        dbt_silver_gold,
        parquet_exports,
        gold_quality_checks,
    ]
)
