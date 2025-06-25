import socket
import threading
import json
import base64
import uuid
from datetime import datetime
from pathlib import Path
from PIL import Image
from io import BytesIO
from bin.load import CONFIG
from emoji import demojize
import time
from bin.db import store_message, load_oldest_message, delete_message_by_id, load_all_messages
from bin.message import Message
from bin.logger import logging
from prometheus_client import start_http_server, Gauge, Counter

DATA_DIR = Path("data/img/tmp")
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRINTER_UP = Gauge('printer_server_up', '1 = server main loop running')
PRINTER_ERRORS = Counter('printer_server_errors_total', 'Total unhandled server errors')
PRINTER_QUEUE_SIZE = Gauge('printer_server_queue_length', 'Current number of unprocessed messages')

text_processors = [
	demojize,
]

def process_text(text: str) -> str:
	for processor in text_processors:
		text = processor(text)
	return text

def save_image_from_base64(image_b64: str, message_id: str) -> str:
	config = CONFIG["printer"]["image"]
	max_width = config["max_width"]

	image_data = base64.b64decode(image_b64)
	image = Image.open(BytesIO(image_data))

	image = image.convert("RGBA")
	background = Image.new("RGBA", image.size, "WHITE")
	background.alpha_composite(image)

	image = background.convert("RGB").rotate(config["rotate"], expand=True)
	if config["rotate_to_fit"] and image.width > config["rotate_to_fit_threshold_factor"] * image.height:
		image = image.rotate(90, expand=True)
	new_height = int(max_width * image.height / image.width)
	image = image.resize((max_width, new_height))
	image_path = DATA_DIR / f"{message_id}.jpg"
	image.save(image_path, "JPEG")
	return str(image_path)

def is_authenticated(data: dict) -> bool:
	if CONFIG["security"].get("allow_unauthenticated"):
		return True
	return data.get("api_key") in CONFIG["security"].get("valid_api_keys", [])

def recv_one_line(sock, bufsize=4096, terminator=b"\n") -> bytes:
	"""Return one \n-terminated line from *sock* (blocking)."""
	chunks = []
	while True:
		chunk = sock.recv(bufsize)
		if not chunk:
			break
		chunks.append(chunk)
		if terminator in chunk:
			break
	return b"".join(chunks)


def handle_client(conn, addr):
	logging.getLogger(__name__).info(f"Connection from {addr}")
	try:
		raw = recv_one_line(conn)
		message_data = json.loads(raw.decode("utf-8").rstrip())

		if not is_authenticated(message_data):
			logging.getLogger(__name__).info(f"{addr} was not authorized")
			conn.send(b"Unauthorized.\n")
			return

		message_data["dt_received"] = datetime.now().isoformat()
		message_id = str(uuid.uuid4())
		message_data["id"] = message_id

		if message_data.get("image"):
			path = save_image_from_base64(message_data["image"], message_id)
			message_data["image_path"] = path
			message_data["image"] = None

		store_message(message_data)
		conn.send(b"Message stored.\n")
		logging.getLogger(__name__).info(f"Message from {addr} stored")
	except Exception as e:
		logging.getLogger(__name__).error(e)
		PRINTER_ERRORS.inc()
		conn.send(f"Error: {e}\n".encode())
	finally:
		conn.close()

def start_server(host="127.0.0.1", port=9000):
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.bind((host, port))
		s.listen()
		logging.getLogger(__name__).info(f"Server listening on {host}:{port}")
		start_http_server(9100)
		PRINTER_UP.set(1)
		while True:
			conn, addr = s.accept()
			thread = threading.Thread(target=handle_client, args=(conn, addr))
			thread.start()

def process_next_message(printer, template):
	record = load_oldest_message()
	PRINTER_QUEUE_SIZE.set(len(load_all_messages()))
	if record:
		message = Message.from_dict(record)
		printer.print_message(message, template)
		delete_message_by_id(message.id)
		logging.getLogger(__name__).info(f"Processed message: {message.id} from {message.sender}")
	

def processing_loop(printer, template, delay_seconds=2.5):
	logging.getLogger(__name__).info("Starting processing")
	while True:
		process_next_message(printer, template)
		time.sleep(delay_seconds)

def start_processing_loop(printer, template):
	t = threading.Thread(target=processing_loop, args=(printer, template), daemon=True)
	t.start()