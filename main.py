"""Punto de entrada principal del proyecto NYC Taxi Data Platform."""

from src.ingestion.download_taxi_data import download_taxi_data_from_config
from src.transformations.build_bronze import build_bronze_from_config
from src.utils.config_loader import load_config


def main() -> None:
    """Ejecuta el flujo inicial Raw -> Bronze."""
    print("NYC Taxi Data Platform")
    print("Iniciando pipeline Raw -> Bronze...")

    config = load_config()

    print("\nPaso 1: Ingesta Raw")
    raw_files = download_taxi_data_from_config(config)

    print("\nPaso 2: Construcción Bronze")
    bronze_files = build_bronze_from_config(config)

    print("\nPipeline finalizado correctamente.")
    print(f"Archivos Raw procesados: {len(raw_files)}")
    print(f"Archivos Bronze generados: {len(bronze_files)}")

    for file_path in bronze_files:
        print(f"- {file_path}")


if __name__ == "__main__":
    main()
