"""Additive named skins; never supply or replace a chassis/stock skin slot."""
import hashlib
from pathlib import Path
import re
import struct

PROFILE = 'prepared-skins-v1'
REGISTRY = 'skins/skins.json'
CAPABILITY = 'additional-mech-skins'
CATALOG_KEY = 'MW34_ADDITIONAL_SKINS'


def select(metadata, host, models, verification=None):
    from prepared_mech_packs import read_json, resolve
    from content_capabilities import require
    selected = {m['id']: m for m in models}
    seen = set()
    result = []
    for root, manifest in metadata:
        payload = manifest.get('native_payload', {})
        if payload.get('profile') != PROFILE:
            continue
        require(host, payload, manifest['id'])
        if (manifest.get('schema_version') != 2 or payload.get('path_base') != 'pack-root'
                or payload.get('registry') != REGISTRY or payload.get('required_formats') != ['BWTEX1']
                or manifest.get('dependencies') or manifest.get('conflicts')
                or manifest.get('provides', {}).get('mechs')):
            raise ValueError('Invalid additive skin pack contract')
        files = manifest.get('files', {})
        if not files or len(files) > 513:
            raise ValueError('Missing or excessive skin file table')
        verified = {}
        paths = {'pack.json'}
        total = 0
        for name, pin in files.items():
            if not isinstance(name, str) or name.casefold() in paths or not isinstance(pin, dict):
                raise ValueError('Colliding or invalid skin file declaration')
            paths.add(name.casefold())
            path = resolve(root, name)
            size = pin.get('bytes')
            if type(size) is not int or size < 0 or size > 256*1024**2:
                raise ValueError('Invalid skin file size')
            total += size
            if total > 1024**3 or path.stat().st_size != size:
                raise ValueError('Skin pack size mismatch')
            expected = pin.get('sha256', '')
            if not re.fullmatch('[0-9a-f]{64}', expected):
                raise ValueError('Invalid skin file hash')
            if verification:
                digest = verification.digest(path, expected)
            else:
                with path.open('rb') as stream:
                    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            if digest != expected:
                raise ValueError('Skin pack integrity failure: ' + name)
            if name != REGISTRY:
                with path.open('rb') as stream:
                    magic = stream.read(8)
                if pin.get('format') != 'BWTEX1' or magic != b'BWTEX1\0\0':
                    raise ValueError('Skin pack contains unsupported payload')
            verified[name] = str(path)
        if REGISTRY not in verified:
            raise ValueError('Undeclared skin registry')
        registry = read_json(Path(verified[REGISTRY]))
        skins = registry.get('skins')
        if (registry.get('schema_version') != 2 or registry.get('payload_profile') != PROFILE
                or not isinstance(skins, list) or not 1 <= len(skins) <= 128):
            raise ValueError('Invalid skin registry')
        used = {REGISTRY}
        for skin in skins:
            if not isinstance(skin, dict):
                raise ValueError('Invalid skin record')
            ident, chassis, name = skin.get('id'), skin.get('chassis'), skin.get('name')
            if (not isinstance(ident, str) or not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,127}:[a-z0-9][a-z0-9._-]{0,63}', ident)
                    or not ident.startswith(manifest['id'] + ':') or ident in seen):
                raise ValueError('Duplicate or invalid namespaced skin ID')
            if (not isinstance(name, str) or not 1 <= len(name) <= 64
                    or any(not 32 <= ord(c) <= 126 for c in name)):
                raise ValueError('Invalid skin display name')
            if not isinstance(chassis, str) or chassis not in selected:
                raise ValueError(f"Skin '{name}' needs an enabled compatible {chassis} model pack")
            model = selected[chassis]
            hashes, textures = skin.get('mesh_sha256', {}), skin.get('textures', {})
            if (not isinstance(hashes, dict) or not isinstance(textures, dict)
                    or set(hashes) != {'close', 'distance'} or set(textures) != {'close', 'distance'}):
                raise ValueError('Skin requires both mesh identities and both LOD textures')
            prefix = 'MW34_' + chassis.upper()
            for lod, key in [('close', prefix + ('_TEST' if chassis == 'bushwacker' else '_MESH')),
                             ('distance', prefix + '_LOD1_MESH')]:
                mesh = model['visuals'][lod]['mesh'] if 'visuals' in model else model['environment'][key]
                with Path(mesh).open('rb') as stream:
                    actual = hashlib.file_digest(stream, 'sha256').hexdigest()
                if hashes[lod] != actual:
                    raise ValueError(f"Skin '{name}' does not match the enabled {chassis} {lod} mesh")
                if not isinstance(textures[lod], str) or textures[lod] not in verified or textures[lod] == REGISTRY:
                    raise ValueError('Undeclared skin texture')
                used.add(textures[lod])
            result.append(dict(id=ident, name=name, chassis=chassis,
                               close=verified[textures['close']], distance=verified[textures['distance']]))
            seen.add(ident)
        if used != set(files):
            raise ValueError('Unused skin pack member')
    if len(result) > 128:
        raise ValueError('Too many additional skins')
    for skin in result:
        selected[skin['chassis']].setdefault('additional_skins', []).append(skin)
    return result


def write_catalog(models, output):
    """Length-prefixed UTF-8 records; paths are coordinator-resolved, never code."""
    skins = sorted((s for m in models for s in m.get('additional_skins', [])), key=lambda s: s['id'])
    if not skins:
        return {}
    blob = bytearray(b'BWSKIN1\0' + struct.pack('<I', len(skins)))
    for skin in skins:
        for key in ('id', 'name', 'chassis', 'close', 'distance'):
            value = skin[key].encode('utf-8')
            if not 0 < len(value) <= 4096:
                raise ValueError('Invalid skin catalog string')
            blob += struct.pack('<I', len(value)) + value
    from native_assets import write_atomic
    output = Path(output) / 'additional-skins.bin'
    write_atomic(output, blob)
    return {CATALOG_KEY: str(output.resolve())}
