"""Author a front silhouette from a BWMESH4 rest pose (Pillow authoring only).

The runtime consumes the resulting MW3ICON1 mask without image dependencies.
"""
import argparse
from pathlib import Path
import struct

from chassis_icons import MAGIC, WIDTH, HEIGHT, mask


def render(data):
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
    if data[:8] != b'BWMESH4\0' or len(data) < 64:
        raise ValueError('Expected BWMESH4 geometry')
    batches, bones, refs, _ = struct.unpack_from('<4I', data, 8)
    if not 0 < bones <= 256 or not 0 < batches <= 4096 or refs > 128:
        raise ValueError('Invalid geometry counts')
    matrices = [struct.unpack_from('<16d', data, 64 + i * 196 + 68) for i in range(bones)]
    offset, triangles = 64 + bones * 196 + refs * 160, []
    for _ in range(batches):
        bone, count, _ = struct.unpack_from('<III', data, offset + 64); offset += 76
        if count % 3 or count > 10_000_000:
            raise ValueError('Invalid triangle count')
        vertices = [struct.unpack_from('<8f', data, offset + i * 32)[:3] for i in range(count)]
        offset += count * 32
        indices = [bone] * count
        if bone == 0xffffffff:
            indices = struct.unpack_from(f'<{count}I', data, offset); offset += count * 4
        points = []
        for p, index in zip(vertices, indices):
            m = matrices[index]
            points.append(tuple(sum(m[r * 4 + c] * p[c] for c in range(3)) + m[r * 4 + 3] for r in range(3)))
        triangles.extend(points[i:i + 3] for i in range(0, count, 3))
    if offset != len(data) or not triangles:
        raise ValueError('Truncated geometry or trailing bytes')
    points = [p for triangle in triangles for p in triangle]
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    scale = min((WIDTH - 4) / (hi[1] - lo[1]), (HEIGHT - 4) / (hi[2] - lo[2]))
    # Donor axes: X forward, Y sideways, Z up. A front orthographic outline
    # uses Y/Z and therefore remains independent of any gameplay camera.
    oversample = 4
    canvas = Image.new('L', (WIDTH * oversample, HEIGHT * oversample))
    draw = ImageDraw.Draw(canvas)
    for triangle in triangles:
        draw.polygon([((WIDTH / 2 + (p[1] - (hi[1] + lo[1]) / 2) * scale) * oversample,
                       (HEIGHT - 2 - (p[2] - lo[2]) * scale) * oversample) for p in triangle], fill=255)
    canvas = canvas.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    edge = ImageChops.subtract(canvas, canvas.filter(ImageFilter.MinFilter(3)))
    result = ImageChops.lighter(edge, canvas.point(lambda p: p // 5))
    raw = MAGIC + struct.pack('<II', WIDTH, HEIGHT) + result.tobytes()
    mask(raw)
    return raw, result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    raw, preview = render(args.mesh.read_bytes())
    args.output.write_bytes(raw)
    preview.resize((WIDTH * 6, HEIGHT * 6)).save(args.output.with_suffix('.png'))
