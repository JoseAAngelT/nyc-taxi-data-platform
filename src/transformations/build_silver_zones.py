"""Construcción de la tabla Silver de zonas de taxi."""

from __future__ import annotations

from pathlib import Path

import duckdb


def build_raw_zone_lookup_path(raw_path: str, file_name: str) -> Path:
    """Construye la ruta del archivo Raw de zonas."""
    return Path(raw_path) / file_name


def build_silver_zones_output_path(silver_path: str) -> Path:
    """Construye la ruta de salida para la tabla Silver de zonas."""
    return Path(silver_path) / "zones" / "taxi_zones_silver.parquet"


def build_silver_zones(
    raw_path: str,
    silver_path: str,
    file_name: str,
    overwrite: bool = False,
) -> Path:
    """Construye la tabla Silver de zonas a partir del CSV original."""
    raw_file_path = build_raw_zone_lookup_path(
        raw_path=raw_path,
        file_name=file_name,
    )

    if not raw_file_path.exists():
        raise FileNotFoundError(
            f"No se encontró la tabla Raw de zonas: {raw_file_path}"
        )

    output_path = build_silver_zones_output_path(silver_path=silver_path)

    if output_path.exists() and not overwrite:
        print(f"Tabla Silver de zonas ya existente, se omite: {output_path}")
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)

    query = f"""
        COPY (
            SELECT
                CAST(LocationID AS INTEGER) AS location_id,
                TRIM(Borough) AS borough,
                TRIM(Zone) AS zone_name,
                TRIM(service_zone) AS service_zone
            FROM read_csv_auto(
                '{raw_file_path.as_posix()}',
                HEADER = TRUE
            )
            WHERE LocationID IS NOT NULL
        )
        TO '{output_path.as_posix()}'
        (FORMAT PARQUET);
    """

    print(f"Construyendo tabla Silver de zonas: {output_path}")

    with duckdb.connect() as connection:
        connection.execute(query)

    print(f"Tabla Silver de zonas generada: {output_path}")

    return output_path


def build_silver_zones_from_config(config: dict) -> Path:
    """Construye la tabla Silver de zonas usando la configuración."""
    raw_path = config["paths"]["raw"]
    silver_path = config["paths"]["silver"]
    file_name = config["zone_lookup"]["file_name"]

    return build_silver_zones(
        raw_path=raw_path,
        silver_path=silver_path,
        file_name=file_name,
        overwrite=False,
    )
