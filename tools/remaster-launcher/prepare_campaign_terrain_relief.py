"""Refine explicitly selected upgraded campaign surfaces; preserve other bindings.

AI height inputs require per-variant alignment screening. Analytic recipes are
color-derived technical drafts, not recovered physical height or new albedo.
"""
from pathlib import Path
import argparse
import json
import shutil
import struct
import numpy as np
from PIL import Image, ImageFilter
import normal_materials as catalog
from prepare_authored_relief import alignment, normals_from_height, sha
from prepare_world_normals import accelerated_hash
from feature_relief import feature_relief


def atlas_relief(image, recipe):
    """Independent clamped panels; excluded regions and panel guards stay flat."""
    w, h = image.size
    rgba = np.full((h,w,4), [128,128,255,255], dtype='uint8')
    height = Image.new('L', (w,h), 128)
    occupied = np.zeros((h,w), dtype=bool); reports = []
    for rect in recipe['panels']:
        if len(rect)!=4 or not all(0<=v<=1 for v in rect):
            raise ValueError('Atlas panel outside normalized texture bounds')
        x0,y0,x1,y1 = [round(v*s) for v,s in zip(rect,(w,h,w,h))]
        if x1-x0<8 or y1-y0<8 or occupied[y0:y1,x0:x1].any():
            raise ValueError('Atlas panels overlap or are too small')
        occupied[y0:y1,x0:x1] = True
        panel = image.crop((x0,y0,x1,y1)).convert('L')
        # Local shallow grain only: painted panels/window shades are not bulges.
        fine = np.asarray(panel.filter(ImageFilter.GaussianBlur(.6)),dtype=float)
        broad = np.asarray(panel.filter(ImageFilter.GaussianBlur(2.)),dtype=float)
        values = np.rint(np.clip(128+(fine-broad)*.35,0,255)).astype('uint8')
        relief = Image.fromarray(values)
        normal, stats = normals_from_height(relief, panel.size, recipe['depth_ratio'],
                                            recipe['slope_limit'], repeat=False)
        data = np.frombuffer(normal[2],dtype='uint8').reshape(y1-y0,x1-x0,4).copy()
        data[:2,:,:3] = data[-2:,:,:3] = [128,128,255]
        data[:,:2,:3] = data[:,-2:,:3] = [128,128,255]
        rgba[y0:y1,x0:x1] = data; height.paste(relief,(x0,y0))
        reports.append(stats)
    if not reports:
        raise ValueError('No atlas panels selected')
    return (w,h,rgba.tobytes()), height, dict(panels=reports,
        clipped_fraction=max(s['clipped_fraction'] for s in reports),
        excluded_pixels=int((~occupied).sum()))


def analytic_height(image, kind):
    value = np.asarray(image.convert('L'), dtype=float) / 255.
    # Remove the persistent left/right cliff lighting bias before interpreting
    # horizontal ledges. This remains an estimate from upgraded color artwork.
    if kind == 'cliff':
        value -= value.mean(axis=0, keepdims=True) - value.mean()
    def blur(radius):
        # Extended borders avoid introducing wraparound detail during filtering.
        pad = max(4, int(radius * 3))
        padded = np.pad(value, pad, mode='wrap')
        filtered = Image.fromarray(np.rint(np.clip(padded, 0, 1)*255).astype('uint8'))
        return np.asarray(filtered.filter(ImageFilter.GaussianBlur(radius)), dtype=float)[pad:-pad, pad:-pad]/255.
    fine, medium, broad = [blur(x) for x in (.7, 3., 24.)]
    if kind == 'cliff':
        height = .75*(medium-broad) + .25*(fine-medium)
    elif kind == 'transition':
        # Do not turn the large painted sand-color transition into a height step.
        height = .10*(medium-broad) + .65*(fine-medium)
    else:
        height = .12*(medium-broad) + .70*(fine-medium)
    return Image.fromarray(np.rint(np.clip(.5+height, 0, 1)*255).astype('uint8'))


