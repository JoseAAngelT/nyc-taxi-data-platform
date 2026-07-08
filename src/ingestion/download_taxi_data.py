"""Descarga controlada de archivos Parquet del dataset NYC Taxi."""

from __future__ import annotations

from pathlib import Path

import requests

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"


def build_taxi_file_url(year: int, month: int, taxi_type: str = "yellow") -> str:
    """Construye la URL del archivo Parquet mensual de NYC Taxi."""
    month_str = f"{month:02d}"
    return f"{BASE_URL}/{taxi_type}_tripdata_{year}-{month_str}.parquet"


def build_taxi_file_name(year: int, month: int, taxi_type: str = "yellow") -> str:
    """Construye el nombre local del archivo Parquet mensual."""
    month_str = f"{month:02d}"
    return f"{taxi_type}_tripdata_{year}-{month_str}.parquet"


def download_file(url: str, output_path: Path) -> None:
    """Descarga un archivo desde una URL y lo guarda localmente."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    with output_path.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)


def download_monthly_taxi_file(
    year: int,
    month: int,
    taxi_type: str,
    raw_path: str,
    overwrite: bool = False,
) -> Path:
    """Descarga un archivo mensual de NYC Taxi en la capa Raw."""
    file_url = build_taxi_file_url(year=year, month=month, taxi_type=taxi_type)
    file_name = build_taxi_file_name(year=year, month=month, taxi_type=taxi_type)
    output_path = Path(raw_path) / file_name

    if output_path.exists() and not overwrite:
        print(f"Archivo ya existente, se omite descarga: {output_path}")
        return output_path

    print(f"Descargando archivo: {file_url}")
    download_file(url=file_url, output_path=output_path)
    print(f"Archivo guardado en: {output_path}")

    return output_path


def download_taxi_data_from_config(config: dict) -> list[Path]:
    """Descarga los archivos definidos en la configuración del proyecto."""
    source_config = config["source"]
    raw_path = config["paths"]["raw"]

    taxi_type = source_config["taxi_type"]
    year = source_config["start_year"]
    start_month = source_config["start_month"]
    end_month = source_config["end_month"]

    downloaded_files = []

    for month in range(start_month, end_month + 1):
        file_path = download_monthly_taxi_file(
            year=year,
            month=month,
            taxi_type=taxi_type,
            raw_path=raw_path,
            overwrite=False,
        )
        downloaded_files.append(file_path)

    return downloaded_files
