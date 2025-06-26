from .tokens import Token, TextToken
import re

ESCAPED_OPEN = "##ESCAPED_LT##"
ESCAPED_CLOSE = "##ESCAPED_GT##"

def parse_tokens(src: str) -> list[Token]:
    src = src.replace(r"\<", ESCAPED_OPEN).replace(r"\>", ESCAPED_CLOSE)
    parts = re.split(r"(<[^>]+>)", src)
    root: list[Token] = []
    stack: list[Token] = []

    def current_container() -> list[Token]:
        return stack[-1].children if stack else root

    for part in parts:
        if not part:
            continue

        part = part.replace(ESCAPED_OPEN, "<").replace(ESCAPED_CLOSE, ">")

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
                    current_container().append(TextToken(part))
                    continue
                tok = cls()
                current_container().append(tok)
                if not self_closing:
                    stack.append(tok)
        else:
            current_container().append(TextToken(part))
    return root