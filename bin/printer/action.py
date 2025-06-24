from typing import Callable, Any
from bin.logger import logging

class PrinterAction:
    def __init__(self, desc: str, func: Callable[..., Any], *args, **kw) -> None:
        self.desc, self.func, self.args, self.kw = desc, func, args, kw

    def run(self) -> None:
        try:
            logging.getLogger(__name__).info(f"[ESC/POS] {self.desc} started")
            self.func(*self.args, **self.kw)
        except Exception as e:
            logging.getLogger(__name__).error(f"[ESC/POS] {self.desc} failed: {e}")
            raise