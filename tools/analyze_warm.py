import sys
from PIL import Image

path = sys.argv[1]
img = Image.open(path)
w, h = img.size

data = list(img.getdata())
# Filter for warm amber/gold lighting (R > 180, G > 90, B < 80)
warm = [(i % w, i // w, p) for i, p in enumerate(data) if p[0] > 160 and p[1] > 80 and p[2] < 100]
print(f"Warm light fixture / illuminated pixels: {len(warm)}")

if warm:
    # Compute centroid
    cx = sum(p[0] for p in warm) / len(warm)
    cy = sum(p[1] for p in warm) / len(warm)
    print(f"Centroid of warm illumination: ({cx:.1f}, {cy:.1f})")
    
    # Check y-distribution
    y_min = min(p[1] for p in warm)
    y_max = max(p[1] for p in warm)
    x_min = min(p[0] for p in warm)
    x_max = max(p[0] for p in warm)
    print(f"Spread: X=[{x_min}, {x_max}], Y=[{y_min}, {y_max}]")
