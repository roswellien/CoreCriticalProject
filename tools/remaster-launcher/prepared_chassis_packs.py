"""Discover data-only additional chassis and compose private original resources.

Pack definitions contain authored overrides, not an original reader archive.
Compilation uses the player's original template and the original native parser.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
import uuid

from chassis_catalog import STOCK, encode_catalog
from reader_archive import _directory, add_members
from zrd_document import decode, encode

PROFILE = 'additional-chassis-v1'
REGISTRY = 'chassis/chassis.json'
CAPABILITY = 'additional-mech-chassis'
CATALOG_KEY = 'MW34_ADDITIONAL_CHASSIS'
FIELDS = {'id', 'name', 'metadata_template', 'controller', 'definition', 'meshes', 'textures'}


def authored(document):
    if (not isinstance(document, dict) or set(document) != {'schema_version', 'template', 'fields'}
            or type(document['schema_version']) is not int or document['schema_version'] != 1
            or not isinstance(document['template'], str) or document['template'] not in STOCK
            or document['template'] == 'elemental' or not isinstance(document['fields'], dict)):
        raise ValueError('Invalid authored chassis definition')
    if 'skins' in document['fields']:
        raise ValueError('Use additional skin packs for named appearances')


def definition(document, original):
    """Compile editable JSON overrides, preserving the template's typed fields."""
    authored(document)
    tree = decode(original)
    if not isinstance(tree, list) or len(tree) != 1 or not isinstance(tree[0], list):
        raise ValueError('Unsupported original definition root')
    fields = tree[0]
    if 'skins' in document['fields']:
        raise ValueError('Use additional skin packs for named appearances')
    skin_position = fields.index('skins') + 1
    fields[skin_position] = fields[skin_position][:2]

    def prior(items, key):
        if isinstance(items, list) and key in items:
            position = items.index(key)
            if position + 1 < len(items):
                return items[position + 1]
        return None

    def convert(value, old):
        if isinstance(value, dict):
            result = []
            for key, child in value.items():
                result.extend([key, convert(child, prior(old, key))])
            return result
        if isinstance(value, list):
            return [convert(v, None) if isinstance(v, dict) else
                    ('true' if v else 'false') if type(v) is bool else v for v in value]
        if value is None:
            return None
        if type(value) is bool:
            return ['true' if value else 'false']
        if type(value) in (str, int, float):
            if isinstance(old, list) and len(old) == 1 and type(old[0]) is float:
                if type(value) not in (float, int):
                    raise ValueError('Expected a numeric chassis field')
                value = float(value)
            return [value]
        raise ValueError('Unsupported authored chassis value')

    for key, value in document['fields'].items():
        if key == 'version' or fields.count(key) != 1:
            raise ValueError('Unknown or immutable chassis field: ' + key)
        position = fields.index(key) + 1
        fields[position] = convert(value, fields[position])
    return encode(tree)


