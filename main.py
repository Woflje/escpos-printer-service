from dotenv import load_dotenv
import logging
from bin.logger import setup_logging

load_dotenv()

if __name__ == "__main__":
	setup_logging()
	logging.getLogger(__name__).info("Starting")