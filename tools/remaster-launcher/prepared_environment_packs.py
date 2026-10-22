"""Resolve installed environment packs into private native launch resources.

Operation banks are selected as a whole, first enabled pack wins per region.
Content never supplies process flags or commands. Exact host identity admits
the compiled fixture catalog; installing a pack cannot authorize a newer host.
"""
import hashlib
import json
import re
import struct
from pathlib import Path

from prepared_mech_packs import canonical_pack_root, read_json, resolve
from normal_materials import read_surface_bindings, pack_surface_bindings

PROFILE = 'prepared-environment-v1'
REGISTRY = 'environment/environment.json'
REGIONS = {'training': {'t1'}, 'operation1': {'c1'}, 'operation2': {'c2'},
           'operation3': {'c3'}, 'operation4': {'c4', 'c4b'}, 'shared-mechs': set()}
RESOURCE_KEYS = {'MW34_REMASTER_BANKS', 'MW34_WORLD_NORMALS', 'MW34_SURFACE_NORMALS',
                 'MW34_EFFECT_LIGHT_CATALOG', 'MW34_WATER_NORMALS',
                 'MW34_SURF_NORMALS', 'MW34_CLOUD_NORMALS', 'MW34_MISSION_ENVIRONMENTS'}
MAX_BYTES = 16 * 1024**3
REVIEWED_HOST_ADMISSIONS = {
'9c578de615168724fb40664ad03b870b34b68169802cd0fae371a6f2c2d666b6': {'0dec8fa9dc1671b16744b406cea2099dd5801613c037e42dbae9bd22d5fc1d93', 'd0a79be7a0e1fe30b22ca5005fa9d3c4ff133380833f80dd6d3d751766681a0d', 'b1a3edb7ed84daf399fa4bb5f3ed246a9d718470e5f6b0fac4fc16e4961af1b6'},  # Same sky correction, guarded host FP scope.
    'a99afd84ddb8fb2375197d0406186286ce8d8775399cbf75373c5a07bcd8482c': {
        '8194028a835c85e46b0963864ea04acfe400749671b1eb7f28ae63a51a2f5532',
        '9c578de615168724fb40664ad03b870b34b68169802cd0fae371a6f2c2d666b6',  # Sky backdrop classification; resource readers unchanged.
        '0dec8fa9dc1671b16744b406cea2099dd5801613c037e42dbae9bd22d5fc1d93',  # Sky backdrop classification; resource readers unchanged.
        'd0a79be7a0e1fe30b22ca5005fa9d3c4ff133380833f80dd6d3d751766681a0d',  # Sky backdrop classification; resource readers unchanged.
        'b1a3edb7ed84daf399fa4bb5f3ed246a9d718470e5f6b0fac4fc16e4961af1b6',  # Sky backdrop classification; resource readers unchanged.
        'e293b3a5f79d3d85f7c04ddcd9f857046e66583f6c7d18255e3ceb43c2cfc46c',
        'c922df9f8663315972d14376ab5ac622cf82316d8ecf78a9c5eda7ecdca9ae95',  # Rebuilt lower-horizon split host; readers unchanged.
    },
    # Lighting-capable 1.1 packs: only AVI routing/codec location changed.
    '0d3d920f6b560ddcd92fbeeb4034d59430ddd46a19b75269255fc8ec83fe12ef': {
        # All-skin host: fixture, environment and normal readers byte-identical.
        'a99afd84ddb8fb2375197d0406186286ce8d8775399cbf75373c5a07bcd8482c',
        '8194028a835c85e46b0963864ea04acfe400749671b1eb7f28ae63a51a2f5532',
        '9c578de615168724fb40664ad03b870b34b68169802cd0fae371a6f2c2d666b6',  # Sky backdrop classification; resource readers unchanged.
        '0dec8fa9dc1671b16744b406cea2099dd5801613c037e42dbae9bd22d5fc1d93',  # Sky backdrop classification; resource readers unchanged.
        'd0a79be7a0e1fe30b22ca5005fa9d3c4ff133380833f80dd6d3d751766681a0d',  # Sky backdrop classification; resource readers unchanged.
        'b1a3edb7ed84daf399fa4bb5f3ed246a9d718470e5f6b0fac4fc16e4961af1b6',  # Sky backdrop classification; resource readers unchanged.
        'e293b3a5f79d3d85f7c04ddcd9f857046e66583f6c7d18255e3ceb43c2cfc46c',
        'c922df9f8663315972d14376ab5ac622cf82316d8ecf78a9c5eda7ecdca9ae95',  # Rebuilt lower-horizon split host; readers unchanged.
        '33bfcf1d6c2b7454d6a21aee1421c34cadbc7b1be5783485b70499b5bc0e8afa',
        '9fd17ba2459ac2d349adda33c0c84d41772bbd2ec7c0e2a620242c696526bb83',
        'c1afedadd8ed9e13a956db917a1a5335a6581fac01374b367969d4e985852115'
    },
    # USER32 keyboard services only. Fixture catalogs and all resource readers are byte-identical.
    '7e1c939111b219f32bd765e25d840c6196c1d9c5b7cfb073ac21b949aedfa5d9': {
        'a99afd84ddb8fb2375197d0406186286ce8d8775399cbf75373c5a07bcd8482c',
        '8194028a835c85e46b0963864ea04acfe400749671b1eb7f28ae63a51a2f5532',
        '9c578de615168724fb40664ad03b870b34b68169802cd0fae371a6f2c2d666b6',  # Sky backdrop classification; resource readers unchanged.
        '0dec8fa9dc1671b16744b406cea2099dd5801613c037e42dbae9bd22d5fc1d93',  # Sky backdrop classification; resource readers unchanged.
        'd0a79be7a0e1fe30b22ca5005fa9d3c4ff133380833f80dd6d3d751766681a0d',  # Sky backdrop classification; resource readers unchanged.
        'b1a3edb7ed84daf399fa4bb5f3ed246a9d718470e5f6b0fac4fc16e4961af1b6',  # Sky backdrop classification; resource readers unchanged.
        'e293b3a5f79d3d85f7c04ddcd9f857046e66583f6c7d18255e3ceb43c2cfc46c',
        'c922df9f8663315972d14376ab5ac622cf82316d8ecf78a9c5eda7ecdca9ae95',  # Rebuilt lower-horizon split host; readers unchanged.
        '3f34ec34ac6fb6f729a8c544b387b79b81495e7c0f250b566ef25008772b4fa2',
        # Optional mission presentation reader; fixture definitions/resource readers unchanged.
        '0d3d920f6b560ddcd92fbeeb4034d59430ddd46a19b75269255fc8ec83fe12ef',
        # AVI read-path routing only; environment and fixture readers unchanged.
        '33bfcf1d6c2b7454d6a21aee1421c34cadbc7b1be5783485b70499b5bc0e8afa',
        # Explicit private codec image path; fixture/lighting readers remain identical.
        '9fd17ba2459ac2d349adda33c0c84d41772bbd2ec7c0e2a620242c696526bb83',
        # Explicit installed original providers; all environment readers unchanged.
        'c1afedadd8ed9e13a956db917a1a5335a6581fac01374b367969d4e985852115'
    }
}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encode_normal_pages(entries, *, world=False):
    """Group identical images before paging; obey the native page/count budgets."""
    groups={}
    for key,value in entries: groups.setdefault(value,[]).append(key)
    batch=[]; images=set(); size=0; count=0; total=0
    limit=8*1024**2 if world else 128*1024**2
    for value,keys in groups.items():
        image_bytes=0 if value is None else len(value[2])
        if image_bytes>limit: raise ValueError('Normal image exceeds page budget')
        for key in sorted(keys):
            extra=0 if value in images else image_bytes
            if batch and (len(batch)>=256 or len(images | {value})>64 or size+extra>limit):
                data=pack_surface_bindings(batch);count+=1;total+=len(data)
                if dict(read_surface_bindings(data))!=dict(batch):raise ValueError('Normal round-trip mismatch')
                yield data
                batch=[];images=set();size=0;extra=image_bytes
            batch.append((key,value));images.add(value);size+=extra
    if batch:
        data=pack_surface_bindings(batch);count+=1;total+=len(data)
        if dict(read_surface_bindings(data))!=dict(batch):raise ValueError('Normal round-trip mismatch')
        yield data
    if count>(256 if world else 16) or total>512*1024**2:
        raise ValueError('Normal catalog exceeds native count/byte budget')


