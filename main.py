from dotenv import load_dotenv
import logging
import threading
import time
from bin.logger import setup_logging
from bin.load import CONFIG
from bin.printer.printer import Printer
from config.template.debug import template
from bin.server import start_processing_loop, start_server

load_dotenv()

if __name__ == "__main__":
	setup_logging()
	logging.getLogger(__name__).info("Starting")

	printer = Printer("WofljeFox", CONFIG["printer"]["port"], CONFIG["printer"]["baud"])
	start_processing_loop(printer, template)

	server_thread = threading.Thread(target=start_server, daemon=True)
	server_thread.start()

	while True:
		time.sleep(1)
