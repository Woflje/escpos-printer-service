from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from tinydb_serialization import SerializationMiddleware
from tinydb_serialization.serializers import DateTimeSerializer
from pathlib import Path
from contextlib import contextmanager
import uuid
from bin.message import Message
import os

DB_PATH = Path("data/db.json")
DB_LOCK = Path("data/db.lock")

serialization = SerializationMiddleware(CachingMiddleware(JSONStorage))
serialization.register_serializer(DateTimeSerializer(), 'TinyDate')

@contextmanager
def get_db():
    with open(DB_LOCK, 'w'):
        db = TinyDB(DB_PATH, storage=serialization)
        try:
            yield db
        finally:
            db.close()

def store_message(message_data: dict) -> str:
    message_id = message_data.get("id") or str(uuid.uuid4())
    message_data["id"] = message_id
    with get_db() as db:
        db.insert(message_data)
    return message_id

def load_message_by_id(message_id: str) -> Message | None:
    with get_db() as db:
        data = db.get(Query().id == message_id)
        if data:
            return Message.from_dict(data)
        return None

def load_all_messages():
    with get_db() as db:
        return db.all()

def drop_all_messages():
    with get_db() as db:
        db.truncate()

def delete_message_by_id(message_id: str):
    with get_db() as db:
        # Attempt to remove the image file if it exists
        data = db.get(Query().id == message_id)
        if data and "image_path" in data and data["image_path"]:
            try:
                os.remove(data["image_path"])
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"Warning: Could not delete image file {data['image_path']}: {e}")
        db.remove(Query().id == message_id)

def load_oldest_message():
    """Get the oldest message by dt_received, fallback to lowest ID if unavailable."""
    with get_db() as db:
        messages = db.all()
        if not messages:
            return None

        with_dt = [m for m in messages if m.get("dt_received")]
        without_dt = [m for m in messages if not m.get("dt_received")]

        if with_dt:
            return sorted(with_dt, key=lambda x: x["dt_received"])[0]
        else:
            return sorted(without_dt, key=lambda x: x.get("id", ""))[0]