def select(roots, host, verification=None):
    """Verify complete installed file closure without writing launch artifacts."""
    if not isinstance(roots, list) or len(roots) > 32 or any(not isinstance(x,str) for x in roots):
        raise ValueError('Invalid environment pack roots')
    selected = {}; ids = set()
    for directory in roots:
        root = canonical_pack_root(directory); manifest = read_json(root/'pack.json')
        ident = manifest.get('id','')
        if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,127}',ident) or ident in ids:
            raise ValueError('Invalid or duplicate environment pack ID')
        ids.add(ident); payload = manifest.get('native_payload',{})
        if (manifest.get('schema_version') != 2 or payload.get('profile') != PROFILE or
            payload.get('registry') != REGISTRY or payload.get('path_base') != 'pack-root'):
            raise ValueError('Unsupported environment pack contract')
        if manifest.get('dependencies') or manifest.get('conflicts'):
            raise ValueError('Environment pack dependencies/conflicts are unsupported')
        actual = host.get('executable_sha256','').lower()
        reference = payload.get('reference_host_sha256')
        if not re.fullmatch('[0-9a-f]{64}',actual) or (
            actual != reference and actual not in REVIEWED_HOST_ADMISSIONS.get(reference, set())
        ):
            raise ValueError('Environment pack requires its explicitly matched fixture-capable host')
        formats = {'ZBD-texture-v1','BWSNR2','MWFX1','MW34SNA1','MW34SNP1','MW34-lighting-v1'}
        if not set(payload.get('required_formats',[])).issubset(formats):
            raise ValueError('Unsupported environment resource format')
        files = manifest.get('files',{}); total = 0; seen = {'pack.json'}
        if not files or len(files)>10000: raise ValueError('Invalid environment file table')
        paths = {}
        for name,pin in files.items():
            path = resolve(root,name); size = pin.get('bytes'); digest = pin.get('sha256','')
            if name.casefold() in seen or type(size) is not int or not 0<=size<=MAX_BYTES:
                raise ValueError('Invalid environment member')
            seen.add(name.casefold()); total += size
            if total>MAX_BYTES or not re.fullmatch('[0-9a-f]{64}',digest) or not path.is_file() or path.stat().st_size!=size:
                raise ValueError('Environment member integrity failure: '+name)
            actual_digest = verification.digest(path,digest) if verification is not None else sha(path)
            if actual_digest != digest:
                raise ValueError('Environment member integrity failure: '+name)
            fmt=pin.get('format')
            if fmt:
                with path.open('rb') as stream: magic=stream.read(24)
                expected={'BWSNR2':b'BWSNR2\0\0','MWFX1':b'MWFX1\0\0\0','MW34SNA1':b'MW34SNA1','MW34SNP1':b'MW34SNP1'}
                if fmt=='ZBD-texture-v1':
                    if len(magic)!=24 or struct.unpack('<3I',magic[:12])!=(0,1,0): raise ValueError('Invalid texture bank')
                elif fmt != 'MW34-lighting-v1' and (fmt not in expected or not magic.startswith(expected[fmt])): raise ValueError('Mislabeled environment payload')
            paths[name]=str(path)
        if REGISTRY not in paths: raise ValueError('Undeclared environment registry')
        registry = read_json(Path(paths[REGISTRY])); region = registry.get('operation')
        if registry.get('schema_version')!=2 or registry.get('payload_profile')!=PROFILE or region not in REGIONS:
            raise ValueError('Unsupported environment registry')
        banks=registry.get('banks',{}); expected={f'zbd/{r}/{n}.zbd' for r in REGIONS[region] for n in ['rtexture','rtexture2','rtexture3','texture','texture1','texture2']}
        if region == 'shared-mechs':
            expected = {'zbd/rmechtex.zbd', 'zbd/rmechtex16.zbd'}
        if set(banks)!=expected: raise ValueError('Incomplete or out-of-region bank set')
        references={REGISTRY,*banks.values()}
        if region == 'shared-mechs':
            pages=registry.get('authored',[]); index=registry.get('authored_manifest','')
            if not isinstance(pages,list) or not 0<len(pages)<=16:
                raise ValueError('Invalid shared mech normal pages')
            references.update(pages);references.add(index)
            if references!=set(paths) or any(files[p].get('format')!='ZBD-texture-v1' for p in banks.values()):
                raise ValueError('Invalid shared mech resource closure')
            if files[index].get('format')!='MW34SNA1' or any(files[p].get('format')!='BWSNR2' for p in pages):
                raise ValueError('Invalid shared mech normal formats')
            if Path(paths[index]).read_text().splitlines()!=['MW34SNA1',*[str(Path(p).relative_to('environment')).replace('\\','/') for p in pages]]:
                raise ValueError('Shared mech normal manifest differs from declared pages')
            if set(registry)!={'schema_version','payload_profile','operation','banks','authored','authored_manifest'}:
                raise ValueError('Unexpected shared mech registry fields')
            selected.setdefault(region,dict(root=str(root),registry=registry,paths=paths,files=files,lighting=None))
            continue
        lighting = None
        if 'lighting' in registry:
            from mission_lighting import validate
            if 1 not in host.get('mission_environment_versions', []):
                raise ValueError('This host cannot load mission lighting packs; update the native runtime')
            name = registry['lighting']
            if name not in paths or files[name].get('format') != 'MW34-lighting-v1':
                raise ValueError('Undeclared or mislabeled lighting catalog')
            lighting = validate(read_json(Path(paths[name])), region)
            references.add(name)
        for role in ['authored','world']:
            pages=registry.get(role,[])
            if not isinstance(pages,list) or not 0<len(pages)<=(16 if role=='authored' else 256): raise ValueError('Invalid normal page list')
            references.update(pages)
        for role in ['effects','authored_manifest','world_manifest']:
            references.add(registry.get(role,''))
        detail=registry.get('detail',{})
        if set(detail)!={'water','surf','cloud'}: raise ValueError('Missing surface detail resources')
        references.update(detail.values())
        if references!=set(paths): raise ValueError('Undeclared or unused environment resources')
        expected_formats={**{p:'ZBD-texture-v1' for p in banks.values()},
                          **{p:'BWSNR2' for p in detail.values()},
                          registry['effects']:'MWFX1',registry['authored_manifest']:'MW34SNA1',
                          registry['world_manifest']:'MW34SNP1'}
        if any(files[p].get('format')!=fmt for p,fmt in expected_formats.items()):
            raise ValueError('Incorrect environment resource role/format')
        for role,magic in [('authored','MW34SNA1'),('world','MW34SNP1')]:
            text=Path(paths[registry[role+'_manifest']]).read_text().splitlines()
            page_names=registry[role]
            if text!=[magic,*[str(Path(p).relative_to('environment')).replace('\\','/') for p in page_names]]:
                raise ValueError('Normal manifest differs from declared pages')
            if any(files[p].get('format')!='BWSNR2' for p in page_names): raise ValueError('Invalid normal page declaration')
        selected.setdefault(region,dict(root=str(root),registry=registry,paths=paths,files=files,lighting=lighting))
    common={}
    for pack in selected.values():
        registry=pack['registry']
        if registry['operation']=='shared-mechs': continue
        for role,name in [('effects',registry['effects']),*registry['detail'].items()]:
            digest=pack['files'][name]['sha256']
            if role in common and common[role]!=digest:
                raise ValueError('Conflicting shared environment resource: '+role)
            common[role]=digest
    return selected


