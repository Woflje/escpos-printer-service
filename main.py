import logging
import threading
from bin.load import CONFIG, load_template_by_name
import time
from bin.logger import setup_logging
from bin.printer.printer import Printer
from bin.server import start_processing_loop, start_server
import os

if __name__ == "__main__":
    setup_logging()
    logging.getLogger(__name__).info("Starting")

    printer = Printer(CONFIG["printer"])
    template = load_template_by_name(os.getenv("TEMPLATE_NAME", "debug"))

    host = os.environ.get("LISTEN_HOST", "127.0.0.1")
    port = int(os.environ.get("LISTEN_PORT", "9000"))

    start_processing_loop(printer, template)

    server_thread = threading.Thread(
        target=start_server, args=(host, port), daemon=True
    )
    server_thread.start()

    while True:
        time.sleep(1)
