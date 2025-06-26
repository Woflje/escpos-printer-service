# ESC/POS Printer Service

A lightweight Python service that **receives messages over TCP, queues them in TinyDB, and prints them on an ESC/POS thermal printer**.  
It supports text, images, QR codes, custom HTML-like templates, Prometheus metrics, fine-grained API-key permissions, runtime control (pause/resume), and scheduled working hours.

---

## ✨ Features

| Feature                              | Details |
| --- | --- |
| **TCP message server**               | Simple `\n`-terminated JSON protocol on a single port. |
| **TinyDB queue**                     | Messages stored as documents; oldest-first processing. |
| **ESC/POS printing**                 | Serial connection via `python-escpos`; supports text, images, QR codes, cut. |
| **HTML-like templates**              | `<h1>`, `<center>`, `<b>`, … tokens parsed to printer actions. |
| **API keys in files**                | `data/printkeys/<name>.txt` (1st line = key, 2nd line = comma-separated permissions). |
| **Permissions**                      | `control`, `summary`, *(future)* custom roles. |
| **Runtime control**                  | Pause / resume queue with a `{"type": "control"}` message. |
| **Daily schedule**                   | Optional time window (e.g. 08:00-20:00); overnight ranges supported. |
| **Prometheus metrics**               | `/metrics` via `prometheus_client`. |
| **Structured logging & rotation**    | Console + file (`data/logs/latest.log`). |
| **Config-driven**                    | Single YAML file → **no code changes** required for most tweaks. |

---

## 📦 Requirements

- Python 3.9+
- ESC/POS-compatible printer (serial/USB)
- OS with serial port access (Linux recommended)
- Packages:
  - `python-escpos`
  - `pillow`
  - `tinydb`
  - `tinydb-serialization`
  - `prometheus_client`
  - `emoji`
  - `PyYAML`

```bash
pip install -r requirements.txt
```

## 🗝️ Print-key Setup
each file in `data/printkeys/` represents a named print-key:
```bash
data/printkeys/
├── wolfsprintkey.txt
├── admin.txt
```
Each file format:
```
<KEY_STRING>
permission1,permission2,control
```
First line: the actual print-key
Second line: (optional) comma-separated permissions

## 💬 Message Types
### 1. Print Message
```json
{
  "api_key": "YOUR_KEY",
  "type": "message",
  "text": "Hello <b>World</b>!",
  "image": "<base64-JPEG>",
  "custom_template": "{text}"
}
```
###  2. Summary Request
```json
{
  "api_key": "YOUR_KEY",
  "type": "summary"
}
```
### 3. Control
```json
{
  "api_key": "ADMIN_KEY",
  "type": "control",
  "value": {
    "message_processing": false
  }
}
```

## Template system
Templates are defined in Python modules in config/template/*.py.
They expose a global template string with supported tokens:
```php-template
<text>, <image>, <qr_codes>, <h1>, <center>, <right>, <b>, <invert>, ...
```
Example:
```php-template
<center><h1>{sender}</h1></center>
{image}
{text}
{qr_codes}
```

- More tokens can be added in bin/printer/tokens/tokens.py
- Message text can make use of style tokens
- Messages can come with custom templates

| Tag        | Description             |
| ---------- | ----------------------- |
| `<h1>`     | Large bold header       |
| `<h2>`     | Medium bold header      |
| `<b>`      | Bold text               |
| `<center>` | Center alignment        |
| `<right>`  | Right alignment         |
| `<invert>` | Invert (black on white) |
| `<flip>`   | Upside-down text        |
| `<u1>`     | Underline               |
| `<u2>`     | Double underline        |
| `<code>`   | Monospaced font         |


## Text Handling
Message text will be processed in order for the printer to be able to print it. Emoji's are 

## 🖼️ Image Handling

You can send a base64-encoded JPEG image with your message:

```json
{
  "api_key": "KEY",
  "text": "Here's a picture",
  "image": "<base64-JPEG>"
}
```

The server will:
- Decode the image
- Convert it to RGB
- Auto-rotate it (optional)
- Resize it to max_width defined in config.yaml
- Save it as a JPEG file
- Store the image path in the message queue

If rotate_to_fit is true, and the image is too wide (e.g. width > 3× height), it gets rotated 90° for better printing.

## 🔗 URLs and QR Codes
If a message contains URLs in its text, they are automatically extracted and processed.

If printer.text.template contains the {qr_codes} token, each detected URL is:
- Referenced instead of rendered in-line
- Rendered as a QR code with the full url as label

```
Hello! Scan this url: https://example.com
```
Becomes
```
Hello! Scan this url: [1]
```
And in the `{qr_codes}` section:
```
<printed qr code>
[1] https://example.com
```

## Prometheus Metrics
| Metric                        | Meaning                      |
| ----------------------------- | ---------------------------- |
| `printer_server_up`           | 1 when the server is running |
| `printer_server_errors_total` | Number of unhandled errors   |
| `printer_server_queue_length` | Number of messages in queue  |

## Credits
With love and help from the thermal-printer fax community

[Ostheer](https://github.com/Ostheer/IBM4610_bot)

[MaxWinsemius](https://github.com/MaxWinsemius/faxwinsemius_tgbot)

[H0yVoy](https://github.com/H0yVoy/Bonnetjesprinter)

[Senkii-code](https://github.com/Senkii-code/faxii)

[Michaaaaaaa](https://github.com/Michaaaaaaa/bonnenprinter)

[ArwinV](https://github.com/ArwinV/BragiTelegramBot)