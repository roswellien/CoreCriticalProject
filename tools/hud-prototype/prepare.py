"""Build a private, standalone MW3 HUD component fidelity prototype."""
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/asset-inventory'))
from decode_images import decode, inspect_package, png_bytes
from prepare_hud_research import IMAGE_HASH, READER_HASH, parse, tree


def pairs(values):
    if len(values) % 2:
        raise ValueError('Invalid property pairs')
    return dict(zip(values[::2], values[1::2]))


def vector_models():
    """Authored geometry following source silhouettes, dimensions and colors.

    Numerals are regenerated Arial, not mechanically enlarged bitmap numerals.
    Dynamic compass and panel text remain a demonstrator, not game telemetry.
    """
    models = {}
    def line(x1, y1, x2, y2, color='#00a000', width=1):
        return dict(kind='line', points=[x1, y1, x2, y2], color=color, width=width)
    def text(value, x, y, size=6, color='#00eb00'):
        return dict(kind='text', value=value, x=x, y=y, size=size, color=color)
    def poly(points, color):
        return dict(kind='polygon', points=points, color=color)
    for family, color in [('ally', '#1010bb'), ('en', '#eb0018'), ('nav', '#00bb00'), ('mfb', '#bba400')]:
        for direction in ['down', 'up', 'left', 'right']:
            vertical = direction in ['down', 'up']
            w, h = (25, 14) if vertical else (14, 25)
            points = {'down': [1, 1, 24, 1, 12.5, 13], 'up': [1, 13, 24, 13, 12.5, 1],
                      'left': [13, 1, 13, 24, 1, 12.5], 'right': [1, 1, 1, 24, 13, 12.5]}[direction]
            models[f'hud_{family}arrow_{direction}'] = {'width': w, 'height': h, 'shapes': [poly(points, color)]}
    for name, color in [('sensor_reticule', '#d00028'), ('hud_zoomcant', '#1010cc'),
                        ('hud_zoomoff', '#1010cc'), ('hud_zoomon', '#1010cc'), ('hud_zoomover', '#1010cc')]:
        models[name] = {'width': 21, 'height': 21, 'shapes': [line(10.5, .5, 10.5, 5.5, color),
                        line(10.5, 15.5, 10.5, 20.5, color), line(.5, 10.5, 5.5, 10.5, color),
                        line(15.5, 10.5, 20.5, 10.5, color),
                        {'kind': 'rect', 'x': 10, 'y': 10, 'width': 1, 'height': 1, 'color': color}]}
    for name, w, h, x, top, bottom, labels in [
            ('hud_speed_frame', 28, 78, 15.5, 10.5, 77.5, [('100', 1, 6), ('50', 1, 29), ('0', 9, 52)]),
            ('hud_altitude_frame', 26, 54, 18.5, 5.5, 53.5, [('100', 0, 5), ('50', 3, 29), ('0', 12, 53)]),
            ('hud_fuel_frame', 27, 38, 21.5, 5.5, 37.5, [('100', 0, 5), ('0', 7, 37)]),
            ('hud_coolant_frame', 20, 40, 14.5, 6.5, 39.5, [('F', 0, 6), ('E', 0, 39)])]:
        shapes = [line(x, top, x, bottom), line(x-6, top, x+1, top), line(x-6, bottom, x+5, bottom)]
        ticks = 3 if name == 'hud_speed_frame' else 2
        for k in range(1, ticks+1):
            yy = top + (bottom-top)*k/(ticks+1)
            shapes.append(line(x-6, yy, x, yy))
        shapes.extend(text(value, xx, yy) for value, xx, yy in labels)
        models[name] = {'width': w, 'height': h, 'shapes': shapes}
    heat = [line(16.5, .5, 16.5, 120.5, '#00b000')]
    for k in range(13):
        y = .5+k*10
        color = '#f00018' if k < 5 else '#ffc000' if k < 8 else '#00c000'
        heat.append(line(0.5 if k < 5 else 8.5, y, 16.5, y, color))
    models['hud_heat_meter'] = {'width': 17, 'height': 122, 'shapes': heat}
    for name, color in [('hud_mech_ally_sm', '#1010bb'), ('hud_mech_enemy_sm', '#eb0018'), ('hud_mech_other_sm', '#00c000')]:
        models[name] = {'width': 5, 'height': 5, 'shapes': [poly([2.5, 0, 5, 2.5, 2.5, 5, 0, 2.5], color)]}
    models['hud_weapon_select'] = {'width': 5, 'height': 7, 'shapes': [poly([0, 0, 5, 3.5, 0, 7], '#eb0018')]}
    models['hud_weapon_chain'] = {'width': 5, 'height': 7, 'shapes': [
        line(.5, .5, 4.5, 3.5, '#00d000'), line(4.5, 3.5, .5, 6.5, '#00d000'), line(.5, .5, .5, 6.5, '#00d000')]}
    return models


