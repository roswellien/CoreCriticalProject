"""Resolve installed environment packs into private native launch resources.

Operation banks are selected as a whole, first enabled pack wins per region.
Content never supplies process flags or commands. Runtime capabilities admit
the resource contracts; installing a pack cannot add a runtime capability.
"""
import hashlib
import json
import re
import struct
from pathlib import Path

from prepared_mech_packs import canonical_pack_root, read_json, resolve
from normal_materials import (
    DecodedSurfaceBudgetExceeded,
    pack_surface_bindings,
    read_surface_bindings,
)
from surface_materials import (
    MAX_IMAGES as MAX_SURFACE_IMAGES,
    MAX_RECORDS as MAX_SURFACE_RECORDS,
    MAX_SIDECAR_BYTES,
    NO_SURFACE_IMAGE,
    NO_SURFACE_MATERIAL,
    read_surface_materials_file,
)

PROFILE = 'prepared-environment-v1'
REGISTRY = 'environment/environment.json'
REGIONS = {'training': {'t1'}, 'operation1': {'c1'}, 'operation2': {'c2'},
           'operation3': {'c3'}, 'operation4': {'c4', 'c4b'}, 'shared-mechs': set()}
RESOURCE_KEYS = {'MW34_REMASTER_BANKS', 'MW34_WORLD_NORMALS', 'MW34_SURFACE_NORMALS',
                 'MW34_EFFECT_LIGHT_CATALOG', 'MW34_WATER_NORMALS',
                 'MW34_SURF_NORMALS', 'MW34_CLOUD_NORMALS', 'MW34_MISSION_ENVIRONMENTS',
                 'MW34_GROUND_SURFACE_MATERIALS', 'MW34_SURFACE_MATERIALS'}
MAX_BYTES = 16 * 1024**3
AUTHORED_CATALOG_BYTES = 1536 * 1024**2
WORLD_CATALOG_BYTES = 4096 * 1024**2
WORLD_PAGE_BYTES = 16 * 1024**2
MERGED_NORMAL_DECODED_BYTES = 240 * 1024**2
REGION_PRIORITY = {'operation1': 0, 'operation2': 1, 'operation3': 2,
                   'operation4': 3, 'training': 4, 'shared-mechs': 5}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def encode_normal_pages(entries, *, world=False):
    """Group identical images before paging; obey the native page/count budgets."""
    groups={}
    for key,value in entries: groups.setdefault(value,[]).append(key)
    batch=[]; images=set(); size=0; count=0; total=0
    limit=128*1024**2

    def emit(page):
        nonlocal count,total
        data=pack_surface_bindings(page,compressed=world)
        if world and len(data)>WORLD_PAGE_BYTES:
            if len(page)<=1: raise ValueError('One normal binding exceeds native page byte budget')
            middle=len(page)//2
            yield from emit(page[:middle]);yield from emit(page[middle:])
            return
        if dict(read_surface_bindings(data))!=dict(page):raise ValueError('Normal round-trip mismatch')
        count+=1;total+=len(data)
        yield data
    for value,keys in groups.items():
        image_bytes=0 if value is None else len(value[2])
        if image_bytes>limit: raise ValueError('Normal image exceeds page budget')
        for key in sorted(keys):
            extra=0 if value in images else image_bytes
            if batch and (len(batch)>=256 or len(images | {value})>64 or size+extra>limit):
                yield from emit(batch)
                batch=[];images=set();size=0;extra=image_bytes
            batch.append((key,value));images.add(value);size+=extra
    if batch:
        yield from emit(batch)
    if count>(256 if world else 16) or total>(WORLD_CATALOG_BYTES if world else AUTHORED_CATALOG_BYTES):
        raise ValueError('Normal catalog exceeds native count/byte budget')


