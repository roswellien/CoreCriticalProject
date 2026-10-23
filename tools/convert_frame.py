import sys
from PIL import Image

src = sys.argv[1]
dst = sys.argv[2]
img = Image.open(src)
img.save(dst)
print(f"Converted {src} ({img.size}, {img.mode}) -> {dst}")
