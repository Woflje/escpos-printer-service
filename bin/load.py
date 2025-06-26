import yaml
from pathlib import Path
from typing import Any
from .logger import logging
import importlib

CONFIG_PATH = "config/config.yaml"
PRINTKEYS_PATH = "data/printkeys"

def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file {path}: {e}")
        
def load_named_api_keys(folder: str = "data/printkeys") -> dict[str, str]:
    key_dir = Path(folder)
    keys: dict[str, str] = {}
    for file in key_dir.glob("*.txt"):
        try:
            content = file.read_text(encoding="utf-8").strip()
            if content:
                keys[file.stem] = content
        except Exception as e:
            logging.getLogger(__name__).warning(f"could not read {file.name}: {e}")
    return keys

def load_template_by_name(name: str):
    try:
        mod = importlib.import_module(f"config.template.{name}")
        return getattr(mod, "template", None)
    except Exception as e:
        print(f"Error loading template '{name}': {e}")
        return None

CONFIG = load_yaml(CONFIG_PATH)