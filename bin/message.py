from datetime import datetime


class Message:
    def __init__(
        self,
        text: str,
        dt_sent: datetime | None = None,
        image: str | None = None,
        sender: str | None = None,
        cut: bool = False,
        has_tokens: bool = False,
    ):
        self.text = text
        self.dt_sent = datetime or "Unknown"
        self.dt_received: datetime or "Unknown"
        self.dt_printed: datetime or "Unknown"
        self.image = image
        self.sender = sender or "Unknown"
        self.cut = cut
        self.has_tokens = has_tokens
