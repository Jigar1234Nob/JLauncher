from pathlib import Path
from PIL import Image, ImageDraw

out = Path("assets")
out.mkdir(exist_ok=True)
size = 256
image = Image.new("RGBA", (size, size), (17, 19, 25, 255))
draw = ImageDraw.Draw(image)
# Angular JL monogram matching the in-app logo.
draw.polygon([(25, 86), (133, 18), (133, 194), (78, 239), (18, 239), (78, 188), (78, 88)], fill="#A33BFF")
draw.polygon([(148, 44), (210, 87), (210, 192), (252, 192), (210, 239), (148, 239)], fill="#16BFEA")
draw.polygon([(133, 18), (148, 44), (148, 239), (133, 221)], fill="#5638E8")
image.save(out / "jigarzon.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