def write_merged_normal_catalog(selected, role, output):
    """Merge installed pages with bounded decoded memory, writing each page immediately."""
    world=role=='world'; page_limit=WORLD_PAGE_BYTES if world else 256*1024**2
    catalog_limit=WORLD_CATALOG_BYTES if world else AUTHORED_CATALOG_BYTES
    decoded_limit=MERGED_NORMAL_DECODED_BYTES
    from normal_codec import encode as encode_normal
    seen_keys={}; batch=[]; images={}; encoded_sizes={}; page_encoded=0
    decoded=0; total=0; names=[]; conflicts=0; pending_checks=[]

    def signatures(entries):
        return [
            (key,None if value is None else
             (value[0],value[1],hashlib.sha256(value[2]).digest()))
            for key,value in entries
        ]

    def page_bytes(entries):
        data=pack_surface_bindings(entries,compressed=world,cache_hashes=False)
        unique_images={value for _,value in entries if value is not None}
        decoded_bytes=sum(len(value[2]) for value in unique_images)
        largest_image=max((len(value[2]) for value in unique_images),default=0)
        decoder_peak=decoded_bytes+2*largest_image if world else decoded_bytes
        if len(data)>page_limit or decoder_peak>decoded_limit:
            if len(entries)<=1:
                raise ValueError('One normal binding exceeds native page or decoded working budget')
            middle=len(entries)//2
            yield from page_bytes(entries[:middle]);yield from page_bytes(entries[middle:])
            return
        yield data,signatures(entries)

    def emit(entries):
        nonlocal total
        for data,expected in page_bytes(entries):
            total+=len(data)
            if total>catalog_limit or len(names)>=(256 if world else 16):
                raise ValueError('Normal catalog exceeds native count/byte budget')
            name=f'{role}-{len(names)}.bin'
            (output/name).write_bytes(data); names.append(name)
            pending_checks.append((output/name,expected))

    def verify_pending():
        while pending_checks:
            path,expected=pending_checks.pop(0)
            actual=read_surface_bindings(
                path.read_bytes(),
                max_decoded_bytes=decoded_limit,
                max_working_bytes=decoded_limit,
                cache_hashes=False,
            )
            actual_signatures=signatures(actual)
            del actual
            if actual_signatures!=expected:
                raise ValueError('Normal page full-pixel roundtrip failed')

    ordered=sorted(selected.items(),key=lambda item:(REGION_PRIORITY.get(item[0],99),item[0]))
    for _region,pack in ordered:
        registry=pack['registry']; paths=pack['paths']
        for name in registry.get(role,[]):
            source_data=Path(paths[name]).read_bytes()
            try:
                entries=read_surface_bindings(
                    source_data,
                    max_decoded_bytes=decoded_limit-decoded,
                    max_working_bytes=decoded_limit,
                    retained_decoded_bytes=decoded,
                    cache_hashes=False,
                )
            except DecodedSurfaceBudgetExceeded:
                if not batch:
                    raise
                emit(batch);batch=[];images={};page_encoded=0;decoded=0
                verify_pending()
                entries=read_surface_bindings(
                    source_data,
                    max_decoded_bytes=decoded_limit,
                    max_working_bytes=decoded_limit,
                    cache_hashes=False,
                )
            page_signatures={}
            for key,value in entries:
                value_id=id(value)
                if value_id not in page_signatures:
                    page_signatures[value_id]=(None if value is None else
                                               (value[0],value[1],hashlib.sha256(value[2]).digest()))
                signature=page_signatures[value_id]
                previous=seen_keys.get(key)
                if key in seen_keys:
                    if previous!=signature:
                        # One exact source identity can be referenced by several
                        # campaigns. Keep the first map in fixed campaign order.
                        conflicts+=1
                    continue
                seen_keys[key]=signature
                image_id=signature
                image_bytes=0 if value is None else len(value[2])
                new_image=value is not None and image_id not in images
                encoded_bytes=0
                if world and new_image:
                    if image_id not in encoded_sizes:
                        encoded_sizes[image_id]=len(encode_normal(value[2]))
                    encoded_bytes=encoded_sizes[image_id]
                projected=(28+56*(len(batch)+1)+56*(len(images)+int(new_image))+
                           page_encoded+encoded_bytes)
                if batch and (
                    len(batch)>=256 or (value is not None and len(images)>=64) or
                    decoded+image_bytes>decoded_limit or
                    (world and projected>page_limit)
                ):
                    emit(batch);batch=[];images={};page_encoded=0;decoded=0
                    new_image=value is not None
                    encoded_bytes=encoded_sizes.get(image_id,0) if world else 0
                    projected=28+56+56*int(new_image)+encoded_bytes
                if world and projected>page_limit:
                    raise ValueError('One normal binding exceeds native page byte budget')
                if new_image:
                    images[image_id]=value;decoded+=image_bytes;page_encoded+=encoded_bytes
                elif value is not None:
                    value=images[image_id]
                batch.append((key,value))
                if len(batch)>=256:
                    emit(batch);batch=[];images={};page_encoded=0;decoded=0
            del value
            del entries
            if not batch:
                verify_pending()
    if batch:
        emit(batch);batch=[];images={};decoded=0
    verify_pending()
    return names,total,conflicts


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
        from content_capabilities import require
        from surface_materials import (
            CAPABILITY as SURFACE_CAPABILITY,
            FORMAT as SURFACE_FORMAT,
        )
        require(host, payload, ident)
        formats = {'ZBD-texture-v1','BWSNR2','BWSNR3','MWFX1','MW34SNA1','MW34SNP1','MW34-lighting-v1',SURFACE_FORMAT}
        if not set(payload.get('required_formats',[])).issubset(formats):
            raise ValueError('Unsupported environment resource format')
        files = manifest.get('files',{}); total = 0; seen = {'pack.json'}
        if not files or len(files)>10000: raise ValueError('Invalid environment file table')
        uses_surface_materials = (
            SURFACE_FORMAT in payload.get('required_formats', [])
            or any(isinstance(pin, dict) and pin.get('format') == SURFACE_FORMAT for pin in files.values())
        )
        if uses_surface_materials and payload.get('required_capabilities', {}).get(SURFACE_CAPABILITY) != 1:
            raise ValueError('Environment surface materials require surface-materials capability version 1')
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
                expected={'BWSNR2':b'BWSNR2\0\0','BWSNR3':b'BWSNR3\0\0','MWFX1':b'MWFX1\0\0\0','MW34SNA1':b'MW34SNA1','MW34SNP1':b'MW34SNP1',SURFACE_FORMAT:b'BWSFM1\0\0'}
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
            if 'surface_materials' in registry:
                surf_name = registry['surface_materials']
                if (not uses_surface_materials or not isinstance(surf_name, str) or
                        surf_name not in paths or files[surf_name].get('format') != SURFACE_FORMAT):
                    raise ValueError('Undeclared or mislabeled shared mech surface materials')
                read_surface_materials_file(Path(paths[surf_name]), expected_asset_id=region)
                references.add(surf_name)
            if references!=set(paths) or any(files[p].get('format')!='ZBD-texture-v1' for p in banks.values()):
                raise ValueError('Invalid shared mech resource closure')
            if files[index].get('format')!='MW34SNA1' or any(files[p].get('format')!='BWSNR2' for p in pages):
                raise ValueError('Invalid shared mech normal formats')
            if Path(paths[index]).read_text().splitlines()!=['MW34SNA1',*[str(Path(p).relative_to('environment')).replace('\\','/') for p in pages]]:
                raise ValueError('Shared mech normal manifest differs from declared pages')
            required_shared_keys = {'schema_version','payload_profile','operation','banks','authored','authored_manifest'}
            if not required_shared_keys.issubset(set(registry)) or not set(registry).issubset(required_shared_keys | {'surface_materials'}):
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
        for surf_role in ('ground_surface_materials', 'surface_materials'):
            if surf_role in registry:
                surf_name = registry[surf_role]
                if (not uses_surface_materials or not isinstance(surf_name, str) or
                        surf_name not in paths or files[surf_name].get('format') != SURFACE_FORMAT):
                    raise ValueError('Undeclared or mislabeled environment surface materials')
                read_surface_materials_file(Path(paths[surf_name]), expected_asset_id=region)
                references.add(surf_name)
        for role in ['authored','world']:
            pages=registry.get(role,[])
            if not isinstance(pages,list) or not 0<len(pages)<=(16 if role=='authored' else 256): raise ValueError('Invalid normal page list')
            page_bytes=sum(files[p]['bytes'] for p in pages if p in files)
            if page_bytes>(AUTHORED_CATALOG_BYTES if role=='authored' else WORLD_CATALOG_BYTES):
                raise ValueError('Normal catalog exceeds native byte budget')
            if role=='world' and any(files[p]['bytes']>WORLD_PAGE_BYTES for p in pages if p in files):
                raise ValueError('World normal page exceeds native byte budget')
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
            allowed_page_formats={'BWSNR2','BWSNR3'} if role=='world' else {'BWSNR2'}
            if any(files[p].get('format') not in allowed_page_formats for p in page_names): raise ValueError('Invalid normal page declaration')
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
    from presentation_policy import environment as presentation_environment
    if not selected:
        environment['MW34_EFFECT_LIGHTS']='0'
        for key in ['MW34_WATER_DETAIL','MW34_SURF_DETAIL','MW34_CLOUD_DETAIL']:
            environment[key]='0'
        return presentation_environment(host, selected, environment)
    first=next((p for p in selected.values() if 'effects' in p['registry']),None)
    if first is None:
        environment=profile_bindings({},host)
        shared=selected['shared-mechs']
        environment['MW34_SURFACE_NORMALS']=shared['paths'][shared['registry']['authored_manifest']]
        if 'surface_materials' in shared['registry']:
            environment['MW34_SURFACE_MATERIALS']=shared['paths'][shared['registry']['surface_materials']]
        return presentation_environment(host, selected, environment)
    registry=first['registry']; paths=first['paths']
    environment.update(MW34_WORLD_NORMALS=paths[registry['world_manifest']],
                       MW34_SURFACE_NORMALS=paths[registry['authored_manifest']],
                       MW34_EFFECT_LIGHT_CATALOG=paths[registry['effects']],
                       MW34_EFFECT_LIGHTS='1')
    for role,name in registry['detail'].items(): environment['MW34_'+role.upper()+'_NORMALS']=paths[name]
    ordered=[pack for _region,pack in sorted(selected.items(),key=lambda item:(REGION_PRIORITY.get(item[0],99),item[0]))]
    for surf_role,env_key in (('ground_surface_materials','MW34_GROUND_SURFACE_MATERIALS'),
                              ('surface_materials','MW34_SURFACE_MATERIALS')):
        sources = [p for p in ordered if surf_role in p['registry']]
        # Multiple sources need the prepared catalog; a single source is safe
        # to expose during preflight before prepare() writes launch resources.
        if len(sources) == 1:
            pack = sources[0]
            environment[env_key] = pack['paths'][pack['registry'][surf_role]]
    return presentation_environment(host, selected, environment)


