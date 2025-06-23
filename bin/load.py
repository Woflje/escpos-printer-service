import yaml
from pathlib import Path
from typing import Any

def load_yaml(path: str | Path) -> dict[str, Any]:
    """
    Load a YAML file and return its contents as a dictionary.
    
    Args:
        path (str | Path): Path to the YAML file.
    
    Returns:
        dict[str, Any]: Parsed YAML content.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the YAML is invalid.
    """
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file {path}: {e}")

CONFIG = load_yaml("config/config.yaml")