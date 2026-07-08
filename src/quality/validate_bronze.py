"""Validaciones de calidad para la capa Bronze."""

from __future__ import annotations

from pathlib import Path

import duckdb

REQUIRED_METADATA_COLUMNS = [
    "source_file",
    "ingestion_timestamp",
    "taxi_type",
    "source_year",
    "source_month",
]


def build_bronze_file_path(
    bronze_path: str,
    year: int,
    month: int,
    taxi_type: str,
) -> Path:
    """Construye la ruta esperada del archivo Bronze mensual."""
    month_str = f"{month:02d}"
    file_name = f"{taxi_type}_tripdata_{year}-{month_str}_bronze.parquet"

    return (
        Path(bronze_path)
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


def validate_required_metadata_columns(file_path: Path) -> list[str]:
    """Valida que existan las columnas técnicas requeridas."""
    columns = get_parquet_columns(file_path)
    missing_columns = [
        column for column in REQUIRED_METADATA_COLUMNS if column not in columns
    ]

    return missing_columns


def validate_metadata_nulls(file_path: Path) -> dict[str, int]:
    """Valida valores nulos en las columnas técnicas Bronze."""
    null_checks = []

    for column in REQUIRED_METADATA_COLUMNS:
        null_checks.append(
            f"SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) AS {column}_nulls"
        )

    query = f"""
        SELECT
            {", ".join(null_checks)}
        FROM read_parquet('{file_path.as_posix()}')
    """

    with duckdb.connect() as connection:
        result = connection.execute(query).fetchdf()

    return result.iloc[0].to_dict()


def validate_bronze_monthly_file(
    bronze_path: str,
    year: int,
    month: int,
    taxi_type: str,
    min_rows: int = 1,
) -> dict:
    """Ejecuta validaciones de calidad sobre un archivo Bronze mensual."""
    file_path = build_bronze_file_path(
        bronze_path=bronze_path,
        year=year,
        month=month,
        taxi_type=taxi_type,
    )

    validation_result = {
        "file_path": str(file_path),
        "exists": file_path.exists(),
        "row_count": 0,
        "min_rows": min_rows,
        "missing_metadata_columns": [],
        "metadata_nulls": {},
        "status": "failed",
    }

    if not file_path.exists():
        return validation_result

    row_count = get_parquet_row_count(file_path)
    missing_metadata_columns = validate_required_metadata_columns(file_path)

    validation_result["row_count"] = row_count
    validation_result["missing_metadata_columns"] = missing_metadata_columns

    if missing_metadata_columns:
        return validation_result

    metadata_nulls = validate_metadata_nulls(file_path)
    validation_result["metadata_nulls"] = metadata_nulls

    has_minimum_rows = row_count >= min_rows
    has_no_metadata_nulls = all(value == 0 for value in metadata_nulls.values())

    if has_minimum_rows and has_no_metadata_nulls:
        validation_result["status"] = "passed"

    return validation_result


def validate_bronze_from_config(config: dict) -> list[dict]:
    """Valida la capa Bronze usando los parámetros de configuración."""
    bronze_path = config["paths"]["bronze"]
    source_config = config["source"]
    quality_config = config.get("quality", {})

    taxi_type = source_config["taxi_type"]
    year = source_config["start_year"]
    start_month = source_config["start_month"]
    end_month = source_config["end_month"]
    min_rows = quality_config.get("min_bronze_rows", 1)

    validation_results = []

    for month in range(start_month, end_month + 1):
        result = validate_bronze_monthly_file(
            bronze_path=bronze_path,
            year=year,
            month=month,
            taxi_type=taxi_type,
            min_rows=min_rows,
        )
        validation_results.append(result)

    failed_results = [
        result for result in validation_results if result["status"] != "passed"
    ]

    print("\nResultados de validación Bronze:")

    for result in validation_results:
        print(f"- Archivo: {result['file_path']}")
        print(f"  Estado: {result['status']}")
        print(f"  Filas: {result['row_count']}")

        if result["missing_metadata_columns"]:
            print(
                f"  Columnas técnicas faltantes: {result['missing_metadata_columns']}"
            )

        if result["metadata_nulls"]:
            print(f"  Nulos en metadatos: {result['metadata_nulls']}")

    if failed_results:
        raise ValueError("Una o más validaciones Bronze fallaron.")

    return validation_results