def profile_bindings(selected, host):
    """Remove stale development bindings, using installed inputs for plan checks."""
    environment={k:v for k,v in host.get('runtime_environment',{}).items() if k not in RESOURCE_KEYS}
    if not selected:
        environment['MW34_EFFECT_LIGHTS']='0'
        for key in ['MW34_WATER_DETAIL','MW34_SURF_DETAIL','MW34_CLOUD_DETAIL']:
            environment[key]='0'
        return environment
    first=next((p for p in selected.values() if 'effects' in p['registry']),None)
    if first is None:
        environment=profile_bindings({},host)
        shared=selected['shared-mechs']
        environment['MW34_SURFACE_NORMALS']=shared['paths'][shared['registry']['authored_manifest']]
        return environment
    registry=first['registry']; paths=first['paths']
    environment.update(MW34_WORLD_NORMALS=paths[registry['world_manifest']],
                       MW34_SURFACE_NORMALS=paths[registry['authored_manifest']],
                       MW34_EFFECT_LIGHT_CATALOG=paths[registry['effects']])
    for role,name in registry['detail'].items(): environment['MW34_'+role.upper()+'_NORMALS']=paths[name]
    return environment


def detail_metadata(selected):
    """Pins for the verified installed resources, independent of development files."""
    first=next((p for p in selected.values() if 'detail' in p['registry']),None)
    if first is None: return {}
    return {role:dict(path=first['paths'][name],
                      sha256=first['files'][name]['sha256'],
                      bytes=first['files'][name]['bytes'])
            for role,name in first['registry']['detail'].items()}


