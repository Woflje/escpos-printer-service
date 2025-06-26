import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Callable, List

LOG_DIR = Path("data/logs")
LATEST_LOG = LOG_DIR / "latest.log"

error_hooks: List[Callable[[str], None]] = []

def register_error_hook(func: Callable[[str], None]):
	error_hooks.append(func)

class HookingHandler(logging.Handler):
	def emit(self, record: logging.LogRecord):
		if record.levelno >= logging.ERROR:
			message = self.format(record)
			for hook in error_hooks:
				try:
					hook(message)
				except Exception as e:
					logging.getLogger(__name__).exception("Error in error hook: %s", e)

def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)

    log_date_format = os.environ.get("DATETIME_FORMAT","%Y-%m-%d %H:%M:%S")

    if LATEST_LOG.exists():
        # Rotate log file
        timestamp = datetime.now().strftime(log_date_format)
        backup_log = LOG_DIR / f"{timestamp}.log"
        try:
            LATEST_LOG.rename(backup_log)
        except Exception as e:
            print(f"Failed to rotate log: {e}")

    log_level = os.environ.get("LOG_LEVEL", "DEBUG").upper()
    level = getattr(logging, log_level, logging.DEBUG)

    log_format = "[{asctime}] [{levelname:^7}] [{name}] {message}"
    style = "{"

    formatter_console = logging.Formatter(fmt=log_format, datefmt=log_date_format, style=style)
    formatter_file = logging.Formatter(fmt=log_format, datefmt=log_date_format, style=style)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter_console)

    file_handler = RotatingFileHandler(
        filename=LATEST_LOG,
        mode='a',
        maxBytes=1_000_000,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter_file)

    hook_handler = HookingHandler()
    hook_handler.setFormatter(formatter_file)

    logging.basicConfig(
        level=level,
        handlers=[console_handler, file_handler, hook_handler]
    )

    logging.getLogger(__name__).info(f"Logging initialized at level {log_level}")