def detail_metadata(selected):
    """Pins for the verified installed resources, independent of development files."""
    first=next((p for p in selected.values() if 'detail' in p['registry']),None)
    if first is None: return {}
    return {role:dict(path=first['paths'][name],
                      sha256=first['files'][name]['sha256'],
                      bytes=first['files'][name]['bytes'])
            for role,name in first['registry']['detail'].items()}


def write_merged_surface_materials(selected, role, output):
    """Keep every distinct selected material; the first region owns name conflicts.

    Preserve the first source's batch bindings for the primary ground surface.
    Without a stable source-key mapping, names are the only available conflict
    identity: later regions contribute only previously unseen material names.
    """
    ordered = sorted(selected.items(), key=lambda item: (REGION_PRIORITY.get(item[0], 99), item[0]))
    records_by_name = {}
    images = []
    image_bytes = 0
    first_mesh_hash = None
    first_binding_names = None
    for region, pack in ordered:
        name = pack['registry'].get(role)
        if name is None:
            continue
        source = read_surface_materials_file(Path(pack['paths'][name]), expected_asset_id=region)
        if first_mesh_hash is None:
            first_mesh_hash = source['mesh_uv_hash']
            first_binding_names = [
                None if index == NO_SURFACE_MATERIAL else source['records'][index]['material_name']
                for index in source['bindings']
            ]
        source_image_indices = {}
        for record in source['records']:
            material_name = record['material_name']
            if material_name in records_by_name:
                continue
            updated = record.copy()
            for field in ('height_image', 'thickness_image'):
                index = record[field]
                if index != NO_SURFACE_IMAGE:
                    if index not in source_image_indices:
                        image = source['images'][index]
                        if image_bytes + len(image['pixels']) > MAX_SIDECAR_BYTES:
                            raise ValueError('Merged surface materials exceed native image byte budget')
                        image_bytes += len(image['pixels'])
                        image_name = f'merged_{len(images):04d}'
                        source_image_indices[index] = len(images)
                        images.append((image_name, image))
                    updated[field] = source_image_indices[index]
            if len(records_by_name) >= MAX_SURFACE_RECORDS or len(images) > MAX_SURFACE_IMAGES:
                raise ValueError('Merged surface materials exceed native record/image budget')
            records_by_name[material_name] = updated
    if first_mesh_hash is None:
        return None

    records = sorted(records_by_name.values(), key=lambda rec: (
        rec['asset_id'].encode('utf-8'), rec['material_name'].encode('ascii')))
    record_indices = {record['material_name']: index for index, record in enumerate(records)}
    bindings = [NO_SURFACE_MATERIAL if name is None else record_indices[name]
                for name in first_binding_names]
    record_bytes = []
    for record in records:
        encoded_record = bytearray()
        for field in ('asset_id', 'material_name'):
            encoded = record[field].encode('utf-8')
            encoded_record.extend(struct.pack('<I', len(encoded)))
            encoded_record.extend(encoded)
        encoded_record.extend(struct.pack(
            '<IIfffIffffIIfffffffffffff',
            record['height_image'], record['thickness_image'], record['height_reference'],
            record['height_amplitude'], record['max_displacement'], record['tessellation_cap'],
            *record['uv_scale'], *record['uv_offset'], record['address_mode_u'],
            record['address_mode_v'], *record['atlas_rect'], record['sss_participation'],
            *record['sss_tint'], record['sss_radius'], record['thickness_scale'],
            record['roughness'], record['reflectivity'], record['metallic'],
        ))
        record_bytes.append(encoded_record)
    header_bytes = 32 + 4 * len(bindings)
    image_headers_bytes = sum(4 + len(name.encode('ascii')) + 20 for name, _ in images)
    total_bytes = header_bytes + sum(map(len, record_bytes)) + image_headers_bytes + image_bytes
    if total_bytes > MAX_SIDECAR_BYTES:
        raise ValueError('Merged surface materials exceed native sidecar byte budget')
    path = output / (role + '.bin')
    with path.open('wb') as stream:
        stream.write(b'BWSFM1\0\0')
        stream.write(struct.pack('<IIIIQ', 1, len(bindings), len(records), len(images), first_mesh_hash))
        stream.write(struct.pack('<' + 'I' * len(bindings), *bindings))
        for encoded_record in record_bytes:
            stream.write(encoded_record)
        for name, image in images:
            encoded = name.encode('ascii')
            stream.write(struct.pack('<I', len(encoded)))
            stream.write(encoded)
            stream.write(struct.pack('<IIIQ', image['role'], image['width'], image['height'], image['hash']))
            stream.write(image['pixels'])
    return str(path.resolve())


