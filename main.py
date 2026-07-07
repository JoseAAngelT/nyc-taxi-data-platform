"""Punto de entrada principal del proyecto NYC Taxi Data Platform."""

from src.ingestion.remote_taxi_reader import (
    get_remote_taxi_schema,
    preview_remote_taxi_data,
)


def main() -> None:
    """Ejecuta una primera prueba de lectura remota del dataset."""
    print("NYC Taxi Data Platform")
    print("Probando lectura remota de datos Parquet...")

    get_remote_taxi_schema(year=2025, month=1, taxi_type="yellow")
    preview_remote_taxi_data(year=2025, month=1, taxi_type="yellow", limit=5)


if __name__ == "__main__":
    main()
