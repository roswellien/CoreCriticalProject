import sys
from PIL import Image

path = sys.argv[1]
img = Image.open(path)
w, h = img.size
print(f"Image {path}: {w}x{h}, mode {img.mode}")

data = list(img.getdata())
bright = [(i % w, i // w, p) for i, p in enumerate(data) if any(c > 150 for c in p[:3])]
print(f"Total bright pixels (>150): {len(bright)}")

# Group by region
for x, y, p in bright[:30]:
    print(f"  Pixel at ({x}, {y}): RGB = {p}")

# Find cluster centers
if bright:
    xs = [b[0] for b in bright]
    ys = [b[1] for b in bright]
    print(f"Bounds: X in [{min(xs)}, {max(xs)}], Y in [{min(ys)}, {max(ys)}]")
