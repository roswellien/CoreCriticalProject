"""Build the native host's hi-res HUD pack (local, private data) from the v3 component package.

For every vector remake whose original sprite has the same name and logical size, the original sprite's identity key
is computed exactly as the native GPU HUD computes it for an in-game image (gpu_hud.inc hud_identity): FNV-1a 64 over
width and height (32-bit little-endian each), then one 16-bit little-endian word per pixel, row-major: the pixel's
RGB565 value when it is opaque, 0 when it is transparent (original alpha 0). The vector is rasterized at the requested
density with the prototype's own vector() function (rasterize.cjs, padded straight-alpha RGBA). Each pack file is
<key as 16 hex digits>.rgba:
  'MW3H', u32 width, u32 height, float u0, v0, u1, v1 (the logical image inside the padded texture), RGBA bytes.
The runtime draws an in-game image with a matching key from this texture, at the image's logical size; the game's
logic, positions and crops are unchanged. Originals and generated textures stay local (docs/legal.md).
Usage: python build_hires_pack.py COMPONENTS.json OUT_DIR --density 4 --canvas-package PATH
"""
import argparse, base64, io, json, struct, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent


def identity(rgba, w, h):
    v = 0xcbf29ce484222325

    def fold(bs):
        nonlocal v
        for b in bs:
            v ^= b
            v = (v * 0x100000001b3) & 0xffffffffffffffff
    fold(struct.pack('<II', w, h))
    px = rgba.load()
    for y in range(h):
        row = bytearray()
        for x in range(w):
            r, g, b, a = px[x, y]
            c = 0 if a == 0 else (round(r * 31 / 255) << 11) | (round(g * 63 / 255) << 5) | round(b * 31 / 255)
            row += struct.pack('<H', c)
        fold(row)
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('components'); ap.add_argument('out')
    ap.add_argument('--density', type=float, default=4.0)
    ap.add_argument('--canvas-package', required=True)
    a = ap.parse_args()
    data = json.loads(Path(a.components).read_text(encoding='utf-8'))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    names = [n for n, v in data['vectors'].items() if n in data['resources']
             and data['resources'][n]['width'] == v['width'] and data['resources'][n]['height'] == v['height']]
    keys = {}
    for n in names:
        r = data['resources'][n]
        img = Image.open(io.BytesIO(base64.b64decode(r['source'].split(',', 1)[1]))).convert('RGBA')
        assert img.size == (r['width'], r['height']), n
        keys[n] = identity(img, r['width'], r['height'])
    with tempfile.TemporaryDirectory() as tmp:
        req = Path(tmp) / 'request.json'
        req.write_text(json.dumps({'density': a.density, 'entries': [{'componentId': n} for n in names]}))
        subprocess.run(['node', str(HERE / 'rasterize.cjs'), a.components, str(req), tmp, a.canvas_package], check=True)
        textures = json.loads((Path(tmp) / 'textures.json').read_text())['textures']
        manifest = []
        for n, t in zip(names, textures):
            assert t['componentId'] == n
            raw = (Path(tmp) / t['file']).read_bytes()
            pw, ph, pad, d = t['physicalWidth'], t['physicalHeight'], t['padding'], t['density']
            u0, v0 = pad / pw, pad / ph
            u1, v1 = (pad + t['logicalWidth'] * d) / pw, (pad + t['logicalHeight'] * d) / ph
            name = f'{keys[n]:016x}.rgba'
            (out / name).write_bytes(b'MW3H' + struct.pack('<IIffff', pw, ph, u0, v0, u1, v1) + raw)
            manifest.append({'component': n, 'key': f'{keys[n]:016x}', 'logical': [t['logicalWidth'], t['logicalHeight']], 'physical': [pw, ph]})
    (out / 'manifest.json').write_text(json.dumps({'density': a.density, 'entries': manifest}, indent=1))
    print(f'{len(manifest)} hi-res HUD components ->', out)


if __name__ == '__main__':
    main()
