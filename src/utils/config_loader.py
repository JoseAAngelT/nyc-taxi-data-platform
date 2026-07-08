"""Utilidades para cargar la configuración del proyecto."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str = "config/config.yaml") -> dict[str, Any]:
    """Carga el archivo de configuración YAML del proyecto."""
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {path}")

    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return config
