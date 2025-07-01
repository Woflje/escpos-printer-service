import socket
import threading
import json
import base64
import uuid
from datetime import datetime
from pathlib import Path
from PIL import Image
from io import BytesIO
from bin.load import CONFIG, load_named_api_keys
from emoji import demojize
from bin.db import (
    store_message,
    load_oldest_message,
    delete_message_by_id,
    load_all_messages,
    set_message_processing,
    get_message_processing,
)
from bin.message import Message
from bin.logger import logging
from prometheus_client import start_http_server, Gauge, Counter
from typing import Tuple, List, Optional

IMG_DATA_DIR = Path("data/img/tmp")
IMG_DATA_DIR.mkdir(parents=True, exist_ok=True)

PRINTER_UP = Gauge("printer_server_up", "1 = server main loop running")
PRINTER_ERRORS = Counter("printer_server_errors_total", "Total unhandled server errors")
PRINTER_QUEUE_SIZE = Gauge(
    "printer_server_queue_length", "Current number of unprocessed messages"
)

text_processors = [
    demojize,
]


def process_text(text: str) -> str:
    for processor in text_processors:
        text = processor(text)
    return text


def is_within_schedule() -> bool:
    schedule = CONFIG.get("printer", {}).get("schedule", {})
    if not schedule.get("enabled", False):
        return True

    try:
        start_str = schedule.get("start", "00:00")
        end_str = schedule.get("end", "23:59")

        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()
        now = datetime.now().time()

        if start_time <= end_time:
            return start_time <= now <= end_time
        else:
            return now >= start_time or now <= end_time
    except Exception as e:
        logging.getLogger(__name__).warning(f"Invalid schedule config: {e}")
        return True


def save_image_from_base64(image_b64: str, message_id: str) -> str:
    config = CONFIG["printer"]["image"]
    max_width = config["max_width"]

    image_data = base64.b64decode(image_b64)
    image = Image.open(BytesIO(image_data))

    image = image.convert("RGBA")
    background = Image.new("RGBA", image.size, "WHITE")
    background.alpha_composite(image)

    image = background.convert("RGB").rotate(config["rotate"], expand=True)
    if (
        config["rotate_to_fit"]
        and image.width > config["rotate_to_fit_threshold_factor"] * image.height
    ):
        image = image.rotate(90, expand=True)
    new_height = int(max_width * image.height / image.width)
    image = image.resize((max_width, new_height))
    image_path = IMG_DATA_DIR / f"{message_id}.jpg"
    image.save(image_path, "JPEG")
    return str(image_path)


def find_printkey(data: dict) -> Optional[Tuple[str, List[str]]]:
    api_key = data.get("api_key")
    for name, rec in load_named_api_keys().items():
        if rec["key"] == api_key:
            return name, rec.get("permissions", [])
    return None


def recv_one_line(sock, bufsize=4096, terminator=b"\n") -> bytes:
    chunks = []
    while True:
        chunk = sock.recv(bufsize)
        if not chunk:
            break
        chunks.append(chunk)
        if terminator in chunk:
            break
    return b"".join(chunks)


def summary() -> str:
    return json.dumps(
        {
            "name": CONFIG.get("printer", {}).get("name", "Unknown"),
            "charcode": CONFIG.get("printer", {}).get("charcode", "CP858"),
            "always_cut": CONFIG.get("printer", {}).get("always_cut", False),
            "allow_custom_template": CONFIG.get("printer", {})
            .get("text", {})
            .get("allow_custom_template", False),
            "text_limit": CONFIG.get("security", {}).get("text_limit", -1),
            "schedule": CONFIG.get("printer", {}).get("schedule", {}),
            "currently_processing": get_message_processing() and is_within_schedule(),
        },
        indent=2,
    )


def handle_client(conn, addr):
    log = logging.getLogger(__name__)
    log.info(f"Connection from {addr}")
    try:
        raw = recv_one_line(conn)
        message_data = json.loads(raw.decode("utf-8").rstrip())

        req_type = message_data.get("type", "message")
        printkey_name: Optional[str] = None
        permissions: List[str] = []

        if not CONFIG["security"].get("allow_unauthenticated", False):
            key_info = find_printkey(message_data)
            if key_info is None:
                log.info(f"{addr} was not authorized")
                conn.send(b"Unauthorized.\n")
                return
            printkey_name, permissions = key_info

        if req_type == "summary":
            conn.send(summary().encode() + b"\n")
            log.info(
                f"Sent summary to {addr} (key: {printkey_name or 'unauthenticated'})"
            )
            return

        if req_type == "control":
            if "control" not in permissions:
                conn.send(b"Forbidden.\n")
                log.info(f"{addr} tried control without permission")
                return

            raw_value = message_data.get("value")

            if isinstance(raw_value, dict):
                flag = raw_value.get("message_processing", None)
            else:
                flag = None

            if not isinstance(flag, bool):
                conn.send(b"Error: 'message_processing' must be true or false.\n")
                log.warning(
                    f"{addr} sent invalid control payload: {message_data.get('value')}"
                )
                return

            set_message_processing(flag)
            conn.send(b"Message processing updated.\n")
            log.info(f"Message processing set to {flag} by key {printkey_name}")
            return

        text = message_data.get("text")
        if text:
            limit = CONFIG["security"].get("text_limit", -1)
            if 0 < limit < len(text):
                raise ValueError(f"Text too long. Limit is {limit} characters.")
            message_data["text"] = process_text(text)

        image = message_data.get("image")

        if not image and not text:
            raise ValueError("Message must contain either text or an image.")

        message_data["dt_received"] = datetime.now().isoformat()
        message_id = str(uuid.uuid4())
        message_data["id"] = message_id

        if image:
            path = save_image_from_base64(message_data["image"], message_id)
            message_data["image_path"] = path
            message_data["image"] = None
        else:
            message_data["image_path"] = None

        store_message(message_data)
        conn.send(b"Message stored.\n")
        if printkey_name:
            log.info(f"Message from {addr} with printkey {printkey_name} stored")
        else:
            log.info(f"Message from {addr} stored")
    except ValueError as ve:
        log.warning(f"Client error from {addr}: {ve}")
        conn.send(f"Error: {ve}\n".encode())
    except Exception as e:
        log.error(f"Unhandled error from {addr}: {e}")
        PRINTER_ERRORS.inc()
        conn.send(b"Error: An unexpected server error occurred.\n")
    finally:
        conn.close()


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        config = CONFIG["server"]
        host = config.get("host", "0.0.0.0")
        port = config.get("port", 9000)
        s.bind((host,port))
        s.listen()
        logging.getLogger(__name__).info(f"Server listening on {host}:{port}")
        if CONFIG["server"].get("prometheus_enabled", False):
            start_http_server(CONFIG["server"].get("prometheus_port", 9100))
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
        logging.getLogger(__name__).info(
            f"Processed message: {message.id} from {message.sender}"
        )


def processing_loop(printer, template):
    log = logging.getLogger(__name__)
    log.info("Starting processing loop")
    while True:
        if get_message_processing() and is_within_schedule():
            process_next_message(printer, template)


def start_processing_loop(printer, template):
    t = threading.Thread(target=processing_loop, args=(printer, template), daemon=True)
    t.start()