def select(metadata, host, verification=None):
    from prepared_mech_packs import read_json, resolve
    from content_capabilities import require
    result, ids = [], set()
    for root, manifest in metadata:
        payload = manifest.get('native_payload', {})
        if payload.get('profile') != PROFILE:
            continue
        require(host, payload, manifest['id'])
        if (manifest.get('schema_version') != 2 or manifest.get('game_id') != 'mw3'
                or payload.get('registry') != REGISTRY or payload.get('path_base') != 'pack-root'
                or payload.get('required_formats') not in (['BWMESH4', 'BWTEX1'], ['BWMESH4', 'BWTEX1', 'MW3ICON1'])
                or manifest.get('dependencies') or manifest.get('conflicts')):
            raise ValueError('Unsupported additional chassis pack contract')
        files = manifest.get('files')
        if not isinstance(files, dict) or not 1 <= len(files) <= 1025:
            raise ValueError('Missing or excessive chassis file table')
        verified, paths, total = {}, {'pack.json'}, 0
        for name, pin in files.items():
            if not isinstance(pin, dict) or name.casefold() in paths:
                raise ValueError('Colliding chassis file declaration')
            paths.add(name.casefold())
            path = resolve(root, name)
            size, digest = pin.get('bytes'), pin.get('sha256', '')
            if (type(size) is not int or not 0 < size <= 256 * 1024**2
                    or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest)):
                raise ValueError('Invalid chassis member pin')
            total += size
            if total > 4 * 1024**3 or path.stat().st_size != size:
                raise ValueError('Chassis pack size mismatch')
            if verification:
                actual = verification.digest(path, digest)
            else:
                with path.open('rb') as stream:
                    actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            if actual != digest:
                raise ValueError('Chassis integrity failure: ' + name)
            fmt = pin.get('format')
            if fmt is not None:
                if fmt not in ('BWMESH4', 'BWTEX1', 'MW3ICON1'):
                    raise ValueError('Unsupported chassis payload format')
                with path.open('rb') as stream:
                    if stream.read(8) != fmt.encode().ljust(8, b'\0'):
                        raise ValueError('Mislabeled chassis payload')
            verified[name] = str(path)
        if REGISTRY not in verified:
            raise ValueError('Undeclared chassis registry')
        registry = read_json(Path(verified[REGISTRY]))
        records = registry.get('chassis')
        if (registry.get('schema_version') != 2 or registry.get('payload_profile') != PROFILE
                or not isinstance(records, list) or not 1 <= len(records) <= 128):
            raise ValueError('Unsupported chassis registry')
        used = {REGISTRY}
        for row in records:
            if not isinstance(row, dict) or not FIELDS <= set(row) or set(row) - FIELDS - {'silhouette', 'base_skin_name', 'sockets'}:
                raise ValueError('Invalid chassis registry fields')
            ident = row['id']
            if not isinstance(ident, str) or not ident.startswith(manifest['id'] + ':') or ident in ids:
                raise ValueError('Duplicate or unowned chassis identity')
            if not isinstance(row['controller'], str) or row['controller'] not in STOCK or row['controller'] == 'elemental':
                raise ValueError('Unsupported chassis controller')
            document_path = row['definition']
            if not isinstance(document_path, str) or document_path not in verified or files[document_path].get('format') is not None:
                raise ValueError('Undeclared authored chassis definition')
            document = read_json(Path(verified[document_path]))
            authored(document)
            if document.get('template') != row['controller']:
                raise ValueError('Definition and visual controller disagree')
            used.add(document_path)
            visual = {'controller': row['controller']}
            for lod in ('close', 'distance'):
                visual[lod] = {}
                for role, fmt in [('meshes', 'BWMESH4'), ('textures', 'BWTEX1')]:
                    if not isinstance(row[role], dict) or set(row[role]) != {'close', 'distance'}:
                        raise ValueError('Chassis requires both LOD bindings')
                    name = row[role][lod]
                    if not isinstance(name, str) or name not in verified or files[name].get('format') != fmt:
                        raise ValueError('Undeclared chassis geometry/material resource')
                    visual[lod]['mesh' if role == 'meshes' else 'textures'] = verified[name]
                    used.add(name)
            record = dict(id=ident, name=row['name'], metadata_template=row['metadata_template'],
                          resource='c' + hashlib.sha256(ident.encode()).hexdigest()[:12], visuals=visual)
            if 'base_skin_name' in row:
                value = row['base_skin_name']
                if (not isinstance(value, str) or not 1 <= len(value) <= 64
                        or any(not 32 <= ord(c) <= 126 for c in value)
                        or payload.get('required_capabilities', {}).get(CAPABILITY, 0) < 2):
                    raise ValueError('Invalid base skin name or missing chassis version 2 requirement')
                record['base_skin_name'] = value
            if 'sockets' in row:
                if payload.get('required_capabilities', {}).get(CAPABILITY, 0) < 2:
                    raise ValueError('Chassis sockets require chassis version 2')
                record['sockets'] = row['sockets']
            encode_catalog([record])  # Shared wire validation; pack cannot supply runtime IDs or commands.
            selected = dict(registration=record, definition=document)
            if 'silhouette' in row:
                from chassis_icons import mask
                name = row['silhouette']
                if (not isinstance(name, str) or name not in verified or files[name].get('format') != 'MW3ICON1'
                        or payload.get('required_capabilities', {}).get(CAPABILITY, 0) < 2
                        or 'MW3ICON1' not in payload['required_formats']):
                    raise ValueError('Undeclared silhouette or missing chassis version 2 requirement')
                mask(Path(verified[name]).read_bytes())
                selected['silhouette'] = verified[name]; used.add(name)
            result.append(selected)
            ids.add(ident)
        if used != set(files) or set(manifest.get('provides', {}).get('mechs', [])) != {r['id'] for r in records}:
            raise ValueError('Chassis pack declarations differ from its resources')
    if len(result) > 128:
        raise ValueError('Too many additional chassis')
    return sorted(result, key=lambda item: item['registration']['id'])


