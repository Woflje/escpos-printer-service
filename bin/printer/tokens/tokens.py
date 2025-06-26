from typing import Any, List, TYPE_CHECKING
from config.style import DEFAULT_STYLE, STYLE_KEYS
from ..action import PrinterAction
from bin.message import Message

if TYPE_CHECKING:
    from ..printer import Printer

def merged_style(base: dict[str, Any], **overrides: dict[str, Any]) -> dict[str, Any]:
    st = {k: base[k] for k in STYLE_KEYS}
    st.update({k: v for k, v in overrides.items() if v is not None})
    return st

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


class H1Token(StyledToken):  	tag, width, height = 	"<h1>", 3, 3
class H2Token(StyledToken):  	tag, width, height = 	"<h2>", 2, 2
class CenterToken(StyledToken): tag, align = 			"<center>", "center"
class RightToken(StyledToken):  tag, align = 			"<right>", "right"
class BoldToken(StyledToken):  	tag, bold = 			"<b>",  True
class U1Token(StyledToken):  	tag, underline = 		"<u1>",  1
class U2Token(StyledToken):  	tag, underline = 		"<u2>",  2
class InvertToken(StyledToken): tag, invert = 			"<invert>",  True
class FlipToken(StyledToken):  	tag, flip = 			"<flip>",  True
class CodeToken(StyledToken):  	tag, font = 			"<code>",  "b"