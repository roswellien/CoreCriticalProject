from PIL import Image

for name in ['c5strt10', 'c5strt04', 'c5strt09', 'c5strt12', 'lighthouse01', 'lighthouse04']:
    path = f'local/work-ahead/missilsrm-correction-v1/t1-texture-staging/{name}.png'
    img = Image.open(path)
    print(f"{name}: {img.size}, {img.mode}")
