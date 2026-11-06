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

HEADLIGHT_CAPABILITY = 'mech-headlights'
HEADLIGHT_FIELDS = {'id', 'space', 'attachment', 'position', 'direction', 'color',
                    'intensity', 'range', 'inner_angle', 'outer_angle'}


def validate_headlights(lights, donor=False):
    """Return normalized copies; pack coordinates are never modified in place."""
    if not isinstance(lights, list) or len(lights) > 8:
        raise ValueError('Expected 0..8 authored headlights')
    ids, result = set(), []
    for light in lights:
        if not isinstance(light, dict) or set(light) != HEADLIGHT_FIELDS:
            raise ValueError('Invalid headlight fields')
        if (not isinstance(light['id'], str)
                or not re.fullmatch(r'[a-z0-9_-]{1,31}', light['id']) or light['id'] in ids
                or light['space'] not in ('guest_node', 'donor_bone')
                or (light['space'] == 'donor_bone' and not donor)
                or not isinstance(light['attachment'], str)
                or not re.fullmatch(r'[A-Za-z0-9_.-]{1,31}', light['attachment'])):
            raise ValueError('Invalid headlight identity or attachment')
        def number(value, low, high):
            return type(value) in (int, float) and low <= value <= high and math.isfinite(value)
        for field, low, high in [('position', -100, 100), ('direction', -1e30, 1e30), ('color', 0, 1)]:
            vector = light[field]
            if not isinstance(vector, list) or len(vector) != 3 or not all(number(v, low, high) for v in vector):
                raise ValueError('Invalid headlight ' + field)
        for field, low, high in [('intensity', 0, 8), ('range', 1, 256), ('inner_angle', 0, 89), ('outer_angle', 0, 89)]:
            if not number(light[field], low, high):
                raise ValueError('Invalid headlight ' + field)
        length = math.hypot(*light['direction'])
        if length == 0 or struct.unpack('<f', struct.pack('<f', light['inner_angle']))[0] >= struct.unpack('<f', struct.pack('<f', light['outer_angle']))[0]:
            raise ValueError('Invalid headlight direction or cone')
        ids.add(light['id'])
        result.append(dict(light, direction=[v / length for v in light['direction']]))
    return result


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
                or set(record) - {'id', 'name', 'resource', 'metadata_template', 'visuals', 'base_skin_name', 'sockets', 'headlights', 'owned_visuals'}):
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
        if 'headlights' in record:
            record = dict(record, headlights=validate_headlights(record['headlights'], 'visuals' in record))
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
    with_weapon_visuals = any(r.get('owned_visuals', {}).get('weapon_attachments') for r in validated)
    with_damage = with_weapon_visuals or any(isinstance(r.get('owned_visuals'), dict) and 'arm_damage' in r['owned_visuals'] for r in validated)
    with_owned = any('owned_visuals' in r for r in validated)
    with_headlights = with_owned or any(r.get('headlights') for r in validated)
    with_sockets = with_headlights or any('sockets' in r for r in validated)
    with_names = with_sockets or any('base_skin_name' in r for r in validated)
    with_visuals = with_names or any('visuals' in r for r in validated)
    blob = bytearray((b'MWCHAS8\0' if with_weapon_visuals else b'MWCHAS7\0' if with_damage else b'MWCHAS6\0' if with_owned else b'MWCHAS5\0' if with_headlights else b'MWCHAS4\0' if with_sockets else b'MWCHAS3\0' if with_names else b'MWCHAS2\0' if with_visuals else b'MWCHAS1\0') + struct.pack('<I', len(validated)))
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
        if with_headlights:
            lights = record.get('headlights', [])
            blob.extend(struct.pack('<I', len(lights)))
            for light in lights:
                # MWCHAS5: three u32-length ASCII strings, then 13 IEEE754
                # binary32 values, all little endian. Counts are bounded above.
                for field in ('id', 'space', 'attachment'):
                    raw = light[field].encode('ascii')
                    blob.extend(struct.pack('<I', len(raw)) + raw)
                blob.extend(struct.pack('<13f', *light['position'], *light['direction'],
                                        *light['color'], light['intensity'], light['range'],
                                        light['inner_angle'], light['outer_angle']))
        if with_owned:
            owned = record.get('owned_visuals')
            blob.extend(struct.pack('<I', int(owned is not None)))
            if owned is not None:
                if 'visuals' in record or set(owned) - {'arm_damage', 'weapon_attachments'} != {'rosters', 'cockpit', 'meshes', 'textures', 'skin_textures'}:
                    raise ValueError('Invalid owned visual catalog fields')
                def text(value):
                    if not isinstance(value, str) or not 0 < len(value.encode('utf-8')) <= 4096 or '\0' in value:
                        raise ValueError('Invalid owned catalog text')
                    raw = value.encode('utf-8')
                    blob.extend(struct.pack('<I', len(raw)) + raw)
                def roster(rows):
                    if not isinstance(rows, list) or len(rows) > 256:
                        raise ValueError('Invalid owned mesh roster')
                    blob.extend(struct.pack('<I', len(rows)))
                    names = set()
                    for row in rows:
                        if (not isinstance(row, dict) or set(row) != {'name', 'owner', 'vertices'}
                                or not all(isinstance(row[k], str) and re.fullmatch('[A-Za-z0-9_.-]{1,31}', row[k]) for k in ('name', 'owner'))
                                or row['name'] in names or type(row['vertices']) is not int
                                or not 1 <= row['vertices'] <= 100000):
                            raise ValueError('Invalid owned mesh roster entry')
                        names.add(row['name']);text(row['name']);text(row['owner'])
                        blob.extend(struct.pack('<I', row['vertices']))
                for lod in ('close', 'distance'):
                    text(owned['meshes'][lod]);text(owned['textures'][lod])
                    if not owned['rosters'][lod]:
                        raise ValueError('Empty owned source roster')
                    roster(owned['rosters'][lod])
                roster(owned['cockpit'])
                skins = owned['skin_textures']
                if not isinstance(skins, dict) or len(skins) > 4096:
                    raise ValueError('Invalid owned source skin map')
                blob.extend(struct.pack('<I', len(skins)))
                for name, skin in sorted(skins.items()):
                    if not re.fullmatch('[A-Za-z0-9_.-]{1,31}', name) or type(skin) is not int or not 0 <= skin <= 7:
                        raise ValueError('Invalid owned source skin binding')
                    text(name);blob.extend(struct.pack('<I', skin))
                if with_damage:
                    plans = owned.get('arm_damage', {'close': [], 'distance': []})
                    if not isinstance(plans, dict) or set(plans) != {'close', 'distance'}:
                        raise ValueError('Invalid owned arm damage LODs')
                    for lod in ('close', 'distance'):
                        rows = plans[lod]
                        if not isinstance(rows, list) or len(rows) > 2:
                            raise ValueError('Invalid owned arm damage count')
                        blob.extend(struct.pack('<I', len(rows)))
                        arms, removed = set(), set()
                        source = {r['name'] for r in owned['rosters'][lod]}
                        for plan in rows:
                            if (not isinstance(plan, dict) or set(plan) != {'arm', 'parent', 'removed'}
                                    or plan['arm'] not in ('larm', 'rarm') or plan['arm'] in arms
                                    or not isinstance(plan['parent'], str)
                                    or not re.fullmatch('[A-Za-z0-9_.-]{1,31}', plan['parent'])
                                    or not isinstance(plan['removed'], list) or not 1 <= len(plan['removed']) <= 8
                                    or any(not isinstance(n, str) or n not in source or n in removed for n in plan['removed'])
                                    or len(set(plan['removed'])) != len(plan['removed'])):
                                raise ValueError('Invalid owned arm damage plan')
                            arms.add(plan['arm']);removed.update(plan['removed'])
                            text(plan['arm']);text(plan['parent'])
                            blob.extend(struct.pack('<I', len(plan['removed'])))
                            for name in plan['removed']:text(name)
                if with_weapon_visuals:
                    table = owned.get('weapon_attachments', {})
                    keys = None
                    for lod in ('close', 'distance'):
                        part = table.get(lod, {'mesh_identity': '0000000000000000', 'records': []})
                        rows = part['records']
                        if not isinstance(rows, list) or len(rows) > 64:
                            raise ValueError('Invalid weapon visual catalog count')
                        identity = int(part['mesh_identity'], 16)
                        if bool(identity) != bool(rows):
                            raise ValueError('Invalid empty weapon visual identity')
                        current_keys = [(r['source_control'], r['weapon']) for r in rows]
                        if len(set(current_keys)) != len(rows) or keys is not None and keys != current_keys:
                            raise ValueError('Ambiguous weapon visual catalog keys')
                        keys = current_keys
                        blob.extend(struct.pack('<QI', identity, len(rows)))
                        for row in rows:
                            for field in ('source_control', 'weapon', 'bone'):
                                value = row[field]
                                if not isinstance(value, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,31}', value):
                                    raise ValueError('Invalid weapon visual catalog name')
                                text(value)
                            position = row['position']
                            if len(position) != 3 or any(type(v) not in (int, float) or not math.isfinite(v) or abs(v)>100 for v in position):
                                raise ValueError('Invalid weapon visual catalog position')
                            if row['source_control'] not in ('lhand', 'rhand') or row['bone'] != ('Forearm_Left' if row['source_control']=='lhand' else 'Forearm_Right'):
                                raise ValueError('Invalid weapon visual catalog control')
                            blob.extend(struct.pack('<3d', *position))
    return bytes(blob)
