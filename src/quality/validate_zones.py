"""Validaciones de calidad para la tabla Silver de zonas."""

from __future__ import annotations

from pathlib import Path

import duckdb

REQUIRED_ZONE_COLUMNS = [
    "location_id",
    "borough",
    "zone_name",
    "service_zone",
]


def build_silver_zones_path(silver_path: str) -> Path:
    """Construye la ruta esperada de la tabla Silver de zonas."""
    return Path(silver_path) / "zones" / "taxi_zones_silver.parquet"


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


def validate_required_zone_columns(file_path: Path) -> list[str]:
    """Valida que existan las columnas requeridas en la tabla de zonas."""
    columns = get_parquet_columns(file_path)

    return [column for column in REQUIRED_ZONE_COLUMNS if column not in columns]


def validate_zone_business_rules(file_path: Path) -> dict[str, int]:
    """Valida reglas básicas de calidad para zonas."""
    query = f"""
        SELECT
            COUNT(*) AS row_count,

            SUM(
                CASE
                    WHEN location_id IS NULL THEN 1
                    ELSE 0
                END
            ) AS null_location_id,

            SUM(
                CASE
                    WHEN borough IS NULL OR borough = '' THEN 1
                    ELSE 0
                END
            ) AS null_borough,

            SUM(
                CASE
                    WHEN zone_name IS NULL OR zone_name = '' THEN 1
                    ELSE 0
                END
            ) AS null_zone_name,

            COUNT(*) - COUNT(DISTINCT location_id) AS duplicate_location_id
        FROM read_parquet('{file_path.as_posix()}')
    """

    with duckdb.connect() as connection:
        result = connection.execute(query).fetchdf()

    return result.iloc[0].to_dict()


def validate_zones_from_config(config: dict) -> dict:
    """Valida la tabla Silver de zonas usando la configuración."""
    silver_path = config["paths"]["silver"]
    min_rows = config.get("quality", {}).get("min_zone_rows", 1)

    file_path = build_silver_zones_path(silver_path=silver_path)

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
        print("\nResultado de validación de zonas:")
        print(f"- Archivo: {file_path}")
        print("  Estado: failed")
        print("  Motivo: archivo no encontrado")
        raise ValueError("La validación de zonas falló.")

    missing_columns = validate_required_zone_columns(file_path)
    validation_result["missing_columns"] = missing_columns

    if missing_columns:
        print("\nResultado de validación de zonas:")
        print(f"- Archivo: {file_path}")
        print("  Estado: failed")
        print(f"  Columnas faltantes: {missing_columns}")
        raise ValueError("La validación de zonas falló.")

    business_rules = validate_zone_business_rules(file_path)
    row_count = int(business_rules["row_count"])

    validation_result["row_count"] = row_count
    validation_result["business_rule_violations"] = business_rules

    has_minimum_rows = row_count >= min_rows
    has_no_null_location_id = business_rules["null_location_id"] == 0
    has_no_null_borough = business_rules["null_borough"] == 0
    has_no_null_zone_name = business_rules["null_zone_name"] == 0
    has_no_duplicate_location_id = business_rules["duplicate_location_id"] == 0

    if (
        has_minimum_rows
        and has_no_null_location_id
        and has_no_null_borough
        and has_no_null_zone_name
        and has_no_duplicate_location_id
    ):
        validation_result["status"] = "passed"

    print("\nResultado de validación de zonas:")
    print(f"- Archivo: {validation_result['file_path']}")
    print(f"  Estado: {validation_result['status']}")
    print(f"  Filas: {validation_result['row_count']}")
    print(f"  Reglas: {validation_result['business_rule_violations']}")

    if validation_result["status"] != "passed":
        raise ValueError("La validación de zonas falló.")

    return validation_result
