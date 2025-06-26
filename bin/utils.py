def encode_cp858(text: str) -> bytes:
	return text.encode('cp858', errors='replace')