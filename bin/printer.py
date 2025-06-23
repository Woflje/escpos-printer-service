
import logging
from escpos.printer import Serial # type: ignore
from datetime import datetime
from time import sleep
from typing import Callable, Any, List, Type
from bin.load import CONFIG
from bin.message import Message
import re

STYLE_KEYS: tuple[str, ...] = (
    "align", "font", "bold", "underline", "custom_size",
    "width", "height", "density", "invert", "smooth", "flip",
)

DEFAULT_STYLE: dict[str, Any] = {
    "align":       "left",
    "font":        "a",
    "bold":        False,
    "underline":   0,
    "custom_size": True,
    "width":       1,
    "height":      1,
    "density":     9,
    "invert":      False,
    "smooth":      False,
    "flip":        False,
}

def merged_style(base: dict[str, Any], **overrides) -> dict[str, Any]:
    st = {k: base[k] for k in STYLE_KEYS}
    st.update({k: v for k, v in overrides.items() if v is not None})
    return st

def encode_cp858(text: str) -> bytes:
	return text.encode('cp858', errors='replace')


class PrinterAction:
    def __init__(self, desc: str, func: Callable[..., Any], *args, **kw) -> None:
        self.desc, self.func, self.args, self.kw = desc, func, args, kw

    def run(self) -> None:
        try:
            logging.getLogger(__name__).info(f"[ESC/POS] {self.desc} started")
            self.func(*self.args, **self.kw)
        except Exception as e:
            logging.getLogger(__name__).error(f"[ESC/POS] {self.desc} failed: {e}")
            raise


class Token:
    tag: str = ""
    registry: dict[str, "type[Token]"] = {}

    def __init_subclass__(cls) -> None:
        if cls.tag:
            Token.registry[cls.tag] = cls

    def __init__(self, children: list["Token"] | None = None):
        self.children = children or []

    def render(self, p: "Printer", m: Message) -> List[PrinterAction]:
        raise NotImplementedError


class TextToken(Token):
    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def render(self, p: "Printer", m: "Message") -> list[PrinterAction]:
        return [PrinterAction("text", p.print_text, self.text)]


class StyledToken(Token):
    align       : str  | None = None
    font        : str  | None = None
    bold        : bool | None = None
    underline   : int  | None = None
    custom_size : bool | None = None
    width       : int  | None = None
    height      : int  | None = None
    density     : int  | None = None
    invert      : bool | None = None
    smooth      : bool | None = None
    flip        : bool | None = None

    def _local_overrides(self) -> dict[str, Any]:
        return {
            k: getattr(self, k)
            for k in STYLE_KEYS
            if getattr(self, k) is not None
        }

    def render_ctx(
        self,
        p: "Printer",
        m: "Message",
        cur_style: dict[str, Any],
    ) -> tuple[list[PrinterAction], dict[str, Any]]:
        """
        Return (actions, resulting_style).  Uses cur_style as the baseline,
        applies overrides, renders children, then resets to cur_style.
        """
        overrides   = self._local_overrides()
        new_style   = merged_style(cur_style, **overrides)
        actions: list[PrinterAction] = [
            PrinterAction(f"set {self.__class__.__name__}", p.printer.set, **new_style)
        ]

        for child in self.children:
            if isinstance(child, StyledToken):
                child_actions, _ = child.render_ctx(p, m, new_style)
                actions.extend(child_actions)
            else:
                actions.extend(child.render(p, m))
                
        if "align" in overrides:
            actions.append(PrinterAction("newline", p.print_text, "\n"))
        actions.append(
            PrinterAction(f"reset {self.__class__.__name__}", p.printer.set, **cur_style)
        )
        return actions, cur_style

    def render(self, p: "Printer", m: "Message") -> list[PrinterAction]:
        actions, _ = self.render_ctx(p, m, DEFAULT_STYLE)
        return actions


class H1Token(StyledToken):  tag, width, height = "<h1>", 3, 3
class H2Token(StyledToken):  tag, width, height = "<h2>", 2, 2
class CenterToken(StyledToken): tag, align = "<center>", "center"
class RightToken(StyledToken):  tag, align = "<right>", "right"
class BoldToken(StyledToken):  tag, bold = "<b>",  True
class U1Token(StyledToken):  tag, underline = "<u1>",  1
class U2Token(StyledToken):  tag, underline = "<u2>",  2
class InvertToken(StyledToken):  tag, invert = "<invert>",  True
class FlipToken(StyledToken):  tag, flip = "<flip>",  True
class CodeToken(StyledToken):  tag, font = "<code>",  "b"


