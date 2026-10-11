"""Export MW3 HUD evidence and an isolated font-antialiasing archive candidate.

Uses the project's compiled, checked M4 reader parser. Never installs outputs.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import struct
import subprocess

from decode_images import decode, inspect_package, png_bytes

ROOT = Path(__file__).resolve().parents[2]
READER_HASH = '5e17037f3634480f74265b3e378e4513b84cae518e20bc55cd5c6e9c6683851a'
IMAGE_HASH = '3519eb39907a08900ec175ec9dd828ba15878e2a4a9b0f7263525eb5a88ad4cc'
TARGETS = {'hud_messages', 'hud_htal', 'mech_string', 'wepif_font',
           'wepstring_red', 'wepstring_green', 'wepstring_yellow', 'wepstring_grey'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse(parser, path, entry=None):
    args = [str(parser), '--document' if entry else '--directory', str(path)]
    if entry:
        args.append(entry)
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    obj = json.loads(result.stdout)
    return obj['document'] if entry else obj


def tree(document, index=0):
    node = document['nodes'][index]
    if node['type'] == 4:
        return [tree(document, child) for child in node['children']]
    if node['type'] == 3:
        return bytes.fromhex(node['string_hex']).decode('ascii')
    if node['type'] == 2:
        return struct.unpack('<f', struct.pack('<I', node['word']))[0]
    return struct.unpack('<i', struct.pack('<I', node['word']))[0]


def patch_fonts(payload, document):
    """Append quality=4 to exactly eight existing Windows font property lists."""
    base = document['view_offset']
    nodes = document['nodes']
    edits = []
    found = set()
    addition = struct.pack('<II', 3, 7) + b'quality' + struct.pack('<II', 4, 2) + struct.pack('<II', 1, 4)
    for node in nodes:
        if node['type'] != 4:
            continue
        children = node['children']
        for pos, child in enumerate(children[:-1]):
            key = tree(document, child)
            if not isinstance(key, str) or key not in TARGETS:
                continue
            if key in found:
                raise ValueError('Duplicate target font')
            properties = nodes[children[pos + 1]]
            values = tree(document, children[pos + 1])
            if properties['type'] != 4 or 'quality' in values:
                raise ValueError('Unsupported font property layout or existing quality')
            if len(values) % 2 or 'face' not in values or 'height' not in values:
                raise ValueError('Missing font properties')
            found.add(key)
            edits.append((properties['offset'] - base, properties['end'] - base))
    if found != TARGETS:
        raise ValueError('Missing target fonts')
    result = bytearray(payload)
    for begin, end in sorted(edits, reverse=True):
        count = struct.unpack_from('<I', result, begin + 4)[0]
        struct.pack_into('<I', result, begin + 4, count + 2)
        result[end:end] = addition
    return bytes(result)


def candidate_archive(data, directory, entry, replacement):
    """Keep all old payloads/metadata; redirect only fonts to an appended payload."""
    start = directory['directory_offset']
    tail = bytearray(data[start:])
    relative = entry['directory_offset'] - start
    struct.pack_into('<II', tail, relative, start, len(replacement))
    return data[:start] + replacement + tail


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reader', type=Path, default=ROOT / 'MW3/zbd/reader.zbd')
    ap.add_argument('--images', type=Path, default=ROOT / 'MW3/zbd/rimage.zbd')
    ap.add_argument('--parser', type=Path, default=ROOT / 'build/m4-assets-parser-r1/mw34_m4_assets.exe')
    ap.add_argument('--output-dir', type=Path, required=True)
    args = ap.parse_args()
    output = args.output_dir.resolve()
    private = (ROOT / 'local/work-ahead').resolve()
    if output == private or not output.is_relative_to(private) or output.exists():
        ap.error('Choose a fresh directory below local/work-ahead')
    reader, images = args.reader.read_bytes(), args.images.read_bytes()
    if digest(reader) != READER_HASH or digest(images) != IMAGE_HASH:
        ap.error('Unsupported original archive identity')
    directory = parse(args.parser, args.reader)
    fonts = parse(args.parser, args.reader, 'fonts.zrd')
    layout = parse(args.parser, args.reader, 'hud.zrd')
    entry = next(e for e in directory['entries'] if e['name'] == 'fonts.zrd')
    payload = reader[entry['offset']:entry['offset'] + entry['bytes']]
    modified = patch_fonts(payload, fonts)
    candidate = candidate_archive(reader, directory, entry, modified)
    table, accepted, rejected = inspect_package(images)
    if rejected:
        raise ValueError('Image descriptor rejection')
    previews = []
    for e in table['entries']:
        if e['name'].startswith('hud_') or e['name'] == 'sensor_reticule':
            info, rgba = decode(images, e)
            png = png_bytes(info['width'], info['height'], rgba)
            previews.append((e, info, png))
    output.mkdir(parents=True)
    candidate_path = output / 'reader-antialiased-candidate.zbd'
    candidate_path.write_bytes(candidate)
    # Independent native parser must accept the reconstructed whole archive.
    after_directory = parse(args.parser, candidate_path)
    after_fonts = parse(args.parser, candidate_path, 'fonts.zrd')
    expected = tree(fonts)
    definitions = expected[0][3]
    for i in range(0, len(definitions), 2):
        if definitions[i] in TARGETS:
            definitions[i + 1].extend(['quality', [4]])
    if tree(after_fonts) != expected:
        raise ValueError('Candidate font tree changed beyond requested quality fields')
    unchanged = 0
    for old, new in zip(directory['entries'], after_directory['entries'], strict=True):
        if old['name'] == 'fonts.zrd':
            continue
        old_fields = {k: v for k, v in old.items() if k != 'directory_offset'}
        new_fields = {k: v for k, v in new.items() if k != 'directory_offset'}
        if old_fields != new_fields or reader[old['offset']:old['offset'] + old['bytes']] != candidate[new['offset']:new['offset'] + new['bytes']]:
            raise ValueError('Non-font archive entry changed')
        unchanged += 1
    inventory = []
    cards = []
    for e, info, png in previews:
        filename = f"entry-{e['index']:05d}.png"
        (output / filename).write_bytes(png)
        inventory.append({'index': e['index'], 'name': e['name'], **info, 'file': filename, 'sha256': digest(png)})
        cards.append(f'<article><b>{html.escape(e["name"])}</b><p>{info["width"]} × {info["height"]} · {info["alpha_mode"]}</p><div><img src="{filename}" alt="{html.escape(e["name"])}" style="width:{info["width"]}px;height:{info["height"]}px"></div></article>')
    original_fonts = tree(fonts)[0][3]
    definitions = {original_fonts[i]: original_fonts[i + 1] for i in range(0, len(original_fonts), 2)}
    report = {'status': 'offline research; candidate not installed or game-tested',
              'reader_sha256': digest(reader), 'images_sha256': digest(images),
              'tool_sha256': digest(Path(__file__).read_bytes()), 'parser_sha256': digest(args.parser.read_bytes()),
              'decoder_sha256': digest(Path(__file__).with_name('decode_images.py').read_bytes()),
              'image_table_parser_sha256': digest(Path(__file__).with_name('probe.py').read_bytes()),
              'fonts': definitions, 'hud_layouts': tree(layout), 'sprites': inventory,
              'candidate': {'file': candidate_path.name, 'sha256': digest(candidate),
                            'targets': sorted(TARGETS), 'quality': 4, 'unchanged_other_entries': unchanged,
                            'native_parser_verified': True, 'font_tree_exact_change_verified': True,
                            'dimensions_and_layout_changed': False}}
    (output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    document = '''<!doctype html><meta charset="utf-8"><title>MW3 HUD source review</title>
<style>body{background:#101917;color:#d3e6da;font:15px system-ui;margin:32px}article{border:1px solid #385047;padding:14px;margin:12px 0}article div{overflow:auto;padding:20px;background:#050806}p{color:#aec4b8}img{image-rendering:pixelated}canvas{max-width:100%;border:1px solid #385047}label{display:block;margin:16px 0}</style>
<h1>MW3 HUD source review</h1><p>Original decoded sprites. Font comparison below is a browser demonstration of resolution strategy, not captured game text or proof of the archive candidate.</p>
<label>HUD scale <input id="scale" type="range" min="1" max="5" value="3" step="1"> <span id="value"></span></label>
<h2>Small raster enlarged</h2><canvas id="old"></canvas><h2>Font rendered at output resolution</h2><canvas id="new"></canvas>
<p>Illustrative Arial sample at 10 logical pixels. The isolated archive candidate requests quality=4 for eight HUD-related fonts; it preserves their original size and all layout settings. Game validation is still required.</p>
<h2>Source sprites</h2>''' + ''.join(cards) + '''<script>
const scale=document.getElementById('scale');
function render(){let s=Number(scale.value);document.getElementById('value').textContent=s+'×';let source=document.createElement('canvas');source.width=540;source.height=30;let c=source.getContext('2d');c.fillStyle='#00eb00';c.font='10px Arial';c.fillText('PPC   LRM 20   HEAT 35%   SPEED 64 KPH   TARGET: MAD CAT',8,18);
for(let id of ['old','new']){let dest=document.getElementById(id);dest.width=540*s;dest.height=30*s;let d=dest.getContext('2d');d.fillStyle='#050806';d.fillRect(0,0,dest.width,dest.height);if(id==='old'){d.imageSmoothingEnabled=false;d.drawImage(source,0,0,dest.width,dest.height)}else{d.fillStyle='#00eb00';d.font=(10*s)+'px Arial';d.fillText('PPC   LRM 20   HEAT 35%   SPEED 64 KPH   TARGET: MAD CAT',8*s,18*s)}}
document.querySelectorAll('img').forEach(img=>{img.style.width=(Number(img.dataset.w??(img.dataset.w=parseInt(img.style.width)))*s)+'px';img.style.height=(Number(img.dataset.h??(img.dataset.h=parseInt(img.style.height)))*s)+'px'})}
scale.addEventListener('input',render);render();</script>'''
    (output / 'review.html').write_text(document, encoding='utf-8')
    if args.reader.read_bytes() != reader or args.images.read_bytes() != images:
        raise ValueError('Original archives changed during preparation')
    print(json.dumps({'output': str(output), 'sprites': len(inventory), 'fonts': len(definitions),
                      'candidate': report['candidate']}, indent=2))


if __name__ == '__main__':
    main()
