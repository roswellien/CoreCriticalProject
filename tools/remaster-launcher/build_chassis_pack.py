"""Build an unsigned additional-mech .mw3pack from a portable authored project."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from prepared_mech_packs import read_json, resolve
from prepared_chassis_packs import PROFILE, REGISTRY, CAPABILITY, select


def build(project_path, output):
    project_path = Path(project_path).resolve()
    project = read_json(project_path)
    if (not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,127}', project.get('pack_id', ''))
            or not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', project.get('version', ''))
            or not isinstance(project.get('chassis'), list) or not 1 <= len(project['chassis']) <= 128):
        raise ValueError('Invalid chassis project identity/version')
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    stage = output / 'pack'; stage.mkdir()
    files, records = {}, []
    legacy_skins = False

    def add(data, fmt=None, extension='.bin'):
        name = 'payload/' + hashlib.sha256(data).hexdigest() + extension
        path = stage / name; path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        files[name] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        if fmt:
            files[name]['format'] = fmt
        return name

    for entry in project['chassis']:
        if 'legacy' in entry:
            from legacy_chassis_resources import resource_paths, load
            row = {key: entry[key] for key in ('id', 'name', 'metadata_template')}
            row['id'] = project['pack_id'] + ':' + row['id']
            source = resolve(project_path.parent, entry['legacy'])
            document = read_json(source)
            def read_legacy(name):
                path = resolve(source.parent, name)
                if not 0 < path.stat().st_size <= 16 * 1024**2:
                    raise ValueError('Legacy project resource exceeds size limit')
                return path.read_bytes()
            load(document, read_legacy)
            legacy_skins = legacy_skins or document['schema_version'] == 2
            for role, name, relative in list(resource_paths(document)):
                payload = add(read_legacy(relative))
                if name is None:
                    document[role] = payload
                else:
                    document[role][name] = payload
            row['legacy'] = add((json.dumps(document, indent=2) + '\n').encode(), extension='.json')
            if 'headlights' in entry:
                row['headlights'] = entry['headlights']
            records.append(row)
            continue
        row = {k: entry[k] for k in ('id', 'name', 'controller', 'metadata_template')}
        row['id'] = project['pack_id'] + ':' + row['id']
        if 'base_skin_name' in entry:
            row['base_skin_name'] = entry['base_skin_name']
        if 'headlights' in entry:
            row['headlights'] = entry['headlights']
        if 'sockets' in entry:
            row['sockets'] = entry['sockets']
        definition = read_json(resolve(project_path.parent, entry['definition']))
        row['definition'] = add((json.dumps(definition, indent=2) + '\n').encode(), extension='.json')
        row.update(meshes={}, textures={})
        if 'silhouette' in entry:
            from chassis_icons import mask
            data = resolve(project_path.parent, entry['silhouette']).read_bytes(); mask(data)
            row['silhouette'] = add(data, 'MW3ICON1')
        for lod in ('close', 'distance'):
            for role, fmt in [('meshes', 'BWMESH4'), ('textures', 'BWTEX1')]:
                path = resolve(project_path.parent, entry[role][lod])
                if path.stat().st_size > 256 * 1024**2:
                    raise ValueError('Chassis project resource exceeds size limit')
                row[role][lod] = add(path.read_bytes(), fmt)
        if 'surface_materials' in entry:
            from surface_materials import FORMAT as SURFACE_FORMAT, MAX_SIDECAR_BYTES
            row['surface_materials'] = {}
            for lod in ('close', 'distance'):
                path = resolve(project_path.parent, entry['surface_materials'][lod])
                if path.stat().st_size > MAX_SIDECAR_BYTES:
                    raise ValueError('Chassis surface-material resource exceeds size limit')
                row['surface_materials'][lod] = add(path.read_bytes(), SURFACE_FORMAT)
        records.append(row)
    registry = dict(schema_version=2, payload_profile=PROFILE, chassis=records)
    data = (json.dumps(registry, indent=2) + '\n').encode()
    (stage / REGISTRY).parent.mkdir(); (stage / REGISTRY).write_bytes(data)
    files[REGISTRY] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    icons = any('silhouette' in row for row in records)
    surface_materials = any('surface_materials' in row for row in records)
    legacy = any('legacy' in row for row in records)
    if legacy and not all('legacy' in row for row in records):
        raise ValueError('Keep legacy and prepared-visual chassis in separate packs')
    headlights = any(row.get('headlights') for row in records)
    version_two = headlights or icons or any('base_skin_name' in row or 'sockets' in row for row in records)
    from surface_materials import CAPABILITY as SURFACE_CAPABILITY, FORMAT as SURFACE_FORMAT
    required_formats = (['MW3LEGACY'] if legacy else
                        ['BWMESH4', 'BWTEX1'] + (['MW3ICON1'] if icons else []) + ([SURFACE_FORMAT] if surface_materials else []))
    manifest = dict(schema_version=2, game_id='mw3', id=project['pack_id'], name=project['name'],
                    version=project['version'], author=project.get('author', 'Community'), category='Mechs',
                    description=project.get('description', 'Additional selectable mechs. Choose in Mech Lab.'),
                    native_payload=dict(profile=PROFILE, registry=REGISTRY, path_base='pack-root',
                                        required_formats=required_formats, required_capabilities={CAPABILITY: 3 if legacy else 2 if version_two else 1}),
                    provides=dict(mechs=[r['id'] for r in records]), files=files)
    if headlights:
        manifest['native_payload']['required_capabilities']['mech-headlights'] = 1
    if surface_materials:
        manifest['native_payload']['required_capabilities'][SURFACE_CAPABILITY] = 1
    from legacy_chassis_skins import CAPABILITY as SKIN_CAPABILITY
    if legacy_skins:
        manifest['native_payload']['required_capabilities'][SKIN_CAPABILITY] = 1
    (stage / 'pack.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    select([(stage, manifest)], {'content_capabilities': {
        CAPABILITY: [1, 2, 3], 'mech-headlights': [1], SKIN_CAPABILITY: [1], SURFACE_CAPABILITY: [1]}})
    archive = output / (project['pack_id'] + '-' + project['version'] + '.mw3pack')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as target:
        for path in sorted(stage.rglob('*')):
            if path.is_file():
                target.write(path, path.relative_to(stage).as_posix())
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(build(args.project, args.output))
