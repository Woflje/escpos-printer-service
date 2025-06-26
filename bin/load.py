import yaml
from pathlib import Path
from typing import Any, Dict, List
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


def load_named_api_keys(folder: str = "data/printkeys") -> Dict[str, dict]:
    """
    Returns {key_name: {"key": api_key, "permissions": [str, ...]}, ...}

    Each .txt file:
        line 1 → the key
        line 2 → optional comma-separated list of permissions
    """
    result: Dict[str, dict] = {}
    for f in Path(folder).glob("*.txt"):
        lines: List[str] = f.read_text(encoding="utf-8").splitlines()
        if not lines:
            continue
        api_key = lines[0].strip()
        perms   = [p.strip() for p in lines[1].split(",")] if len(lines) > 1 else []
        result[f.stem] = {"key": api_key, "permissions": perms}
    return result


def load_template_by_name(name: str):
    try:
        mod = importlib.import_module(f"config.template.{name}")
        return getattr(mod, "template", None)
    except Exception as e:
        print(f"Error loading template '{name}': {e}")
        return None


CONFIG = load_yaml(CONFIG_PATH)
