"""Build a replacement-mech normal-map sidecar (BWNRM1) from its texture sidecar and donor normal maps.

The texture sidecar (BWTEX1) gives the batch -> material list and the five
material names (Body, Variant, Weapons, Window, MissileHead). Body/Variant/
Weapons take the donor OpenGL (Y+) tangent-space normal PNGs unchanged (as
the validated Mad Cat sidecar); Window and MissileHead are flat 64x64.
Outputs stay local (derived from licensed game assets).
"""
from pathlib import Path
import argparse, struct
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
NAMES = ('Body', 'Variant', 'Weapons')

def read_texture_sidecar(path):
    with open(path, 'rb') as f:
        if f.read(8) != b'BWTEX1\0\0': raise SystemExit('Not a BWTEX1 texture sidecar')
        batches, count = struct.unpack('<II', f.read(8))
        index = struct.unpack('<%dI' % batches, f.read(4 * batches))
        names = []
        for _ in range(count):
            names.append(f.read(32).split(b'\0')[0].decode()); w, h = struct.unpack('<II', f.read(8)); f.read(8); f.seek(w * h * 2, 1)
    return index, names

def find_normal(donor, name):
    for pattern in (f'{name}_normal_opengl.png', f'{name}_opengl_normal.png'):
        p = Path(donor) / pattern
        if p.exists(): return p
    raise SystemExit(f'No donor normal map for {name} in {donor}')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--textures', required=True); ap.add_argument('--donor', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    index, names = read_texture_sidecar(a.textures)
    if len(names) != 5: raise SystemExit('Expected five materials')
    out = bytearray(b'BWNRM1\0\0') + struct.pack('<II', len(index), len(names)) + struct.pack('<%dI' % len(index), *index)
    for name in names:
        if name in NAMES:
            px = np.asarray(Image.open(find_normal(a.donor, name)).convert('RGBA'), np.uint8).copy(); px[..., 3] = 255
        else:
            px = np.zeros((64, 64, 4), np.uint8); px[...] = (128, 128, 255, 255)
        h, w = px.shape[:2]
        tag = struct.pack('<Q', hash(px[::17, ::17].tobytes()) & 0xffffffffffffffff)
        out += name.encode().ljust(32, b'\0') + struct.pack('<II', w, h) + tag + px.tobytes()
        print(f'  {name}: {w}x{h}')
    Path(a.out).write_bytes(bytes(out)); print('wrote', a.out, len(out))

if __name__ == '__main__':
    main()
