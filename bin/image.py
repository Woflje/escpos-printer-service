from PIL import Image

def process_image():
	# Convert to RGBA and paste onto white background
	img = img.convert("RGBA")
	background = Image.new("RGBA", img.size, "WHITE")
	background.alpha_composite(img)

	# Convert to RGB and rotate
	img = background.convert("RGB").rotate(rotate_angle, expand=True)

	# Rotate again if aspect ratio exceeds threshold
	if img.width > rotate_to_fit_threshold_factor * img.height:
		img = img.rotate(90, expand=True)

	# Resize to max width while maintaining aspect ratio
	new_height = int(max_width * img.height / img.width)
	img = img.resize((max_width, new_height))