def prepare(config_path, output, hash_library):
    if output.exists():
        raise ValueError('Preserve previous output: choose a fresh directory')
    config = json.loads(config_path.read_text())
    digest = accelerated_hash(hash_library); catalog.pixel_hash = digest
    source_path = Path(config['source_receipt'])
    if sha(source_path) != config['source_receipt_sha256']:
        raise ValueError('Source registration changed')
    source = json.loads(source_path.read_text())
    manifest = Path(config['base_manifest'])
    if sha(manifest) != config['base_manifest_sha256']:
        raise ValueError('Base manifest changed')
    registrations = {tuple(x['key']): x for x in source['registrations']}
    recipes = config['materials']; selected = {}; pins = {}; reports = []; pages = []
    for key, entry in registrations.items():
        choices = [(a, recipes[a['name'].lower()]) for a in entry['aliases']
                   if a['name'].lower() in recipes and
                   Path(source['banks'][a['bank']]['path']).name.startswith('c1-') and
                   ('keys' not in recipes[a['name'].lower()] or
                    list(key) in recipes[a['name'].lower()]['keys'])]
        if choices:
            selected[key] = choices[0]
    output.mkdir(parents=True); (output/'editable').mkdir()
    seen = set(); changed_keys = set(); retained = 0
    lines = manifest.read_text().splitlines()
    if not lines or lines[0] != 'MW34SNP1':
        raise ValueError('Unsupported world manifest')
    for filename in lines[1:]:
        if not filename:
            continue
        path = manifest.parent/filename; before = sha(path)
        result = []; changed = False
        for key, normal in catalog.read_surface_bindings(path.read_bytes()):
            if key in seen:
                raise ValueError('Duplicate world identity')
            seen.add(key)
            if key not in selected:
                result.append((key, normal)); retained += 1; continue
            alias, recipe = selected[key]; name = alias['name'].lower()
            bank = Path(source['banks'][alias['bank']]['path'])
            if str(bank) not in pins:
                pins[str(bank)] = sha(bank)
                if pins[str(bank)] != source['banks'][alias['bank']]['sha256']:
                    raise ValueError('Upgraded source bank changed')
            with bank.open('rb') as stream:
                stream.seek(alias['offset'])
                flags, w, h, reserved, palette, stretch = struct.unpack('<IHHIHH', stream.read(16))
                raw = stream.read(w*h*2)
            if flags not in (5, 37) or reserved or palette or (w,h,1,digest(raw)) != key:
                raise ValueError('Complete source identity mismatch')
            words = np.frombuffer(raw, dtype='<u2').reshape(h,w).astype('uint32')
            rgb = np.stack(((words>>11)*255//31, ((words>>5)&63)*255//63, (words&31)*255//31), axis=-1).astype('uint8')
            image = Image.fromarray(rgb); ratio = min(1., recipe['longest_side']/max(w,h))
            size = (round(w*ratio), round(h*ratio)); review = None
            if 'features' in recipe:
                reference = Path(recipe['layout_reference'])
                if sha(reference) != recipe['layout_reference_sha256']:
                    raise ValueError('Authored feature layout reference changed')
                review = alignment(image, Image.open(reference))
                if review['zero'] < .88 or review['best'][1:] != (0,0):
                    raise ValueError('Feature layout requires separate variant review: '+str((name,key,review)))
                normal, height, stats = feature_relief(image.resize(size, Image.Resampling.LANCZOS), recipe)
            elif recipe.get('panels'):
                normal, height, stats = atlas_relief(image.resize(size, Image.Resampling.LANCZOS), recipe)
            elif recipe.get('height'):
                height_path = Path(recipe['height'])
                if sha(height_path) != recipe['height_sha256']:
                    raise ValueError('Reviewed height changed')
                height = Image.open(height_path).convert('L')
                review = alignment(image, height)
                if review['zero'] < .88 or review['best'][1:] != (0,0):
                    raise ValueError('Height requires separate alignment review: '+str((name,key,review)))
            else:
                height = analytic_height(image.resize(size, Image.Resampling.LANCZOS), recipe['kind'])
            if not recipe.get('panels') and 'features' not in recipe:
                normal, stats = normals_from_height(height, size, recipe['depth_ratio'], recipe['slope_limit'])
            if stats['clipped_fraction'] > .05:
                raise ValueError('Excess clipped relief; recalibrate ' + name)
            stem = f'{name}-{key[3]:016x}'
            height.save(output/'editable'/(stem+'-height.png'))
            Image.frombytes('RGBA', size, normal[2]).save(output/'editable'/(stem+'-normal.png'))
            result.append((key, normal)); changed = True; changed_keys.add(key)
            reports.append(dict(name=name, key=key, recipe=recipe, normal_size=size, alignment=review, stats=stats))
        target = output/filename
        if changed:
            def write_page(entries, name):
                data = catalog.pack_surface_bindings(entries)
                if len(data)>16*1024*1024:
                    if len(entries)<2:
                        raise ValueError('A single normal binding exceeds page budget')
                    mid = len(entries)//2
                    stem = Path(name).stem
                    write_page(entries[:mid], stem+'-a.bin')
                    write_page(entries[mid:], stem+'-b.bin')
                    return
                path_out = output/name
                path_out.write_bytes(data)
                if catalog.read_surface_bindings(data) != entries:
                    raise ValueError('Output roundtrip changed a binding')
                pages.append(dict(name=name,sha256=sha(path_out),bytes=len(data)))
            write_page(result,filename)
        else:
            shutil.copyfile(path, target)
            if catalog.read_surface_bindings(target.read_bytes()) != result:
                raise ValueError('Output roundtrip changed a binding')
            pages.append(dict(name=filename,sha256=sha(target),bytes=target.stat().st_size))
        if sha(path) != before:
            raise ValueError('Page source changed during preparation')
    if changed_keys != selected.keys() or {x['name'] for x in reports} != set(recipes):
        raise ValueError('Selected source identity absent from current manifest')
    total = sum(x['bytes'] for x in pages)
    if total > 512*1024*1024 or len(pages)>256:
        raise ValueError('World package exceeds existing byte budget')
    for path, pin in pins.items():
        if sha(Path(path)) != pin:
            raise ValueError('Source bank changed during authoring')
    receipt = dict(status='Mixed AI-height candidate and material-specific analytic drafts; native art review required',
                   config_sha256=sha(config_path), base_manifest=str(manifest), base_manifest_sha256=sha(manifest),
                   source_pins=pins, pages=pages, bytes=total, bindings=len(seen), retained_bindings=retained,
                   edits=reports, strength_baked=False, albedo_unchanged=True)
    (output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    (output/'world-normals.txt').write_text('MW34SNP1\n'+'\n'.join(x['name'] for x in pages)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'output', 'hash-library'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.config, args.output, args.hash_library)
    print(json.dumps(dict(bytes=result['bytes'], edited_bindings=len(result['edits']), retained_bindings=result['retained_bindings'])))
