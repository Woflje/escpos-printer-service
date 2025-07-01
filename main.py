import logging
import threading
from bin.load import CONFIG, load_template_by_name
import time
from bin.logger import setup_logging
from bin.printer.printer import Printer
from bin.server import start_processing_loop, start_server

if __name__ == "__main__":
    setup_logging()
    logging.getLogger(__name__).info("Starting")

    printer = Printer(CONFIG["printer"])
    template = load_template_by_name(CONFIG["printer"].get("template_name","debug"))

    start_processing_loop(printer, template)

    server_thread = threading.Thread(
        target=start_server, daemon=True
    )
    server_thread.start()

    while True:
        time.sleep(1)
