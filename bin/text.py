from emoji import demojize

text_processors = [
	demojize,

]

def process_text(text: str) -> str:
	"""
	Process the text using a series of text processors.
	:param text: The input text to process.
	:return: The processed text.
	"""
	for processor in text_processors:
		text = processor(text)
	return text