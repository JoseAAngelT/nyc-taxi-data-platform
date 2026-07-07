"""Lectura remota de archivos Parquet del dataset NYC Taxi."""

from __future__ import annotations

import duckdb

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"


def build_taxi_file_url(year: int, month: int, taxi_type: str = "yellow") -> str:
    """Construye la URL del archivo Parquet mensual de NYC Taxi."""
    month_str = f"{month:02d}"
    return f"{BASE_URL}/{taxi_type}_tripdata_{year}-{month_str}.parquet"


def preview_remote_taxi_data(
    year: int,
    month: int,
    taxi_type: str = "yellow",
    limit: int = 10,
) -> None:
    """Lee una muestra remota del archivo Parquet sin descargarlo localmente."""
    file_url = build_taxi_file_url(year, month, taxi_type)

    query = f"""
        SELECT *
        FROM read_parquet('{file_url}')
        LIMIT {limit}
    """

    with duckdb.connect() as connection:
        connection.execute("INSTALL httpfs;")
        connection.execute("LOAD httpfs;")

        df = connection.execute(query).fetchdf()

    print(f"Archivo remoto consultado: {file_url}")
    print(f"Filas mostradas: {len(df)}")
    print(df.head(limit))


def get_remote_taxi_schema(
    year: int,
    month: int,
    taxi_type: str = "yellow",
) -> None:
    """Muestra el esquema del archivo Parquet remoto."""
    file_url = build_taxi_file_url(year, month, taxi_type)

    query = f"""
        DESCRIBE
        SELECT *
        FROM read_parquet('{file_url}')
    """

    with duckdb.connect() as connection:
        connection.execute("INSTALL httpfs;")
        connection.execute("LOAD httpfs;")

        schema = connection.execute(query).fetchdf()

    print(f"Esquema del archivo remoto: {file_url}")
    print(schema)
