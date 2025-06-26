import socket
import json
import base64
from pathlib import Path
import os

SERVER_HOST = os.environ.get("LISTEN_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("LISTEN_PORT", "9000"))
BUF_SIZE     = 4096

def _read_until_newline(sock: socket.socket, bufsize=BUF_SIZE) -> bytes:
    chunks = []
    while True:
        chunk = sock.recv(bufsize)
        if not chunk:
            break
        chunks.append(chunk)
        if b'\n' in chunk:
            break
    return b''.join(chunks)

def send_message(sender,
                 text,
                 image_path=None,
                 api_key=None):
    message = {
        "sender": sender,
        "text": text,
    }
    if api_key:
        message["api_key"] = api_key

    if image_path:
        message["image"] = base64.b64encode(
            Path(image_path).read_bytes()
        ).decode()

    wire = json.dumps(message, separators=(",", ":")).encode() + b"\n"

    with socket.create_connection((SERVER_HOST, SERVER_PORT)) as sock:
        sock.sendall(wire)
        raw = _read_until_newline(sock)
        reply = raw.strip().decode()
        print(f"[Server response] {reply}")

send_message("Client", "<center>\\<b\\>Hello from client!\\</b\\></center>")