def svg(model):
    elements = []
    for s in model['shapes']:
        color = s['color']
        if s['kind'] == 'line':
            x1,y1,x2,y2 = s['points']
            elements.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{s["width"]}"/>')
        elif s['kind'] == 'polygon':
            points = ' '.join(f'{x},{y}' for x,y in zip(s['points'][::2], s['points'][1::2]))
            elements.append(f'<polygon points="{points}" fill="{color}"/>')
        elif s['kind'] == 'rect':
            elements.append(f'<rect x="{s["x"]}" y="{s["y"]}" width="{s["width"]}" height="{s["height"]}" fill="{color}"/>')
        elif s['kind'] == 'text':
            elements.append(f'<text x="{s["x"]}" y="{s["y"]}" font-family="Arial,sans-serif" font-size="{s["size"]}" fill="{color}">{html.escape(s["value"])}</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{model["width"]}" height="{model["height"]}" viewBox="0 0 {model["width"]} {model["height"]}">' + ''.join(elements) + '</svg>'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--parser', type=Path, default=ROOT/'build/m4-assets-parser-r1/mw34_m4_assets.exe')
    args = ap.parse_args()
    out = args.output_dir.resolve(); private = (ROOT/'local/work-ahead').resolve()
    if out == private or not out.is_relative_to(private) or out.exists():
        ap.error('Output must be a fresh directory below local/work-ahead')
    image_path = ROOT/'MW3/zbd/rimage.zbd'; reader_path = ROOT/'MW3/zbd/reader.zbd'
    images = image_path.read_bytes(); reader = reader_path.read_bytes()
    if hashlib.sha256(images).hexdigest() != IMAGE_HASH or hashlib.sha256(reader).hexdigest() != READER_HASH:
        ap.error('Original archive identities do not match')
    table, _, rejected = inspect_package(images)
    if rejected:
        raise ValueError('Unsupported source images')
    fonts = tree(parse(args.parser, reader_path, 'fonts.zrd'))[0][3]
    layout = tree(parse(args.parser, reader_path, 'hud.zrd'))[0]
    models = vector_models(); resources = {}; outputs = {}
    for entry in table['entries']:
        if not (entry['name'].startswith('hud_') or entry['name'] == 'sensor_reticule'):
            continue
        info, rgba = decode(images, entry); png = png_bytes(info['width'], info['height'], rgba)
        name = entry['name']
        resources[name] = {'index': entry['index'], 'width': info['width'], 'height': info['height'],
                           'source': 'data:image/png;base64,' + base64.b64encode(png).decode()}
        if name in models:
            model = models[name]
            if (model['width'], model['height']) != (info['width'], info['height']):
                raise ValueError('Logical dimensions changed')
            outputs[name+'.svg'] = svg(model).encode()
    data = {'resources': resources, 'vectors': models, 'fonts': {n: pairs(v) for n,v in pairs(fonts).items()},
            'layouts': {n: {k: pairs(v) for k,v in pairs(vals).items()} for n,vals in pairs(layout).items()}}
    js = Path(__file__).with_name('renderer.js').read_text(encoding='utf-8')
    template = Path(__file__).with_name('review.html').read_text(encoding='utf-8')
    document = template.replace('/*MODEL*/', 'const HUD_DATA = '+json.dumps(data)+';').replace('/*RENDERER*/', js)
    outputs['review.html'] = document.encode('utf-8')
    outputs['components.json'] = (json.dumps(data, indent=2)+'\n').encode()
    manifest = {'status': 'standalone authored component prototype; no game telemetry or integration',
                'source_images_sha256': IMAGE_HASH, 'source_reader_sha256': READER_HASH,
                'vector_count': len(outputs)-2, 'source_component_count': len(resources),
                'original_logical_dimensions_preserved': True,
                'style_limitations': 'Source-informed geometry and regenerated numerals; not pixel-identical redraws',
                'sources': {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.iterdir() if f.is_file()},
                'outputs': {n: hashlib.sha256(v).hexdigest() for n,v in outputs.items()}}
    outputs['manifest.json'] = (json.dumps(manifest, indent=2)+'\n').encode()
    out.mkdir(parents=True)
    for name, value in outputs.items():
        (out/name).write_bytes(value)
    if image_path.read_bytes() != images or reader_path.read_bytes() != reader:
        raise ValueError('Original assets changed during preparation')
    print(json.dumps({'output': str(out), 'vectors': manifest['vector_count'], 'source_components': len(resources)}))


if __name__ == '__main__':
    main()
