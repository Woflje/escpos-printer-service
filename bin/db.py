from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from tinydb_serialization import SerializationMiddleware  # type: ignore
from tinydb_serialization.serializers import DateTimeSerializer  # type: ignore
from pathlib import Path
from contextlib import contextmanager
from typing import Any, List, Optional, cast
from bin.message import Message, MessageRecord
import os

DB_PATH = Path("data/db.json")
DB_LOCK = Path("data/db.lock")

serialization = SerializationMiddleware(CachingMiddleware(JSONStorage))  # type: ignore
serialization.register_serializer(DateTimeSerializer(), "TinyDate")


@contextmanager
def get_db():
    with open(DB_LOCK, "w"):
        db = TinyDB(DB_PATH, storage=serialization)
        try:
            yield db
        finally:
            db.close()


def store_message(raw: dict[str, Any]) -> str:
    msg = Message.from_dict(raw)
    with get_db() as db:
        db.insert(msg.to_record())  # type: ignore[arg-type]
    return msg.id


def load_message_by_id(message_id: str) -> Optional[Message]:
    with get_db() as db:
        record: Optional[MessageRecord] = db.get(Query().id == message_id)  # type: ignore[assignment]
        return Message.from_dict(record) if record else None


def load_all_messages():
    with get_db() as db:
        return db.all()


def drop_all_messages():
    with get_db() as db:
        db.truncate()


def delete_message_by_id(message_id: str) -> None:
    with get_db() as db:
        rec: Optional[MessageRecord] = cast(
            Optional[MessageRecord], db.get(Query().id == message_id)
        )

        image_path = rec.get("image_path") if rec else None  # type: ignore[attr-defined]

        if image_path:
            try:
                os.remove(image_path)
            except FileNotFoundError:
                pass
            except Exception as exc:
                print(f"Warning: could not delete image {image_path}: {exc}")

        db.remove(Query().id == message_id)


def load_oldest_message() -> Optional[MessageRecord]:
    with get_db() as db:
        msgs: List[MessageRecord] = db.all()  # type: ignore
        if not msgs:
            return None

        with_dt = [m for m in msgs if m.get("dt_received") is not None]
        without_dt = [m for m in msgs if m.get("dt_received") is None]

        if with_dt:
            return sorted(
                with_dt,
                key=lambda m: m.get("dt_received") or "",
            )[0]
        return sorted(without_dt, key=lambda m: str(m.get("id", "")))[0]
