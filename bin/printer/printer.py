from escpos.printer import Serial # type: ignore
from bin.load import CONFIG
from bin.message import Message
from .action import PrinterAction
from bin.utils import encode_cp858
from config.style import DEFAULT_STYLE
from datetime import datetime
from typing import List
import re
from .tokens.tokens import Token, TextToken, StyledToken
from .tokens.parser import parse_tokens
from time import sleep


def _format_dt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "Unknown"

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
				timeout=1,
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
		actions = self.build_actions(message, template)
		for action in actions:
			action.run()
		if self.config.get("always_cut") or getattr(message, "cut", False):
			self.printer.cut()

	def build_actions(self, m: Message, tmpl: str) -> List[PrinterAction]:
		# Use .get and getattr to avoid errors if keys/attributes are missing
		if self.config.get("text", {}).get("allow_custom_template", False) and getattr(m, "custom_template", None):
			tmpl = m.custom_template

		m.dt_printed = getattr(m, "dt_printed", None) or datetime.now()

		show_qr      = self.config.get("url", {}).get("show_qr", False)
		ref_urls     = self.config.get("url", {}).get("reference_urls", False)
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
			"{sender}":   getattr(m, "sender", "Unknown") or "Unknown",
			"{sent}":     _format_dt(getattr(m, "dt_sent", None)),
			"{received}": _format_dt(getattr(m, "dt_received", None)),
			"{printed}":  _format_dt(getattr(m, "dt_printed", None)),
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
					actions.append(PrinterAction("text", self.print_text, txt))

			elif isinstance(tok, StyledToken):
				tok_actions, _ = tok.render_ctx(self, m, DEFAULT_STYLE)
				actions.extend(tok_actions)
				if "align" in tok._local_overrides():
					strip_leading_nl = True

			else:
				actions.extend(tok.render(self, m))
		for part in re.split(r"(\{[^}]+\})", tmpl):
			if not part:
				continue

			if part == "{text}":
				for t in parse_tokens(m.text):
					append_token_actions(t)

			elif part == "{image}":
				if getattr(m, "image", None):
					actions.append(PrinterAction("image", self.print_image, m.image))
					actions.append(PrinterAction("cool-down", sleep, self.config.get("cooldown_ms", {}).get("image", 0) / 1000))

			elif part == "{qr_codes}":
				if show_qr and urls:
					seen = {}
					for url in urls:
						if url not in seen:
							index = len(seen) + 1
							seen[url] = index
							actions.append(PrinterAction("qr", self.print_qr, url))
							label = f"[{index}] {url}" if ref_urls else url
							actions.append(PrinterAction("qr label", self.print_text, label))

			elif part.startswith("{") and part.endswith("}"):
				continue

			else:
				for t in parse_tokens(part):
					append_token_actions(t)

		return actions