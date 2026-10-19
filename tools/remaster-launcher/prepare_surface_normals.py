"""Bind reviewed stock normal maps to exact, pinned live color-bank pixels.

The local configuration explicitly selects bank entries and preview manifests.
The PNG must reproduce every bank color word using the published bank's RGB565
rounding rule. Names alone never admit a material. No color bank is modified.
"""
from pathlib import Path
import argparse
import array
import hashlib
import json
import os
import struct
import sys

from normal_materials import pack_surface_bindings, pixel_hash, read_surface_bindings


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pinned(item, base):
    path = (base / item['path']).resolve(strict=True)
    if sha(path) != item['sha256']:
        raise ValueError('Pinned input changed: ' + str(path))
    return path


def bank_entries(path):
    # Existing MW3 image-table contract: 24-byte header and 40-byte records.
    with path.open('rb') as stream:
        header = stream.read(24)
        if len(header) != 24:
            raise ValueError('Truncated color bank')
        words = struct.unpack('<6I', header)
        count = words[3]
        if not 0 < count <= 100000 or words != (0, 1, 0, count, 0, 0):
            raise ValueError('Unsupported color bank header')
        raw = stream.read(count * 40)
        if len(raw) != count * 40:
            raise ValueError('Truncated color bank table')
    size = path.stat().st_size
    records=[];names=set();previous=24+count*40-1
    for raw_name, offset, marker in struct.iter_unpack('<32sII', raw):
        name=raw_name.split(b'\0')[0].decode('ascii')
        if not name or name in names or offset<=previous or offset+16>size or marker!=0xffffffff:
            raise ValueError('Invalid color bank entry')
        names.add(name);records.append((name,offset));previous=offset
    return {name:(offset,(records[i+1][1] if i+1<len(records) else size)-offset)
            for i,(name,offset) in enumerate(records)}


def prepare(config_path, output):
    from PIL import Image
    config_path=Path(config_path).resolve(strict=True);base=config_path.parent
    output=Path(output).resolve()
    if output.exists() or output.with_suffix('.json').exists():
        raise ValueError('Choose a fresh catalog output; preserve previous evidence')
    config=json.loads(config_path.read_text())
    if config.get('schema_version')!=1:
        raise ValueError('Unsupported catalog registration')
    bindings={};receipt=[];normal_cache={}
    if config.get('preserve_catalog'):
        seed=pinned(config['preserve_catalog'],base)
        bindings.update(read_surface_bindings(seed.read_bytes()))
    red=[round(value*31/255) for value in range(256)]
    green=[round(value*63/255) for value in range(256)]
    for registration in config['registrations']:
        bank=pinned(registration['bank'],base);table=bank_entries(bank)
        manifest_path=pinned(registration['manifest'],base)
        manifest=json.loads(manifest_path.read_text())
        normal_pins={(manifest_path.parent/entry['normal']).resolve():entry['normal_sha256']
                     for entry in manifest.get('unique_relief_tiles',[]) if 'normal_sha256' in entry}
        orientation=registration['normal_row_order'];normal_y=registration['normal_y']
        if orientation not in ('stored','flip-y') or normal_y not in ('preserve','invert'):
            raise ValueError('Explicit normal row order and Y convention required')
        excluded=set(registration.get('exclude',[]));seen=set()
        with bank.open('rb') as stream:
            for material in manifest['materials']:
                name=material['name'];seen.add(name)
                if name in excluded:continue
                if name not in table:raise ValueError('Missing selected bank material: '+name)
                offset,span=table[name];stream.seek(offset);descriptor=stream.read(16)
                flags,w,h,reserved,palette,stretch=struct.unpack('<IHHIHH',descriptor)
                if flags not in (3,5,0x23,0x25) or reserved or palette or stretch or not 0<w<=4096 or not 0<h<=4096 or span!=16+w*h*2:
                    raise ValueError('Unsupported opaque color layout: '+name)
                colour=stream.read(w*h*2)
                colour_path=(manifest_path.parent/material['basecolor']).resolve(strict=True)
                normal_path=(manifest_path.parent/material['normal']).resolve(strict=True)
                colour_digest=sha(colour_path);normal_digest=sha(normal_path)
                if normal_pins and normal_pins.get(normal_path)!=normal_digest:
                    raise ValueError('Reviewed normal image identity changed: '+name)
                with Image.open(colour_path) as image:
                    image=image.convert('RGB')
                    if image.size!=(w,h):raise ValueError('Color dimensions differ: '+name)
                    pixels=image.get_flattened_data() if hasattr(image,'get_flattened_data') else image.getdata()
                    expected=array.array('H',((red[r]<<11)|(green[g]<<5)|red[b] for r,g,b in pixels))
                if sys.byteorder!='little':expected.byteswap()
                if expected.tobytes()!=colour:
                    raise ValueError('Reviewed color does not match every bank pixel: '+name)
                normal_identity=(str(normal_path),normal_digest,orientation,normal_y)
                if normal_identity not in normal_cache:
                    with Image.open(normal_path) as image:
                        image=image.convert('RGBA')
                        if orientation=='flip-y':image=image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                        if normal_y=='invert':
                            r,g,b,a=image.split();image=Image.merge('RGBA',(r,g.point([255-i for i in range(256)]),b,a))
                        normal_cache[normal_identity]=(*image.size,image.tobytes())
                if sha(colour_path)!=colour_digest or sha(normal_path)!=normal_digest:
                    raise ValueError('Material source changed during preparation: '+name)
                normal=normal_cache[normal_identity];key=(w,h,1,pixel_hash(colour))
                if key in bindings and bindings[key]!=normal:
                    raise ValueError('Conflicting normal maps for identical color pixels: '+name)
                bindings[key]=normal
                receipt.append(dict(material=name,bank=str(bank),bank_offset=offset,key=key,
                                    colour_sha256=colour_digest,normal=str(normal_path),
                                    normal_sha256=normal_digest,row_order=orientation,normal_y=normal_y))
        if excluded-seen:raise ValueError('Unknown explicit material exclusions')
        if sha(bank)!=registration['bank']['sha256'] or sha(manifest_path)!=registration['manifest']['sha256']:
            raise ValueError('Pinned bank/manifest changed during preparation')
    packed=pack_surface_bindings(list(bindings.items()))
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_suffix(output.suffix+'.tmp')
    with temporary.open('xb') as stream:stream.write(packed)
    os.replace(temporary,output)
    report=dict(config_sha256=sha(config_path),catalog_sha256=sha(output),bindings=len(bindings),
                registrations=receipt,scope='Exact color pixels; optional stock surface normals; no color or game-state changes')
    output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=prepare(args.config,args.output)
    print('Prepared',report['bindings'],'full-content surface bindings')
