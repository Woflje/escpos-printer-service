import socket
import json
import base64
from pathlib import Path

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9000
BUF_SIZE     = 4096

def _read_until_newline(sock: socket.socket, bufsize=BUF_SIZE) -> bytes:
    """Read from *sock* until we find a lone newline byte or the peer closes."""
    chunks = []
    while True:
        chunk = sock.recv(bufsize)
        if not chunk:
            break
        chunks.append(chunk)
        if b'\n' in chunk:
            break
    return b''.join(chunks)

def send_message(api_key=None,
                 sender="Tester",
                 text="Hello from client!",
                 image_path=None):
    message = {
        "sender": sender,
        "text":   text,
        "cut":    True,
        "custom_template": "{image}\n{text}"
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

send_message(text="<center>Whowh</center>", image_path="olbrecht.png")