def prepare(selected, host, output):
    """Write fresh per-launch bank and merged normal indices; never edit packs."""
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    environment=profile_bindings(selected,host); bankmap={}; catalogs={'authored':{},'world':{}}
    for pack in selected.values():
        registry=pack['registry'];paths=pack['paths']
        for key,name in registry['banks'].items(): bankmap[key]=paths[name]
        for role in catalogs:
            for name in registry.get(role,[]):
                for key,value in read_surface_bindings(Path(paths[name]).read_bytes()):
                    if key in catalogs[role] and catalogs[role][key]!=value:
                        raise ValueError('Conflicting installed normal images')
                    catalogs[role][key]=value
    data=bytearray(b'MWBANK1\0'+struct.pack('<I',len(bankmap)))
    for key,path in sorted(bankmap.items()):
        a=key.encode();b=path.encode();data+=struct.pack('<II',len(a),len(b))+a+b
    if bankmap:
        (output/'texture-banks.bin').write_bytes(data)
        environment['MW34_REMASTER_BANKS']=str((output/'texture-banks.bin').resolve())
    for role,entries in catalogs.items():
        names=[];items=sorted(entries.items());total=0
        for index,data in enumerate(encode_normal_pages(items,world=role=='world')):
            path=output/f'{role}-{index}.bin';total+=len(data);path.write_bytes(data);names.append(path.name)
        if role=='authored' and total>host.get('authored_normal_catalog_budget_bytes',536870912):
            raise ValueError('Installed authored normal catalog exceeds native budget')
        if not names: continue
        path=output/(role+'.txt');path.write_text(('MW34SNA1' if role=='authored' else 'MW34SNP1')+'\n'+'\n'.join(names)+'\n')
        environment['MW34_SURFACE_NORMALS' if role=='authored' else 'MW34_WORLD_NORMALS']=str(path.resolve())
    from mission_lighting import prepare as prepare_lighting
    environment.update(prepare_lighting(selected, output))
    return environment
