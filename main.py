from dotenv import load_dotenv
import logging
from bin.logger import setup_logging
from bin.load import CONFIG
from bin.printer import Printer
from bin.message import Message
from datetime import datetime
from config.template.debug import template

load_dotenv()

if __name__ == "__main__":
	setup_logging()
	logging.getLogger(__name__).info("Starting")

m = Message(
    text="https://5etools.woflje.com",
    sender="System",
	has_tokens=True,
	cut=True
)

m.dt_sent = datetime(2025, 6, 1, 14, 30)
m.dt_received = datetime.now()

printer = Printer("WofljeFox", CONFIG["printer"]["port"], CONFIG["printer"]["baud"])
printer.print_message(m, template)