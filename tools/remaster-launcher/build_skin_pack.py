"""Build an unsigned, data-only named skin pack from a local authored project."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import struct
import zipfile

from native_assets import material_pixels
from prepared_skin_packs import PROFILE, REGISTRY


def build(project_path, output):
    project_path = Path(project_path).resolve()
    project = json.loads(project_path.read_text(encoding='utf-8'))
    if (not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,127}', project['pack_id'])
            or not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,63}', project['skin_id'])
            or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[a-zA-Z0-9.-]+)?', project['version'])
            or not isinstance(project.get('materials'), dict) or not 1 <= len(project['materials']) <= 64
            or any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]{0,30}', n) for n in project['materials'])):
        raise ValueError('Invalid local skin project identifiers or material names')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    stage = output / 'pack'
    files = {}

    def add(name, data, fmt=None):
        path = stage / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        files[name] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        if fmt:
            files[name]['format'] = fmt
        return name

    textures, meshes = {}, {}
    for lod in ('close', 'distance'):
        entry = project['lods'][lod]
        metadata = json.loads((project_path.parent / entry['metadata']).read_text())
        mesh = project_path.parent / entry['mesh']
        with mesh.open('rb') as stream:
            meshes[lod] = hashlib.file_digest(stream, 'sha256').hexdigest()
        names = list(project['materials'])
        bindings = [names.index(batch['material']) for batch in metadata['batches']]
        blob = (b'BWTEX1\0\0' + struct.pack('<II', len(bindings), len(names))
                + struct.pack('<'+'I'*len(bindings), *bindings)
                + material_pixels(project_path.parent, project['materials']))
        digest = hashlib.sha256(blob).hexdigest()
        name = 'payload/' + digest + '.bin'
        if name not in files:
            add(name, blob, 'BWTEX1')
        textures[lod] = name
    registry = dict(schema_version=2, payload_profile=PROFILE, skins=[dict(
        id=project['pack_id'] + ':' + project['skin_id'], name=project['name'],
        chassis=project['chassis'], mesh_sha256=meshes, textures=textures)])
    encode = lambda value: (json.dumps(value, indent=2) + '\n').encode('utf-8')
    add(REGISTRY, encode(registry))
    chassis_name = project.get('chassis_name', 'Additional Mech' if ':' in project['chassis'] else project['chassis'].title())
    if not isinstance(chassis_name, str) or not 1 <= len(chassis_name) <= 64 or any(ord(c)<32 for c in chassis_name):
        raise ValueError('Invalid chassis display name')
    capabilities = {'additional-mech-skins': 1}
    if ':' in project['chassis']:
        capabilities['additional-mech-chassis'] = 1
    manifest = dict(schema_version=2, game_id='mw3', id=project['pack_id'],
                    name=project['name'] + ' — ' + chassis_name + ' Skin',
                    version=project['version'], author=project.get('author', 'Core Critical'),
                    category='Mech Skins', description=project.get('description', 'Additional selectable '+project['name']+
                    ' skin. Select it in Mech Lab. Preserves all existing skins. Requires a compatible enabled model pack.'),
                    native_payload=dict(profile=PROFILE, registry=REGISTRY, path_base='pack-root',
                                        required_formats=['BWTEX1'], required_capabilities=capabilities),
                    provides=dict(textures=True), files=files)
    (stage / 'pack.json').write_bytes(encode(manifest))
    archive = output / (project['skin_id'] + '-' + project['version'] + '.mw3pack')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                z.write(path, path.relative_to(stage).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist()) == {'pack.json', *files}
        for name, pin in files.items():
            assert hashlib.sha256(z.read(name)).hexdigest() == pin['sha256']
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(build(args.project, args.output))
