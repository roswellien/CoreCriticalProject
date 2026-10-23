"""Package existing local HUD/menu artwork without modifying source resources."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import math
import zipfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def build(kind, sprites, background, host, output):
    if kind not in ('hud', 'menu') or (host and not re.fullmatch('[0-9a-f]{64}', host)):
        raise ValueError('Invalid artwork kind or optional provenance hash')
    sources = {}
    identities = {}
    for path in sorted(Path(sprites).glob('*.rgba')):
        if not re.fullmatch('[0-9a-f]{16}', path.stem):
            raise ValueError('Invalid sprite identity')
        with path.open('rb') as stream:
            magic, w, h, u0, v0, u1, v1 = struct.unpack('<4sII4f', stream.read(28))
        if (magic != b'MW3H' or not 0 < w <= 8192 or not 0 < h <= 8192 or
                path.stat().st_size != 28 + w*h*4 or
                not all(math.isfinite(v) for v in (u0, v0, u1, v1)) or
                not (0 <= u0 < u1 <= 1 and 0 <= v0 < v1 <= 1)):
            raise ValueError('Invalid sprite resource: ' + str(path))
        name = 'ui/sprites/' + path.name
        sources[name] = (path, 'MW3H-v1')
        identities[path.stem] = name
    bg = None
    if background:
        path = Path(background)
        with path.open('rb') as stream:
            magic, w, h, sw, sh = struct.unpack('<8sIIII', stream.read(24))
        if kind != 'menu' or magic != b'MWHDBG1\0' or not all(0 < v <= 16384 for v in (w,h,sw,sh)) or path.stat().st_size != 24+w*h*3:
            raise ValueError('Invalid background resource')
        bg = 'ui/background.mwhd'
        sources[bg] = (path, 'MWHDBG1')
    if not sources or len(identities) > 256:
        raise ValueError('Empty or excessive artwork pack')
    registry = json.dumps(dict(schema_version=2, payload_profile='prepared-ui-v1', kind=kind,
                               sprites=identities, background=bg), indent=2).encode()
    files = {name: dict(bytes=path.stat().st_size, sha256=digest(path), format=fmt)
             for name, (path, fmt) in sources.items()}
    files['ui/ui.json'] = dict(bytes=len(registry), sha256=hashlib.sha256(registry).hexdigest())
    if sum(f['bytes'] for f in files.values()) > 512*1024*1024:
        raise ValueError('Artwork pack exceeds 512 MiB')
    manifest = dict(schema_version=2, game_id="mw3", id='com.mw3remaster.'+kind, name='Remaster '+('HUD' if kind == 'hud' else 'Menus'),
                    version='1.0.0', author='MW3 Remaster', category=kind.title(),
                    description='Current remaster artwork; original layout and input remain in the runtime.',
                    native_payload=dict(profile='prepared-ui-v1', registry='ui/ui.json', path_base='pack-root',
                                        required_capabilities={'ui-artwork':1}, reference_host_sha256=host, required_formats=sorted({fmt for _,fmt in sources.values()})), files=files)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
        archive.writestr('pack.json', json.dumps(manifest, indent=2))
        archive.writestr('ui/ui.json', registry)
        for name, (path, _) in sources.items():
            archive.write(path, name)
    with zipfile.ZipFile(output) as archive:
        for name, pin in files.items():
            with archive.open(name) as stream:
                if hashlib.file_digest(stream, 'sha256').hexdigest() != pin['sha256']:
                    raise ValueError('Archive verification failed: '+name)
    for name, (path, _) in sources.items():
        if digest(path) != files[name]['sha256']:
            raise ValueError('Source changed while packaging: '+str(path))
    return dict(path=str(output.resolve()), sha256=digest(output), bytes=output.stat().st_size, verified=True, files=files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    native = json.loads(args.profile.read_text())['native']
    env = native['runtime_environment']
    results = [build(kind, env[key], env.get('MW34_MENU_HD_BG') if kind == 'menu' else None,
                     native['executable_sha256'], args.output / (kind+'-1.0.0.mw3pack'))
               for kind, key in [('hud','MW34_HIRES_HUD'), ('menu','MW34_HIRES_MENU')]]
    (args.output/'packs.json').write_text(json.dumps(dict(verified=True, packs=results), indent=2))
    print(json.dumps([{k:v for k,v in result.items() if k != 'files'} for result in results], indent=2))
