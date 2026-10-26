"""Private chassis-loader catalog bridge; not yet an installable pack profile.

Authoring uses namespaced stable IDs and stock template names. Numeric runtime
IDs are assigned only by the native reader. The first native boundary inherits
mass, class and technology; arbitrary chassis stats and save integration remain
unsupported and must not be advertised by a runtime capability declaration.
"""
import re
import struct
import math

STOCK = ('annihilator', 'avatar', 'blackhawk', 'bushwacker', 'cauldron',
         'champion', 'daishi', 'elemental', 'firefly', 'madcat', 'orion',
         'owens', 'puma', 'shadowcat', 'strider', 'sunder', 'supernova',
         'thor', 'vulture')


def validate_sockets(sockets):
    if not isinstance(sockets, list) or not 1 <= len(sockets) <= 64:
        raise ValueError('Expected 1..64 authored chassis sockets')
    nodes = set()
    for socket in sockets:
        if (not isinstance(socket, dict) or set(socket) != {'node', 'bone', 'position'}
                or not isinstance(socket['node'], str) or not re.fullmatch(r'firepoint[0-9]{2}', socket['node'])
                or socket['node'] in nodes or not isinstance(socket['bone'], str)
                or not re.fullmatch(r'[A-Za-z0-9_.-]{1,31}', socket['bone'])
                or not isinstance(socket['position'], list) or len(socket['position']) != 3
                or any(type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 100 for v in socket['position'])):
            raise ValueError('Invalid or duplicate authored chassis socket')
        nodes.add(socket['node'])


def encode_catalog(records):
    if not isinstance(records, list) or not 1 <= len(records) <= 128:
        raise ValueError('Expected 1..128 additional chassis')
    ids, resources, validated = set(), set(), []
    for record in records:
        if (not isinstance(record, dict) or not {'id', 'name', 'resource', 'metadata_template'} <= set(record)
                or set(record) - {'id', 'name', 'resource', 'metadata_template', 'visuals', 'base_skin_name', 'sockets'}):
            raise ValueError('Invalid chassis registration fields')
        ident, name, resource, template = (record[k] for k in
                                           ('id', 'name', 'resource', 'metadata_template'))
        if (not isinstance(ident, str) or not re.fullmatch(
                r'[a-z0-9][a-z0-9._-]{0,127}:[a-z0-9][a-z0-9._-]{0,63}', ident)
                or ident in ids):
            raise ValueError('Duplicate or invalid chassis identity')
        if (not isinstance(resource, str) or not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,23}', resource)
                or resource in resources or resource in STOCK or resource == 'notmech'):
            raise ValueError('Colliding or invalid chassis resource')
        if (not isinstance(name, str) or not 1 <= len(name) <= 64
                or any(not 32 <= ord(c) <= 126 for c in name)):
            raise ValueError('Chassis display names require printable ASCII')
        if not isinstance(template, str) or template not in STOCK or template == 'elemental':
            raise ValueError('Unsupported chassis metadata template')
        if 'base_skin_name' in record:
            label = record['base_skin_name']
            if (not isinstance(label, str) or not 1 <= len(label) <= 64
                    or any(not 32 <= ord(c) <= 126 for c in label)):
                raise ValueError('Base skin names require 1..64 printable ASCII characters')
        if 'sockets' in record:
            validate_sockets(record['sockets'])
            if 'visuals' not in record:
                raise ValueError('Chassis sockets require a donor visual controller')
        if 'visuals' in record:
            visual = record['visuals']
            if (not isinstance(visual, dict) or set(visual) != {'controller', 'close', 'distance'}
                    or visual['controller'] not in STOCK or visual['controller'] == 'elemental'):
                raise ValueError('Unsupported chassis visual controller')
            for lod in ('close', 'distance'):
                paths = visual[lod]
                if not isinstance(paths, dict) or set(paths) != {'mesh', 'textures'}:
                    raise ValueError('Both LODs require geometry and textures')
                for value in paths.values():
                    if (not isinstance(value, str) or not 0 < len(value.encode('utf-8')) <= 4096
                            or '\0' in value):
                        raise ValueError('Invalid coordinator-resolved visual path')
        ids.add(ident)
        resources.add(resource)
        validated.append(record)
    with_sockets = any('sockets' in r for r in validated)
    with_names = with_sockets or any('base_skin_name' in r for r in validated)
    with_visuals = with_names or any('visuals' in r for r in validated)
    blob = bytearray((b'MWCHAS4\0' if with_sockets else b'MWCHAS3\0' if with_names else b'MWCHAS2\0' if with_visuals else b'MWCHAS1\0') + struct.pack('<I', len(validated)))
    for record in sorted(validated, key=lambda r: r['id']):
        for field in ('id', 'name', 'resource'):
            value = record[field].encode('ascii')
            blob.extend(struct.pack('<I', len(value)) + value)
        blob.extend(struct.pack('<I', STOCK.index(record['metadata_template'])))
        if with_visuals:
            blob.extend(struct.pack('<I', int('visuals' in record)))
            if 'visuals' in record:
                visual = record['visuals']
                values = [visual['controller']]
                for lod in ('close', 'distance'):
                    values.extend(visual[lod][field] for field in ('mesh', 'textures'))
                for value in values:
                    raw = value.encode('utf-8')
                    blob.extend(struct.pack('<I', len(raw)) + raw)
        if with_names:
            raw = record.get('base_skin_name', '').encode('ascii')
            blob.extend(struct.pack('<I', len(raw)) + raw)
        if with_sockets:
            sockets = record.get('sockets', [])
            blob.extend(struct.pack('<I', len(sockets)))
            for socket in sockets:
                for field in ('node', 'bone'):
                    raw = socket[field].encode('ascii')
                    blob.extend(struct.pack('<I', len(raw)) + raw)
                blob.extend(struct.pack('<3d', *socket['position']))
    return bytes(blob)
