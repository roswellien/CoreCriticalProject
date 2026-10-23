import sys
from PIL import Image

path = sys.argv[1]
img = Image.open(path)
w, h = img.size
print(f"Image {path}: {w}x{h}, mode {img.mode}")

dw, dh = 80, 28
small = img.resize((dw, dh)).convert('L')
pixels = list(small.getdata())
chars = " .:-=+*#%@"
print("-" * 80)
for y in range(dh):
    line = "".join(chars[pixels[y * dw + x] * len(chars) // 256] for x in range(dw))
    print(line)
print("-" * 80)
