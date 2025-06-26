from __future__ import annotations

import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Mapping, Optional, TypedDict


def dt_to_iso(value: Optional[datetime]) -> Optional[str]:
    return value.isoformat() if value else None


class MessageRecord(TypedDict, total=False):
    id: str
    text: str
    dt_sent: str
    dt_received: str
    dt_printed: str
    image_path: str
    sender: str
    cut: bool
    custom_template: str


@dataclass(slots=True)
class Message:
    id: str
    text: str = ""
    dt_sent: Optional[datetime] = None
    dt_received: Optional[datetime] = None
    dt_printed: Optional[datetime] = None
    image_path: Optional[str] = None
    sender: Optional[str] = None
    cut: bool = True
    custom_template: Optional[str] = None

    def to_record(self) -> dict[str, Any]:
        raw: dict[str, Any] = asdict(self)
        for key in ("dt_sent", "dt_received", "dt_printed"):
            raw[key] = dt_to_iso(raw[key])  # type: ignore[index]

        return {k: v for k, v in raw.items() if v is not None}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> "Message":
        if data is None:
            raise ValueError("Cannot build Message from None")

        def _parse_dt(raw: Any) -> Optional[datetime]:
            if isinstance(raw, datetime):
                return raw
            if isinstance(raw, str) and raw:
                try:
                    return datetime.fromisoformat(raw)
                except ValueError:
                    pass
            return None

        return cls(
            id=str(data.get("id") or uuid.uuid4()),
            text=str(data.get("text", "")),
            dt_sent=_parse_dt(data.get("dt_sent")),
            dt_received=_parse_dt(data.get("dt_received")),
            dt_printed=_parse_dt(data.get("dt_printed")),
            image_path=data.get("image_path") or None,
            sender=data.get("sender") or None,
            cut=bool(data.get("cut", True)),
            custom_template=data.get("custom_template") or None,
        )
