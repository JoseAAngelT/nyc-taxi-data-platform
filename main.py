"""Punto de entrada principal del proyecto NYC Taxi Data Platform."""

from src.ingestion.download_taxi_data import download_taxi_data_from_config
from src.quality.validate_bronze import validate_bronze_from_config
from src.quality.validate_silver import validate_silver_from_config
from src.transformations.build_bronze import build_bronze_from_config
from src.transformations.build_silver import build_silver_from_config
from src.utils.config_loader import load_config


def main() -> None:
    """Ejecuta el flujo Raw -> Bronze -> Silver."""
    print("NYC Taxi Data Platform")
    print("Iniciando pipeline Raw -> Bronze -> Silver...")

    config = load_config()

    print("\nPaso 1: Ingesta Raw")
    raw_files = download_taxi_data_from_config(config)

    print("\nPaso 2: Construcción Bronze")
    bronze_files = build_bronze_from_config(config)

    print("\nPaso 3: Validación Bronze")
    bronze_validation_results = validate_bronze_from_config(config)

    print("\nPaso 4: Construcción Silver")
    silver_files = build_silver_from_config(config)

    print("\nPaso 5: Validación Silver")
    silver_validation_results = validate_silver_from_config(config)

    print("\nPipeline finalizado correctamente.")
    print(f"Archivos Raw procesados: {len(raw_files)}")
    print(f"Archivos Bronze generados: {len(bronze_files)}")
    print(f"Validaciones Bronze ejecutadas: {len(bronze_validation_results)}")
    print(f"Archivos Silver generados: {len(silver_files)}")
    print(f"Validaciones Silver ejecutadas: {len(silver_validation_results)}")


if __name__ == "__main__":
    main()
