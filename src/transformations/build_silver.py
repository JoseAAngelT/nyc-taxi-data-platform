"""Construcción de la capa Silver para el dataset NYC Taxi."""

from __future__ import annotations

from pathlib import Path

import duckdb

PAYMENT_TYPE_MAP = {
    1: "Credit card",
    2: "Cash",
    3: "No charge",
    4: "Dispute",
    5: "Unknown",
    6: "Voided trip",
}


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


def build_silver_output_path(
    silver_path: str,
    year: int,
    month: int,
    taxi_type: str,
) -> Path:
    """Construye la ruta de salida particionada para la capa Silver."""
    month_str = f"{month:02d}"
    file_name = f"{taxi_type}_tripdata_{year}-{month_str}_silver.parquet"

    return (
        Path(silver_path)
        / taxi_type
        / f"year={year}"
        / f"month={month_str}"
        / file_name
    )


def build_payment_case_expression() -> str:
    """Construye la expresión SQL para mapear métodos de pago."""
    cases = []

    for payment_code, payment_name in PAYMENT_TYPE_MAP.items():
        cases.append(f"WHEN payment_type = {payment_code} THEN '{payment_name}'")

    return " ".join(cases)


def build_silver_monthly_file(
    bronze_path: str,
    silver_path: str,
    year: int,
    month: int,
    taxi_type: str,
    overwrite: bool = False,
) -> Path:
    """Construye un archivo Silver mensual a partir de un archivo Bronze."""
    bronze_file_path = build_bronze_file_path(
        bronze_path=bronze_path,
        year=year,
        month=month,
        taxi_type=taxi_type,
    )

    if not bronze_file_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo Bronze: {bronze_file_path}")

    output_path = build_silver_output_path(
        silver_path=silver_path,
        year=year,
        month=month,
        taxi_type=taxi_type,
    )

    if output_path.exists() and not overwrite:
        print(f"Archivo Silver ya existente, se omite: {output_path}")
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)

    payment_case = build_payment_case_expression()

    query = f"""
        COPY (
            WITH source_data AS (
                SELECT
                    VendorID AS vendor_id,
                    tpep_pickup_datetime AS pickup_datetime,
                    tpep_dropoff_datetime AS dropoff_datetime,
                    passenger_count,
                    trip_distance,
                    RatecodeID AS rate_code_id,
                    store_and_fwd_flag,
                    PULocationID AS pickup_location_id,
                    DOLocationID AS dropoff_location_id,
                    payment_type,
                    fare_amount,
                    extra,
                    mta_tax,
                    tip_amount,
                    tolls_amount,
                    improvement_surcharge,
                    total_amount,
                    congestion_surcharge,
                    airport_fee,
                    source_file,
                    ingestion_timestamp,
                    taxi_type,
                    source_year,
                    source_month
                FROM read_parquet('{bronze_file_path.as_posix()}')
            ),

            cleaned_data AS (
                SELECT
                    vendor_id,
                    pickup_datetime,
                    dropoff_datetime,
                    CAST(pickup_datetime AS DATE) AS pickup_date,
                    EXTRACT(YEAR FROM pickup_datetime) AS pickup_year,
                    EXTRACT(MONTH FROM pickup_datetime) AS pickup_month,
                    EXTRACT(DAY FROM pickup_datetime) AS pickup_day,
                    EXTRACT(HOUR FROM pickup_datetime) AS pickup_hour,
                    EXTRACT(DOW FROM pickup_datetime) AS pickup_day_of_week,

                    DATE_DIFF(
                        'minute',
                        pickup_datetime,
                        dropoff_datetime
                    ) AS trip_duration_minutes,

                    passenger_count,
                    trip_distance,
                    rate_code_id,
                    store_and_fwd_flag,
                    pickup_location_id,
                    dropoff_location_id,
                    payment_type,

                    CASE
                        {payment_case}
                        ELSE 'Unknown'
                    END AS payment_type_description,

                    fare_amount,
                    extra,
                    mta_tax,
                    tip_amount,
                    tolls_amount,
                    improvement_surcharge,
                    total_amount,
                    congestion_surcharge,
                    airport_fee,

                    source_file,
                    ingestion_timestamp,
                    taxi_type,
                    source_year,
                    source_month
                FROM source_data
            )

            SELECT *
            FROM cleaned_data
            WHERE pickup_datetime IS NOT NULL
              AND dropoff_datetime IS NOT NULL
              AND dropoff_datetime > pickup_datetime
              AND trip_duration_minutes BETWEEN 1 AND 1440
              AND trip_distance >= 0
              AND total_amount >= 0
              AND fare_amount >= 0
              AND pickup_location_id IS NOT NULL
              AND dropoff_location_id IS NOT NULL
        )
        TO '{output_path.as_posix()}'
        (FORMAT PARQUET);
    """

    print(f"Construyendo archivo Silver: {output_path}")

    with duckdb.connect() as connection:
        connection.execute(query)

    print(f"Archivo Silver generado: {output_path}")

    return output_path


def build_silver_from_config(config: dict) -> list[Path]:
    """Construye la capa Silver usando los parámetros de configuración."""
    bronze_path = config["paths"]["bronze"]
    silver_path = config["paths"]["silver"]
    source_config = config["source"]

    taxi_type = source_config["taxi_type"]
    year = source_config["start_year"]
    start_month = source_config["start_month"]
    end_month = source_config["end_month"]

    silver_files = []

    for month in range(start_month, end_month + 1):
        silver_file = build_silver_monthly_file(
            bronze_path=bronze_path,
            silver_path=silver_path,
            year=year,
            month=month,
            taxi_type=taxi_type,
            overwrite=False,
        )
        silver_files.append(silver_file)

    return silver_files