def _banks(path):
    if not path:
        return {}
    data = Path(path).read_bytes()
    if len(data) < 12 or len(data) > 1024**2 or data[:8] != b'MWBANK1\0':
        raise ValueError('Invalid inherited resource map')
    count = struct.unpack_from('<I', data, 8)[0]
    if not 1 <= count <= 256:
        raise ValueError('Invalid inherited resource count')
    position, result = 12, {}
    for _ in range(count):
        if position + 8 > len(data):
            raise ValueError('Truncated resource map')
        a, b = struct.unpack_from('<II', data, position); position += 8
        if not a or not b or a > 1024 or b > 4096 or position + a + b > len(data):
            raise ValueError('Invalid resource map lengths')
        key = data[position:position + a].decode(); position += a
        value = data[position:position + b].decode(); position += b
        if (key in result or not key.startswith('zbd/') or '..' in key
                or '\0' in key + value or not Path(value).is_file()):
            raise ValueError('Invalid inherited resource path')
        result[key] = value
    if position != len(data):
        raise ValueError('Trailing resource map data')
    return result


def prepare(records, game_exe, output, environment):
    if not records:
        return {}
    output = Path(output) / 'chassis' / uuid.uuid4().hex
    output.mkdir(parents=True, exist_ok=False)
    banks = _banks(environment.get('MW34_REMASTER_BANKS'))
    sources = {}
    for archive in ('reader.zbd', 'mechlib.zbd'):
        path = Path(banks.get('zbd/' + archive, Path(game_exe).resolve().parent / 'zbd' / archive))
        blob = path.read_bytes(); _, directory = _directory(blob)
        sources[archive] = (blob, {name: blob[offset:offset + size] for name, offset, size, _ in directory})
    definitions, models, registrations = {}, {}, []
    for item in records:
        record, document = item['registration'], item['definition']
        controller, resource = document['template'], record['resource']
        original = sources['reader.zbd'][1]['dfn_' + controller + '.zrd']
        encoded = definition(document, original)
        # The metadata getter's original x87 ABI remains authoritative. Require
        # a template with the same declared mass; never silently report another tonnage.
        metadata = decode(sources['reader.zbd'][1]['dfn_' + record['metadata_template'] + '.zrd'])[0]
        authored = decode(encoded)[0]
        for key in ('max_mass', 'weight_class', 'clan'):
            if key in authored or key in metadata:
                if key not in authored or key not in metadata or authored[authored.index(key) + 1] != metadata[metadata.index(key) + 1]:
                    raise ValueError('Chassis mass/class/technology needs a matching metadata template: ' + key)
        definitions['dfn_' + resource + '.zrd'] = (encoded, 'dfn_' + controller + '.zrd')
        for suffix in ('', '_1', '_hud'):
            old, new = 'mech_' + controller + suffix + '.flt', 'mech_' + resource + suffix + '.flt'
            data = bytearray(sources['mechlib.zbd'][1][old])
            if data[:32].split(b'\0')[0].decode('ascii') != old or len(new) >= 32:
                raise ValueError('Unsupported original model resource header')
            data[:32] = new.encode().ljust(32, b'\0')
            if suffix != '_hud':
                if data[352:384].split(b'\0')[0].decode('ascii') != controller:
                    raise ValueError('Unsupported original controller root')
                data[352:384] = resource.encode().ljust(32, b'\0')
            models[new] = (bytes(data), old)
        registrations.append(record)
    for archive, additions in [('reader.zbd', definitions), ('mechlib.zbd', models)]:
        path = output / archive
        path.write_bytes(add_members(sources[archive][0], additions))
        banks['zbd/' + archive] = str(path.resolve())
    silhouettes = {item['registration']['resource']: Path(item['silhouette']).read_bytes()
                   for item in records if 'silhouette' in item}
    if silhouettes:
        from chassis_icons import append_icons
        source = Path(banks.get('zbd/rimage.zbd', Path(game_exe).resolve().parent / 'zbd/rimage.zbd'))
        path = output / 'rimage.zbd'; path.write_bytes(append_icons(source.read_bytes(), silhouettes))
        banks['zbd/rimage.zbd'] = str(path.resolve())
    catalog = output / 'chassis.bin'; catalog.write_bytes(encode_catalog(registrations))
    if len(banks) > 256:
        raise ValueError('Composed resource map exceeds native limit')
    data = bytearray(b'MWBANK1\0' + struct.pack('<I', len(banks)))
    for key, value in sorted(banks.items()):
        a, b = key.encode(), value.encode(); data += struct.pack('<II', len(a), len(b)) + a + b
    mapping = output / 'banks.bin'; mapping.write_bytes(data)
    return {CATALOG_KEY: str(catalog.resolve()), 'MW34_REMASTER_BANKS': str(mapping.resolve())}
