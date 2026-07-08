"""Punto de entrada principal del proyecto NYC Taxi Data Platform."""

from src.ingestion.download_taxi_data import download_taxi_data_from_config
from src.ingestion.download_zone_lookup import download_zone_lookup_from_config
from src.quality.validate_bronze import validate_bronze_from_config
from src.quality.validate_silver import validate_silver_from_config
from src.quality.validate_zones import validate_zones_from_config
from src.transformations.build_bronze import build_bronze_from_config
from src.transformations.build_silver import build_silver_from_config
from src.transformations.build_silver_zones import build_silver_zones_from_config
from src.utils.config_loader import load_config


def main() -> None:
    """Ejecuta el flujo Raw -> Bronze -> Silver."""
    print("NYC Taxi Data Platform")
    print("Iniciando pipeline Raw -> Bronze -> Silver...")

    config = load_config()

    print("\nPaso 1: Ingesta Raw de viajes")
    raw_files = download_taxi_data_from_config(config)

    print("\nPaso 2: Ingesta Raw de zonas")
    zone_lookup_file = download_zone_lookup_from_config(config)

    print("\nPaso 3: Construcción Bronze de viajes")
    bronze_files = build_bronze_from_config(config)

    print("\nPaso 4: Validación Bronze")
    bronze_validation_results = validate_bronze_from_config(config)

    print("\nPaso 5: Construcción Silver de viajes")
    silver_files = build_silver_from_config(config)

    print("\nPaso 6: Construcción Silver de zonas")
    silver_zones_file = build_silver_zones_from_config(config)

    print("\nPaso 7: Validación Silver de viajes")
    silver_validation_results = validate_silver_from_config(config)

    print("\nPaso 8: Validación Silver de zonas")
    zone_validation_result = validate_zones_from_config(config)

    print("\nPipeline finalizado correctamente.")
    print(f"Archivos Raw de viajes procesados: {len(raw_files)}")
    print(f"Archivo Raw de zonas procesado: {zone_lookup_file}")
    print(f"Archivos Bronze generados: {len(bronze_files)}")
    print(f"Validaciones Bronze ejecutadas: {len(bronze_validation_results)}")
    print(f"Archivos Silver de viajes generados: {len(silver_files)}")
    print(f"Archivo Silver de zonas generado: {silver_zones_file}")
    print(f"Validaciones Silver de viajes ejecutadas: {len(silver_validation_results)}")
    print(f"Validación de zonas: {zone_validation_result['status']}")


if __name__ == "__main__":
    main()
