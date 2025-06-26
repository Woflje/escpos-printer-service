from typing import Any

STYLE_KEYS: tuple[str, ...] = (
    "align",
    "font",
    "bold",
    "underline",
    "custom_size",
    "width",
    "height",
    "density",
    "invert",
    "smooth",
    "flip",
)

DEFAULT_STYLE: dict[str, Any] = {
    "align": "left",
    "font": "a",
    "bold": False,
    "underline": 0,
    "custom_size": True,
    "width": 1,
    "height": 1,
    "density": 9,
    "invert": False,
    "smooth": False,
    "flip": False,
}
