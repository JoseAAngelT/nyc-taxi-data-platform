"""Descarga controlada de la tabla auxiliar Taxi Zone Lookup."""

from __future__ import annotations

from pathlib import Path

import requests


def download_file(url: str, output_path: Path) -> None:
    """Descarga un archivo desde una URL y lo guarda localmente."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    with output_path.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)


def download_zone_lookup_file(
    raw_path: str,
    url: str,
    file_name: str,
    overwrite: bool = False,
) -> Path:
    """Descarga la tabla Taxi Zone Lookup en la capa Raw."""
    output_path = Path(raw_path) / file_name

    if output_path.exists() and not overwrite:
        print(f"Tabla de zonas ya existente, se omite descarga: {output_path}")
        return output_path

    print(f"Descargando tabla de zonas: {url}")
    download_file(url=url, output_path=output_path)
    print(f"Tabla de zonas guardada en: {output_path}")

    return output_path


def download_zone_lookup_from_config(config: dict) -> Path:
    """Descarga la tabla de zonas usando la configuración del proyecto."""
    raw_path = config["paths"]["raw"]
    zone_config = config["zone_lookup"]

    return download_zone_lookup_file(
        raw_path=raw_path,
        url=zone_config["url"],
        file_name=zone_config["file_name"],
        overwrite=False,
    )
