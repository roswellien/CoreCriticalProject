from PIL import Image

img = Image.open('reports/lighting-integrated-20261019-r6/captures/fixture-lights-night-frame650.png')
w, h = img.size

# Let's crop to the region of interest where warm pixels are (around y=500 to 768, x=0 to 1024)
crop = img.crop((0, 450, w, 768))
crop.save('reports/lighting-integrated-20261019-r6/captures/fixture-lights-ground-crop.png')
print("Cropped ground illumination to fixture-lights-ground-crop.png:", crop.size)

# Let's also inspect if there are bright lamp posts or fixtures in the upper part
upper = img.crop((0, 0, w, 450))
data_up = list(upper.getdata())
bright_up = [(i % w, i // w, p) for i, p in enumerate(data_up) if any(c > 120 for c in p[:3])]
print("Bright points in upper scene (lamps/towers/flares):", len(bright_up))
for pt in bright_up[:15]:
    print("  Upper point:", pt)
