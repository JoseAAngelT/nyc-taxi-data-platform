"""Construcción de la capa Bronze para el dataset NYC Taxi."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb


def build_raw_file_name(year: int, month: int, taxi_type: str) -> str:
    """Construye el nombre esperado del archivo Raw."""
    month_str = f"{month:02d}"
    return f"{taxi_type}_tripdata_{year}-{month_str}.parquet"


def build_bronze_output_path(
    bronze_path: str,
    year: int,
    month: int,
    taxi_type: str,
) -> Path:
    """Construye la ruta de salida particionada para la capa Bronze."""
    month_str = f"{month:02d}"
    file_name = f"{taxi_type}_tripdata_{year}-{month_str}_bronze.parquet"

    return (
        Path(bronze_path)
        / taxi_type
        / f"year={year}"
        / f"month={month_str}"
        / file_name
    )


def build_bronze_monthly_file(
    raw_path: str,
    bronze_path: str,
    year: int,
    month: int,
    taxi_type: str,
    overwrite: bool = False,
) -> Path:
    """Construye un archivo Bronze mensual a partir de un archivo Raw."""
    raw_file_name = build_raw_file_name(
        year=year,
        month=month,
        taxi_type=taxi_type,
    )
    raw_file_path = Path(raw_path) / raw_file_name

    if not raw_file_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo Raw: {raw_file_path}")

    output_path = build_bronze_output_path(
        bronze_path=bronze_path,
        year=year,
        month=month,
        taxi_type=taxi_type,
    )

    if output_path.exists() and not overwrite:
        print(f"Archivo Bronze ya existente, se omite: {output_path}")
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)

    ingestion_timestamp = datetime.now(UTC).isoformat()

    query = f"""
        COPY (
            SELECT
                *,
                '{raw_file_name}' AS source_file,
                '{ingestion_timestamp}' AS ingestion_timestamp,
                '{taxi_type}' AS taxi_type,
                {year} AS source_year,
                {month} AS source_month
            FROM read_parquet('{raw_file_path.as_posix()}')
        )
        TO '{output_path.as_posix()}'
        (FORMAT PARQUET);
    """

    print(f"Construyendo archivo Bronze: {output_path}")

    with duckdb.connect() as connection:
        connection.execute(query)

    print(f"Archivo Bronze generado: {output_path}")

    return output_path


def build_bronze_from_config(config: dict) -> list[Path]:
    """Construye la capa Bronze usando los parámetros de configuración."""
    raw_path = config["paths"]["raw"]
    bronze_path = config["paths"]["bronze"]
    source_config = config["source"]

    taxi_type = source_config["taxi_type"]
    year = source_config["start_year"]
    start_month = source_config["start_month"]
    end_month = source_config["end_month"]

    bronze_files = []

    for month in range(start_month, end_month + 1):
        bronze_file = build_bronze_monthly_file(
            raw_path=raw_path,
            bronze_path=bronze_path,
            year=year,
            month=month,
            taxi_type=taxi_type,
            overwrite=False,
        )
        bronze_files.append(bronze_file)

    return bronze_files
