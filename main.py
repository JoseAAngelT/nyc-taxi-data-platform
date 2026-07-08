"""Punto de entrada principal del proyecto NYC Taxi Data Platform."""

from src.ingestion.download_taxi_data import download_taxi_data_from_config
from src.utils.config_loader import load_config


def main() -> None:
    """Ejecuta la ingesta Raw del proyecto."""
    print("NYC Taxi Data Platform")
    print("Iniciando descarga controlada de datos Raw...")

    config = load_config()
    downloaded_files = download_taxi_data_from_config(config)

    print("Descarga finalizada.")
    print(f"Archivos procesados: {len(downloaded_files)}")

    for file_path in downloaded_files:
        print(f"- {file_path}")


if __name__ == "__main__":
    main()
