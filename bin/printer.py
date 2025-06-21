import logging
from escpos.printer import Serial
from datetime import datetime
from time import sleep
from config import CONFIG
from message import Message
import re

class Printer:
    def __init__(self, name: str, port: str, baud: int):
        self.name = name
        self.port = port
        self.baud = baud
        self.config = CONFIG["printer"]
        self.connect()

    def connect(self):
        try:
            self.printer = Serial(devfile=self.port, baudrate=self.baud)
        except Exception as e:
            raise RuntimeError(f"Failed to connect to printer {self.name}: {e}")

    def print_text(self, text: str):
        self.printer.text(text)

    def print_image(self, image_path: str):
        self.printer.image(image_path)

    def cut(self):
        self.printer.cut()

    def print_qr(self, url: str):
        self.printer.qr(url)

    def print_qr_codes(self, urls):
        for i, url in enumerate(urls, 1):
            self.print_qr(url)
            if self.config["url"]["reference_urls"]:
                self.print_text(f"[{i}] {url}\n")
            else:
                self.print_text(url + "\n")

    def print_template_split(self, message: Message, template: str):
        formatted = template.format(
            text=message.text,
            sender=message.sender,
            received=message.dt.sent.strftime("%Y-%d-%m %H:%M:%S"),
            received=message.dt.received.strftime("%Y-%d-%m %H:%M:%S"),
            printed=message.dt.printed.strftime("%Y-%d-%m %H:%M:%S"),
        )
        self.print_text(formatted)

    def print_template_urls(self, message: Message, template: str, urls):
        if '{urls}' not in template:
            self.print_template_split(message, template)
            return
        parts = template.split('{urls}')
        if len(parts) == 2:
            self.print_template_split(message, parts[0])
            if urls and self.config["url"]["show_qr"]:
                self.print_qr_codes(urls)
            self.print_template_split(message, parts[1])
        else:
            raise ValueError("Invalid {urls} usage in template")

    def print_message(self, message: Message, template: str):
        message.dt.printed = datetime.now()
        parts = template.split('{image}')
        show_qr = self.config["url"]["show_qr"]
        reference_urls = self.config["url"]["reference_urls"]

        urls = re.findall(r"https?://\S+", message.text) if (show_qr or reference_urls) else []

        if reference_urls and urls:
            if '{urls}' in template:
                for i, url in enumerate(urls, 1):
                    message.text = message.text.replace(url, f"[{i}]")
            else:
                logging.getLogger(__name__).warning("{urls} not found in template, URLs not replaced.")

        if len(parts) == 1:
            self.print_template_urls(message, template, urls)
        elif len(parts) == 2:
            self.print_template_urls(message, parts[0], urls)
            self.print_image(message.image)
            sleep(self.config["cooldown_ms"]["image"] / 1000)
            self.print_template_urls(message, parts[1], urls)
        else:
            raise ValueError("Invalid {image} usage in template")

        self.cut()