def parse_tokens(src: str) -> list[Token]:
    """
    Builds a proper tree so inner tags get rendered too.
    Supports <tag>, </tag>, <tag/> self-close.
    """
    parts = re.split(r"(<[^>]+>)", src)
    root: list[Token] = []
    stack: list[Token] = []

    def current_container() -> list[Token]:
        return stack[-1].children if stack else root

    for part in parts:
        if not part:
            continue

        if part.startswith("<") and part.endswith(">"):
            tag_txt = part.strip()
            closing = tag_txt.startswith("</")
            self_closing = tag_txt.endswith("/>")
            tag_name = tag_txt.strip("</> ").split()[0].lower()
            key = f"<{tag_name}>"

            if closing:
                while stack and stack[-1].__class__.tag != key:
                    stack.pop()
                if stack:
                    stack.pop()
            else:
                cls = Token.registry.get(key)
                if not cls:
                    continue
                tok = cls()
                current_container().append(tok)
                if not self_closing:
                    stack.append(tok)
        else:
            current_container().append(TextToken(part))
    return root


class Printer:
    def __init__(self, name: str, port: str, baud: int) -> None:
        self.name, self.port, self.baud = name, port, baud
        self.config = CONFIG["printer"]
        self.connect()
        self.printer.charcode("CP858")
        self.default_settings().run()

    def connect(self) -> None:
        try:
            self.printer = Serial(
                devfile=self.port,
                baudrate=self.baud,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1.00,
                dsrdtr=False,
                profile="TM-T88III"
            )
        except Exception as e:
            raise RuntimeError(f"Printer '{self.name}' connection failed: {e}")
    
    def print_text(self, text: str):
        self.printer._raw(encode_cp858(text)) # type: ignore

    def print_image(self, image_path: str):
        self.printer.image(image_path) # type: ignore
    
    def print_qr(self, url: str):
        self.printer.qr(url) # type: ignore

    def cut(self):
        self.printer.cut()

    def default_settings(self) -> PrinterAction:
        return PrinterAction("defaults", self.printer.set, **DEFAULT_STYLE)


    def print_message(self, message: Message, template = "{text}") -> None:
        actions = build_actions(self, message, template)
        for action in actions:
            action.run()
        if self.config["always_cut"] or message.cut:
            self.printer.cut()


def build_actions(p: Printer, m: Message, tmpl: str) -> List[PrinterAction]:
    m.dt_printed = datetime.now()

    show_qr      = p.config["url"]["show_qr"]
    ref_urls     = p.config["url"]["reference_urls"]
    urls         = re.findall(r"https?://\S+", m.text) if (show_qr or ref_urls) else []

    if ref_urls:
        seen = {}
        index = 1
        for u in urls:
            if u not in seen:
                seen[u] = index
                index += 1

        for url, i in seen.items():
            m.text = m.text.replace(url, f"[{i}]")

    repl = {
        "{sender}":   m.sender or "Unknown",
        "{sent}":     m.dt_sent.strftime("%Y-%m-%d %H:%M:%S") if isinstance(m.dt_sent, datetime) else "Unknown",
        "{received}": m.dt_received.strftime("%Y-%m-%d %H:%M:%S") if isinstance(m.dt_received, datetime) else "Unknown",
        "{printed}":  m.dt_printed.strftime("%Y-%m-%d %H:%M:%S") if isinstance(m.dt_printed, datetime) else "Unknown",
    }
    for k, v in repl.items():
        tmpl = tmpl.replace(k, v)

    actions: List[PrinterAction] = []
    strip_leading_nl = False
    def append_token_actions(tok: Token) -> None:
        nonlocal strip_leading_nl
        if isinstance(tok, TextToken):
            txt = tok.text
            if strip_leading_nl and txt.startswith("\n"):
                txt = txt[1:]
            strip_leading_nl = False
            if txt:
                actions.append(PrinterAction("text", p.print_text, txt))

        elif isinstance(tok, StyledToken):
            tok_actions, _ = tok.render_ctx(p, m, DEFAULT_STYLE)
            actions.extend(tok_actions)
            if "align" in tok._local_overrides():
                strip_leading_nl = True

        else:
            actions.extend(tok.render(p, m))
    for part in re.split(r"(\{[^}]+\})", tmpl):
        if not part:
            continue

        if part == "{text}":
            if m.has_tokens:
                for t in parse_tokens(m.text):
                    append_token_actions(t)
            else:
                append_token_actions(TextToken(m.text))

        elif part == "{image}":
            if m.image:
                actions.append(PrinterAction("image", p.print_image, m.image))
                actions.append(PrinterAction("cool-down", sleep, p.config["cooldown_ms"]["image"] / 1000))

        elif part == "{qr_codes}":
            if show_qr and urls:
                seen = {}
                for url in urls:
                    if url not in seen:
                        index = len(seen) + 1
                        seen[url] = index
                        actions.append(PrinterAction("qr", p.print_qr, url))
                        label = f"[{index}] {url}" if ref_urls else url
                        actions.append(PrinterAction("qr label", p.print_text, label))

        elif part.startswith("{") and part.endswith("}"):
            continue

        else:
            for t in parse_tokens(part):
                append_token_actions(t)

    return actions