def prepare(selected, host, output):
    """Write fresh per-launch bank and merged normal indices; never edit packs."""
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    environment=profile_bindings(selected,host); bankmap={}
    for pack in selected.values():
        registry=pack['registry'];paths=pack['paths']
        for key,name in registry['banks'].items(): bankmap[key]=paths[name]
    data=bytearray(b'MWBANK1\0'+struct.pack('<I',len(bankmap)))
    for key,path in sorted(bankmap.items()):
        a=key.encode();b=path.encode();data+=struct.pack('<II',len(a),len(b))+a+b
    if bankmap:
        (output/'texture-banks.bin').write_bytes(data)
        environment['MW34_REMASTER_BANKS']=str((output/'texture-banks.bin').resolve())
    for role in ('authored','world'):
        names,total,_conflicts=write_merged_normal_catalog(selected,role,output)
        if role=='authored' and total>host.get('authored_normal_catalog_budget_bytes',AUTHORED_CATALOG_BYTES):
            raise ValueError('Installed authored normal catalog exceeds native budget')
        if not names: continue
        path=output/(role+'.txt');path.write_text(('MW34SNA1' if role=='authored' else 'MW34SNP1')+'\n'+'\n'.join(names)+'\n')
        environment['MW34_SURFACE_NORMALS' if role=='authored' else 'MW34_WORLD_NORMALS']=str(path.resolve())
    for role, env_key in (('ground_surface_materials', 'MW34_GROUND_SURFACE_MATERIALS'),
                          ('surface_materials', 'MW34_SURFACE_MATERIALS')):
        merged = write_merged_surface_materials(selected, role, output)
        if merged is not None:
            environment[env_key] = merged
    from mission_lighting import prepare as prepare_lighting
    environment.update(prepare_lighting(selected, output))
    from presentation_policy import environment as presentation_environment
    return presentation_environment(host, selected, environment)
