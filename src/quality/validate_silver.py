"""Validaciones de calidad para la capa Silver."""

from __future__ import annotations

from pathlib import Path

import duckdb

REQUIRED_SILVER_COLUMNS = [
    "vendor_id",
    "pickup_datetime",
    "dropoff_datetime",
    "pickup_date",
    "pickup_year",
    "pickup_month",
    "pickup_day",
    "pickup_hour",
    "pickup_day_of_week",
    "trip_duration_minutes",
    "passenger_count",
    "trip_distance",
    "pickup_location_id",
    "dropoff_location_id",
    "payment_type",
    "payment_type_description",
    "fare_amount",
    "tip_amount",
    "total_amount",
    "source_file",
    "ingestion_timestamp",
    "taxi_type",
    "source_year",
    "source_month",
]


def build_silver_file_path(
    silver_path: str,
    year: int,
    month: int,
    taxi_type: str,
) -> Path:
    """Construye la ruta esperada del archivo Silver mensual."""
    month_str = f"{month:02d}"
    file_name = f"{taxi_type}_tripdata_{year}-{month_str}_silver.parquet"

    return (
        Path(silver_path)
        / taxi_type
        / f"year={year}"
        / f"month={month_str}"
        / file_name
    )


def get_parquet_columns(file_path: Path) -> list[str]:
    """Obtiene las columnas de un archivo Parquet usando DuckDB."""
    query = f"""
        DESCRIBE
        SELECT *
        FROM read_parquet('{file_path.as_posix()}')
    """

    with duckdb.connect() as connection:
        schema = connection.execute(query).fetchdf()

    return schema["column_name"].tolist()


def get_parquet_row_count(file_path: Path) -> int:
    """Obtiene el número de filas de un archivo Parquet."""
    query = f"""
        SELECT COUNT(*) AS row_count
        FROM read_parquet('{file_path.as_posix()}')
    """

    with duckdb.connect() as connection:
        result = connection.execute(query).fetchone()

    return int(result[0])


def validate_required_columns(file_path: Path) -> list[str]:
    """Valida que existan las columnas requeridas en Silver."""
    columns = get_parquet_columns(file_path)

    return [column for column in REQUIRED_SILVER_COLUMNS if column not in columns]


def validate_silver_business_rules(file_path: Path) -> dict[str, int]:
    """Valida reglas básicas de negocio en la capa Silver."""
    query = f"""
        SELECT
            SUM(
                CASE
                    WHEN pickup_datetime IS NULL THEN 1
                    ELSE 0
                END
            ) AS null_pickup_datetime,

            SUM(
                CASE
                    WHEN dropoff_datetime IS NULL THEN 1
                    ELSE 0
                END
            ) AS null_dropoff_datetime,

            SUM(
                CASE
                    WHEN dropoff_datetime <= pickup_datetime THEN 1
                    ELSE 0
                END
            ) AS invalid_datetime_order,

            SUM(
                CASE
                    WHEN trip_duration_minutes <= 0 THEN 1
                    ELSE 0
                END
            ) AS invalid_duration,

            SUM(
                CASE
                    WHEN trip_distance < 0 THEN 1
                    ELSE 0
                END
            ) AS negative_trip_distance,

            SUM(
                CASE
                    WHEN total_amount < 0 THEN 1
                    ELSE 0
                END
            ) AS negative_total_amount,

            SUM(
                CASE
                    WHEN fare_amount < 0 THEN 1
                    ELSE 0
                END
            ) AS negative_fare_amount,

            SUM(
                CASE
                    WHEN pickup_location_id IS NULL THEN 1
                    ELSE 0
                END
            ) AS null_pickup_location_id,

            SUM(
                CASE
                    WHEN dropoff_location_id IS NULL THEN 1
                    ELSE 0
                END
            ) AS null_dropoff_location_id
        FROM read_parquet('{file_path.as_posix()}')
    """

    with duckdb.connect() as connection:
        result = connection.execute(query).fetchdf()

    return result.iloc[0].to_dict()


def validate_silver_monthly_file(
    silver_path: str,
    year: int,
    month: int,
    taxi_type: str,
    min_rows: int = 1,
) -> dict:
    """Ejecuta validaciones de calidad sobre un archivo Silver mensual."""
    file_path = build_silver_file_path(
        silver_path=silver_path,
        year=year,
        month=month,
        taxi_type=taxi_type,
    )

    validation_result = {
        "file_path": str(file_path),
        "exists": file_path.exists(),
        "row_count": 0,
        "min_rows": min_rows,
        "missing_columns": [],
        "business_rule_violations": {},
        "status": "failed",
    }

    if not file_path.exists():
        return validation_result

    row_count = get_parquet_row_count(file_path)
    missing_columns = validate_required_columns(file_path)

    validation_result["row_count"] = row_count
    validation_result["missing_columns"] = missing_columns

    if missing_columns:
        return validation_result

    business_rule_violations = validate_silver_business_rules(file_path)
    validation_result["business_rule_violations"] = business_rule_violations

    has_minimum_rows = row_count >= min_rows
    has_no_business_rule_violations = all(
        value == 0 for value in business_rule_violations.values()
    )

    if has_minimum_rows and has_no_business_rule_violations:
        validation_result["status"] = "passed"

    return validation_result


def validate_silver_from_config(config: dict) -> list[dict]:
    """Valida la capa Silver usando los parámetros de configuración."""
    silver_path = config["paths"]["silver"]
    source_config = config["source"]
    quality_config = config.get("quality", {})

    taxi_type = source_config["taxi_type"]
    year = source_config["start_year"]
    start_month = source_config["start_month"]
    end_month = source_config["end_month"]
    min_rows = quality_config.get("min_silver_rows", 1)

    validation_results = []

    for month in range(start_month, end_month + 1):
        result = validate_silver_monthly_file(
            silver_path=silver_path,
            year=year,
            month=month,
            taxi_type=taxi_type,
            min_rows=min_rows,
        )
        validation_results.append(result)

    failed_results = [
        result for result in validation_results if result["status"] != "passed"
    ]

    print("\nResultados de validación Silver:")

    for result in validation_results:
        print(f"- Archivo: {result['file_path']}")
        print(f"  Estado: {result['status']}")
        print(f"  Filas: {result['row_count']}")

        if result["missing_columns"]:
            print(f"  Columnas faltantes: {result['missing_columns']}")

        if result["business_rule_violations"]:
            print(
                "  Violaciones de reglas de negocio: "
                f"{result['business_rule_violations']}"
            )

    if failed_results:
        raise ValueError("Una o más validaciones Silver fallaron.")

    return validation_results
