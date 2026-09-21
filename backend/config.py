"""Carga la configuración compartida por simulador y backend."""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "simulator" / "config.json"


def load_project_config(path=CONFIG_PATH):
    with open(path, encoding="utf-8") as config_file:
        return json.load(config_file)

