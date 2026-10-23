"""Give a plain upgraded terrain texture the detail and normal relief of a reference.

Example: the Campaign 1 base-plateau sand (DKSAND) next to the detailed desert
ground (txgter_1). Both banks were enlarged 16x from tiny originals, so they
share texel density; the plain one lacks mid-scale features and a normal map.

Method (deterministic, local inputs only):
1. Reference luminance band-pass (pebble/clump scale), made periodic at the
   target width by summing the two half-shifted copies (variance restored).
2. Applied to the target as a relative luminance modulation at the reference's
   relative contrast; the target's own colour is preserved.
3. Normal map from luminance gradients with the blur/scale calibrated to
   reproduce the reference's existing normal map, so both respond alike.

Outputs stay local (derived from original game artwork; never commit them).
Requires Pillow and NumPy only.
"""
from pathlib import Path
import argparse, io, json, struct, zipfile
import numpy as np
from PIL import Image

def blur(a, sigma):
    """Periodic Gaussian blur (textures tile), exact via FFT."""
    if sigma <= 0: return a
    h, w = a.shape
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-2 * (np.pi * sigma) ** 2 * (fx ** 2 + fy ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g))

def luminance(rgb): return rgb @ np.array([0.2126, 0.7152, 0.0722])

def normals(height, sigma, scale):
    hgt = blur(height, sigma)
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) / 2
    gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) / 2
    n = np.dstack([-scale * gx, -scale * gy, np.ones_like(gx)])
    return n / np.linalg.norm(n, axis=2, keepdims=True)

def read_sidecar(path):
    d = Path(path).read_bytes(); assert d[:8] == b'BWNRM1\0\0'
    o = 8; batches, count = struct.unpack_from('<II', d, o); o += 8; out = []
    for _ in range(count):
        name = d[o:o+32].split(b'\0')[0].decode(); o += 32
        w, h = struct.unpack_from('<II', d, o); o += 8; tag = d[o:o+8]; o += 8
        px = np.frombuffer(d, np.uint8, w*h*4, o).reshape(h, w, 4); o += w*h*4
        out.append((name, tag, px))
    return out

def write_sidecar(path, entries):
    b = bytearray(b'BWNRM1\0\0') + struct.pack('<II', 1, len(entries))
    for name, tag, px in entries:
        h, w = px.shape[:2]
        b += name.encode().ljust(32, b'\0') + struct.pack('<II', w, h) + tag + px.astype(np.uint8).tobytes()
    Path(path).write_bytes(bytes(b))

def rgb565_signature(rgb):
    """First two 32-bit words of the RGB565 texture as the game stores it (little-endian pixel pairs)."""
    p = [((int(r) >> 3) << 11) | ((int(g) >> 2) << 5) | (int(b) >> 3) for r, g, b in rgb[0, :4]]
    return (p[1] << 16 | p[0], p[3] << 16 | p[2])

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bank-zip', required=True, help='unzbd textures ZIP of the upgraded bank')
    ap.add_argument('--target', default='DKSAND'); ap.add_argument('--reference', default='txgter_1')
    ap.add_argument('--reference-normals', required=True, help='existing BWNRM1 sidecar for the reference')
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--strength', type=float, default=1.0, help='detail contrast relative to the reference')
    ap.add_argument('--height-blur', type=float, default=0.0, help='height smoothing (pixels) before normals')
    a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    z = zipfile.ZipFile(a.bank_zip)
    tgt = np.asarray(Image.open(io.BytesIO(z.read(a.target + '.png'))).convert('RGB'), np.float64)
    ref = np.asarray(Image.open(io.BytesIO(z.read(a.reference + '.png'))).convert('RGB'), np.float64)
    (ref_name, ref_tag, ref_px), = [e for e in read_sidecar(a.reference_normals) if e[0] == a.reference]
    ref_n = ref_px[..., :3] / 255 * 2 - 1
    th, tw = tgt.shape[:2]; rh, rw = ref.shape[:2]
    if rw % tw or rh % th: raise SystemExit('Reference size must be a whole multiple of the target size')

    # 1. Reference band-pass detail, folded to the target period.
    lr = luminance(ref)
    band = blur(lr, 0.8) - blur(lr, 20)
    rel = band / lr.mean()
    folded = np.zeros((th, tw))
    k = 0
    for y in range(0, rh, th):
        for x in range(0, rw, tw):
            folded += rel[y:y+th, x:x+tw]; k += 1
    folded /= np.sqrt(k)
    folded *= rel.std() / max(folded.std(), 1e-9)

    # 2. Relative luminance modulation of the target (colour preserved).
    out = np.clip(tgt * (1 + a.strength * folded)[..., None], 0, 255)

    # 3. Normal procedure calibrated on the reference.
    best = None
    for sigma in (0.0, 0.5, 0.8, 1.2, 1.6, 2.0):
        for scale in np.geomspace(0.01, 1.0, 40):
            n = normals(lr, sigma, scale)
            err = np.abs(n - ref_n).mean()
            if best is None or err < best[0]: best = (err, sigma, scale)
    err, sigma, scale = best
    # The target's own pixel-scale grain would turn into busy sparkle: smooth
    # its height lightly, then match the reference's overall relief strength.
    height = blur(luminance(out), max(sigma, a.height_blur))
    ref_rms = float(np.sqrt((ref_n[..., :2] ** 2).mean()))
    lo_s, hi_s = 1e-4, 10.0
    for _ in range(60):
        mid = np.sqrt(lo_s * hi_s); rms = float(np.sqrt((normals(height, 0, mid)[..., :2] ** 2).mean()))
        lo_s, hi_s = (mid, hi_s) if rms < ref_rms else (lo_s, mid)
    scale = np.sqrt(lo_s * hi_s)
    tn = normals(height, 0, scale)
    tnp = np.dstack([np.clip((tn + 1) / 2 * 255 + 0.5, 0, 255), np.full((th, tw), 255.0)])

    Image.fromarray(out.round().astype(np.uint8)).save(a.out / f'{a.target}.png')
    Image.fromarray(tnp[..., :3].astype(np.uint8)).save(a.out / f'{a.target}-normal.png')
    sig = rgb565_signature(out.round().astype(np.uint8))
    report = {
        'target': a.target, 'reference': a.reference, 'size': [tw, th], 'strength': a.strength,
        'normal_calibration': {'reference_blur_sigma': sigma, 'target_height_blur': max(sigma, a.height_blur), 'target_scale': float(scale), 'mean_abs_error_vs_reference': float(err)},
        'reference_normal_xy_rms': float(np.sqrt((ref_n[..., :2] ** 2).mean())),
        'target_normal_xy_rms': float(np.sqrt((tn[..., :2] ** 2).mean())),
        'target_rgb565_signature': [f'{sig[0]:08x}', f'{sig[1]:08x}'],
        'mean_rgb_before': tgt.reshape(-1, 3).mean(0).round(2).tolist(), 'mean_rgb_after': out.reshape(-1, 3).mean(0).round(2).tolist(),
    }
    entries = [(ref_name, ref_tag, ref_px), (a.target, struct.pack('<II', *sig), tnp.astype(np.uint8))]
    write_sidecar(a.out / 'ground-normals-v2.bin', entries)
    (a.out / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
