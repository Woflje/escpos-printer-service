from datetime import datetime

class Message:
    def __init__(
        self,
        text: str,
        dt_sent: datetime | None = None,
        dt_received: datetime | None = None,
        dt_printed: datetime | None = None,
        image: str | None = None,
        sender: str | None = None,
        cut: bool = False,
        custom_template: str | None = None,
        id: str | None = None,
    ):
        self.text = text
        self.dt_sent = dt_sent or None
        self.dt_received = dt_received or datetime.now()
        self.dt_printed = dt_printed or datetime.now()
        self.image = image
        self.sender = sender or "Unknown"
        self.cut = cut
        self.custom_template = custom_template
        self.id = id

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            text=data.get("text", ""),
            dt_sent=_try_parse_dt(data.get("dt_sent")),
            dt_received=_try_parse_dt(data.get("dt_received")),
            dt_printed=_try_parse_dt(data.get("dt_printed")),
            image=data.get("image_path"),
            sender=data.get("sender"),
            cut=data.get("cut", False),
            custom_template=data.get("custom_template"),
            id=data.get("id"),
        )

def _try_parse_dt(value):
    try:
        if isinstance(value, datetime):
            return value
        if value:
            return datetime.fromisoformat(value)
    except Exception:
        pass
    return None