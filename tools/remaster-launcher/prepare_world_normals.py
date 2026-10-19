"""Optional automatic world-normal preview, keyed to complete installed pixels.

Uses bounded normal-map pages, preserving authored registrations at runtime.
Height is a conservative color-derived estimate, not recovered physical relief.
Original banks and color artwork are read-only. Outputs must be fresh and local.
"""
from pathlib import Path
import argparse
import ctypes
import hashlib
import json
import struct
import sys

from normal_materials import pack_surface_bindings, pixel_hash
from prepare_surface_normals import bank_entries

REGIONS = {'t1', 'c1', 'c2', 'c3', 'c4', 'c4b'}
EXCLUDED = {'effects_animation', 'sky_candidate', 'water_shore_candidate'}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def accelerated_hash(path):
    library = ctypes.CDLL(str(Path(path).resolve(strict=True)))
    function = library.mw34_normal_hash
    function.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    function.restype = ctypes.c_uint64
    def digest(data):
        return function(data, len(data))
    for data in [b'', bytes(range(256)) * 7]:
        if digest(data) != pixel_hash(data):
            raise ValueError('Normal hash helper failed its reference control')
    return digest


def generate_normal(colour, width, height, format_, *, terrain=False, max_size=128):
    import numpy as np
    from PIL import Image
    words = np.frombuffer(colour, dtype='<u2').reshape(height, width)
    if format_ == 1:
        r, g, b = (words >> 11) / 31., ((words >> 5) & 63) / 63., (words & 31) / 31.
    elif format_ == 2:
        r, g, b = ((words >> 10) & 31) / 31., ((words >> 5) & 31) / 31., (words & 31) / 31.
    else:
        raise ValueError('Unsupported automatic normal source format')
    luminance = (r * .2126 + g * .7152 + b * .0722).astype('float32')
    ratio = min(1., max_size / width, max_size / height)
    size = (max(1, round(width * ratio)), max(1, round(height * ratio)))
    image = Image.fromarray(luminance)
    value = np.asarray(image.resize(size, Image.Resampling.BOX), dtype='float32')
    # Periodic separable Gaussian removes broad baked illumination. A second
    # short filter suppresses texel noise. All differentiation uses stored V.
    def blur(source, kernel):
        result = source
        for axis in [0, 1]:
            result = sum(weight * np.roll(result, i - len(kernel)//2, axis=axis)
                         for i, weight in enumerate(kernel)) / sum(kernel)
        return result
    detail = blur(value, [1, 2, 1]) - blur(value, [1, 4, 6, 4, 1])
    dx = (np.roll(detail, -1, axis=1) - np.roll(detail, 1, axis=1)) * 4.
    dy = (np.roll(detail, -1, axis=0) - np.roll(detail, 1, axis=0)) * 4.
    slopes = np.sqrt(dx*dx + dy*dy)
    maximum = .35 if terrain else .15
    scale = np.minimum(1., maximum / np.maximum(slopes, 1e-20))
    normal = np.stack((-dx*scale, -dy*scale, np.ones_like(dx)), axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    pixels = np.empty((*normal.shape[:2], 4), dtype='uint8')
    pixels[:, :, :3] = np.rint(np.clip(normal*.5 + .5, 0, 1)*255).astype('uint8')
    pixels[:, :, 3] = 255
    if not terrain:
        # Object atlases may not repeat: avoid inventing a ridge at the border.
        pixels[:2, :, :3] = pixels[-2:, :, :3] = [128, 128, 255]
        pixels[:, :2, :3] = pixels[:, -2:, :3] = [128, 128, 255]
    return (*size, pixels.tobytes())


def prepare(banks_path, inventory_path, output, hash_library):
    import numpy as np
    import PIL
    output = Path(output).resolve()
    if output.exists():
        raise ValueError('Choose a fresh world-normal directory')
    banks_path, inventory_path = Path(banks_path), Path(inventory_path)
    inputs = {'banks_sha256': sha(banks_path), 'inventory_sha256': sha(inventory_path),
              'hash_library_sha256': sha(Path(hash_library))}
    types = {e['name']: e for e in json.loads(inventory_path.read_text())['textures']}
    digest = accelerated_hash(hash_library)
    entries = {}; banks = []; exclusions = {}; selected = 0
    for bank in json.loads(banks_path.read_text()):
        region = Path(bank['target'].replace('\\', '/')).parent.name
        if region not in REGIONS:
            continue
        if bank.get('installed_AI') is not True:
            raise ValueError('World normals require a registered upgraded color bank')
        path = Path(bank['source']).resolve(strict=True)
        if sha(path) != bank['expected_sha256']:
            raise ValueError('Published color bank changed: ' + str(path))
        banks.append(dict(path=str(path), sha256=bank['expected_sha256']))
        print('Indexing', region, bank['bank'], flush=True)
        with path.open('rb') as stream:
            for name, (offset, span) in bank_entries(path).items():
                entry = types.get(name.lower())
                reason = None
                if not entry or region not in entry['scene_referenced_regions']:
                    reason = 'not_referenced_by_world_scene'
                elif entry['category'] in EXCLUDED:
                    reason = entry['category']
                if reason:
                    exclusions[reason] = exclusions.get(reason, 0) + 1
                    continue
                stream.seek(offset)
                flags, w, h, reserved, palette, stretch = struct.unpack('<IHHIHH', stream.read(16))
                alpha_plane = flags in (11, 0x2b)
                if flags not in (5, 0x25, 11, 0x2b) or reserved or palette or stretch not in (0,1,2,3) or not 0<w<=4096 or not 0<h<=4096 or span != 16+w*h*(3 if alpha_plane else 2):
                    raise ValueError('Unmodelled selected world color layout: ' + str((path, name)))
                colour = stream.read(w*h*2)
                terrain = entry['category'] == 'terrain_marked_world_geometry'
                alias = dict(name=name, bank=len(banks)-1, offset=offset, stretch=stretch)
                variants = [(1, colour, 'rgb565')]
                if alpha_plane:
                    words = np.frombuffer(colour, dtype='<u2')
                    alpha = np.frombuffer(stream.read(w*h), dtype='uint8').astype('uint16')
                    argb1555 = ((words >> 1) & 0x7fe0) | (words & 31) | ((alpha >= 128).astype('uint16') << 15)
                    argb4444 = ((words >> 4) & 0xf00) | ((words >> 3) & 0xf0) | ((words >> 1) & 15) | ((alpha >> 4) << 12)
                    variants += [(2, argb1555.astype('<u2').tobytes(), 'argb1555'),
                                 (3, argb4444.astype('<u2').tobytes(), 'argb4444')]
                for format_, pixels, conversion in variants:
                    key = (w, h, format_, digest(pixels))
                    if key in entries:
                        entries[key]['aliases'].append(alias)
                        entries[key]['terrain'] &= terrain
                    else:
                        entries[key] = dict(terrain=terrain, aliases=[alias], conversion=conversion)
                selected += 1
    # Build one page at a time; at most 64 small normal images are retained.
    output.mkdir(parents=True)
    pages = []; receipt = []; batch = []; last_source = None; last_normal = None
    for number, (key, entry) in enumerate(entries.items()):
        w, h, format_, _ = key; source = entry['aliases'][0]
        with Path(banks[source['bank']]['path']).open('rb') as stream:
            stream.seek(source['offset']+16);colour = stream.read(w*h*2)
        if entry['conversion'] == 'rgb565' and digest(colour) != key[3]:
            raise ValueError('World source changed during generation')
        source_identity = (source['bank'], source['offset'], entry['terrain'])
        normal = last_normal if source_identity == last_source else generate_normal(colour, w, h, 1, terrain=entry['terrain'])
        last_source, last_normal = source_identity, normal
        batch.append((key, normal))
        receipt.append(dict(key=key, terrain=entry['terrain'], aliases=entry['aliases'], conversion=entry['conversion'],
                            normal_size=normal[:2], normal_sha256=hashlib.sha256(normal[2]).hexdigest()))
        if len(batch) == 64 or number == len(entries)-1:
            name = f'page-{len(pages):03d}.bin';data = pack_surface_bindings(batch)
            (output/name).write_bytes(data);pages.append(dict(name=name, sha256=sha(output/name), bindings=len(batch)))
            print('Prepared', name, 'through', number+1, '/', len(entries), flush=True);batch.clear()
    if not pages or len(pages)>256 or sum((output/p['name']).stat().st_size for p in pages)>512*1024*1024:
        raise ValueError('World-normal package exceeds its bounded resident budget')
    for bank in banks:
        if sha(Path(bank['path'])) != bank['sha256']:
            raise ValueError('World bank changed during preparation')
    if sha(banks_path)!=inputs['banks_sha256'] or sha(inventory_path)!=inputs['inventory_sha256']:
        raise ValueError('World registration inputs changed during preparation')
    # Publish the manifest last. An interrupted directory is not launchable.
    report=dict(schema_version=1, method='conservative automatic color-derived height; not authored physical relief',
                source_entries=selected, unique_bindings=len(entries), pages=pages, banks=banks,
                exclusions=exclusions, registrations=receipt, inputs=inputs,
                settings=dict(max_normal_size=128, terrain_slope_limit=.35, object_slope_limit=.15,
                              object_flat_border=2, row_order='stored', normal_y='negative height V derivative'),
                dependencies=dict(pillow=PIL.__version__, numpy=np.__version__),
                authored_precedence=True)
    (output/'receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    (output/'world-normals.txt').write_text('MW34SNP1\n'+'\n'.join(p['name'] for p in pages)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--banks', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hash-library', type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.banks, args.inventory, args.output, args.hash_library)
    print('Prepared', result['unique_bindings'], 'unique world normal bindings')
