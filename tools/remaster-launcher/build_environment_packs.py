"""Build five local launcher environment archives from the selected, pinned assets.

No source artwork, executable, generated game code or developer paths enter an
archive. Every bank is streamed, hashed while packaging and independently read
back. A completed packs.json is written only after all archives pass.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile

from prepared_environment_packs import PROFILE,REGISTRY,REGIONS,sha,encode_normal_pages
from prepare_effect_lights import banks
from prepare_surface_normals import bank_entries
from normal_materials import read_surface_bindings,pack_surface_bindings
from prepare_world_normals import accelerated_hash
from campaign_material_source import converted_color
from mission_lighting import MISSIONS, validate as validate_lighting

ROOT=Path(__file__).resolve().parents[2]


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def normal_pages(path):
    path=Path(path)
    with path.open('rb') as stream:magic=stream.read(8)
    if magic==b'BWSNR2\0\0':return [path]
    if magic not in (b'MW34SNA1',b'MW34SNP1'):raise ValueError('Unsupported normal manifest')
    return [(path.parent/p).resolve() for p in path.read_text().splitlines()[1:] if p]


def verify_archive(path):
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist();manifest=json.loads(archive.read('pack.json'));files=manifest['files']
        if len(names)!=len(set(names)) or set(names)!={'pack.json',*files}:raise ValueError('Archive closure failure')
        for name,pin in files.items():
            if archive.getinfo(name).file_size!=pin['bytes']:raise ValueError('Archive size mismatch')
            with archive.open(name) as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=pin['sha256']:raise ValueError('Archive hash mismatch')
        for name in ['pack.json',REGISTRY]:
            raw=archive.read(name)
            if any(p in raw for p in [b'D:/',b'C:/',b'D:\\',b'C:\\']):raise ValueError('Developer path in archive')
        return manifest


def build(profile_path,output):
    import numpy as np
    if output.exists():raise ValueError('Choose a fresh pack output directory')
    output.mkdir(parents=True);profile_pin=sha(profile_path);profile=json.loads(profile_path.read_bytes());host=profile['native'];env=host['runtime_environment']
    if sha(host['executable'])!=host['executable_sha256']:raise ValueError('Host pin mismatch')
    if 1 not in host.get('mission_environment_versions', []): raise ValueError('Lighting packs require a mission-environment-v1 host')
    mission_source=Path(__file__).with_name('mission-lighting.json')
    authored_missions=json.loads(mission_source.read_text(encoding='utf-8'))['missions']
    banklist=banks(Path(env['MW34_REMASTER_BANKS']));digest=accelerated_hash(ROOT/'build/default/mw34_normal_hash.dll')
    normal_sources={role:normal_pages(env[key]) for role,key in [('authored','MW34_SURFACE_NORMALS'),('world','MW34_WORLD_NORMALS')]}
    catalogs={};provenance={str(profile_path):profile_pin,str(mission_source):sha(mission_source)}
    for role,pages in normal_sources.items():
        catalog={}
        for page in pages:
            provenance[str(page)]=sha(page)
            for key,value in read_surface_bindings(page.read_bytes()):
                if key in catalog and catalog[key]!=value:raise ValueError('Ambiguous input normal key')
                catalog[key]=value
        catalogs[role]=catalog
    prepared=[]
    for operation,regions in REGIONS.items():
        if operation == 'shared-mechs': continue  # Built separately; owns only the two root mech banks.
        stage=output/('prepared-'+operation);stage.mkdir();sources={};filetable={};runtime_keys=set();bankrefs={}
        def add(relative,path,fmt=None):
            path=Path(path);pin=dict(bytes=path.stat().st_size,sha256=sha(path))
            if fmt:pin['format']=fmt
            sources[relative]=path;filetable[relative]=pin;provenance[str(path)]=pin['sha256'];return relative
        for bank,path in banklist:
            if bank.split('/')[1] not in regions:continue
            bankrefs[bank]=add('environment/banks/'+bank.split('/')[1]+'/'+path.name,path,'ZBD-texture-v1')
            with path.open('rb') as stream:
                for name,(offset,span) in bank_entries(path).items():
                    stream.seek(offset);b=stream.read(span);flags,w,h,*_=struct.unpack('<IHHIHH',b[:16]);base=flags&~96
                    if base not in (3,5,11):raise ValueError('Unsupported published texture descriptor')
                    words=np.frombuffer(b[16:16+w*h*2],'<u2').reshape(h,w).astype('uint32')
                    alpha=np.frombuffer(b[16+w*h*2:],'uint8').reshape(h,w) if base==11 else np.where(words!=0,255,0).astype('uint8') if base==3 else None
                    for fmt in ([1] if alpha is None else [1,2,3]):
                        pixels=converted_color(words,alpha,fmt);runtime_keys.add((w,h,fmt,digest(pixels)))
                        if alpha is not None and fmt!=1:
                            zeroed=np.frombuffer(pixels,'<u2').copy().reshape(h,w);zeroed[alpha==0]=0;runtime_keys.add((w,h,fmt,digest(zeroed.tobytes())))
            print(operation,'indexed',bank,flush=True)
        registry=dict(schema_version=2,payload_profile=PROFILE,operation=operation,banks=bankrefs,detail={})
        for role,catalog in catalogs.items():
            items=sorted((k,v) for k,v in catalog.items() if k in runtime_keys);pages=[]
            if not items:raise ValueError('Missing regional normal coverage')
            for i,data in enumerate(encode_normal_pages(items,world=role=='world')):
                name=f'environment/{role}-{i:03}.bin';path=stage/name;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(data)
                pages.append(add(name,path,'BWSNR2'))
            registry[role]=pages
            path=stage/'environment'/(role+'.txt');path.write_text(('MW34SNA1' if role=='authored' else 'MW34SNP1')+'\n'+'\n'.join(str(Path(p).relative_to('environment')).replace('\\','/') for p in pages)+'\n')
            registry[role+'_manifest']=add('environment/'+path.name,path,'MW34SNA1' if role=='authored' else 'MW34SNP1')
        registry['effects']=add('environment/effects.bin',env['MW34_EFFECT_LIGHT_CATALOG'],'MWFX1')
        lighting=dict(schema_version=1,missions={ident:authored_missions[ident] for ident in sorted(MISSIONS[operation])},maps={})
        if operation=='training':
            selection=host['sun_preset'];source=ROOT/selection['source']
            provenance[str(source)]=sha(source)
            catalog=json.loads(source.read_text(encoding='utf-8-sig'))
            # The pack owns its authored default. A developer profile may select
            # a different preview preset without changing the shipped map.
            entry=dict(catalog['maps'][selection['map']])
            lighting['maps']={selection['map']:entry}
        validate_lighting(lighting,operation)
        lighting_path=stage/'environment/lighting.json';write_json(lighting_path,lighting)
        registry['lighting']=add('environment/lighting.json',lighting_path,'MW34-lighting-v1')
        for role in ['water','surf','cloud']:
            registry['detail'][role]=add('environment/detail/'+role+'.bin',env['MW34_'+role.upper()+'_NORMALS'],'BWSNR2')
        registry_path=stage/REGISTRY;write_json(registry_path,registry);add(REGISTRY,registry_path)
        title='Training' if operation=='training' else 'Operation '+operation[-1]
        version='1.1.1' if operation=='training' else '1.1.0'
        manifest=dict(schema_version=2, game_id="mw3",id='com.mw3remaster.textures.'+operation,name=title+' Textures and Lighting',version=version,author='MW3 Remaster Project',category='Textures',description='Prepared textures, normals, mission day/night, atmosphere and dynamic-light settings. Local playtest candidate.',provides=dict(textures=True,normal_maps=True),native_payload=dict(profile=PROFILE,registry=REGISTRY,path_base='pack-root',required_capabilities={'environment-resources':1}, reference_host_sha256=host['executable_sha256'],required_formats=['ZBD-texture-v1','BWSNR2','MWFX1','MW34SNA1','MW34SNP1','MW34-lighting-v1']),files=filetable)
        if sum(p['bytes'] for p in filetable.values())>16*1024**3:raise ValueError('Pack exceeds installer budget')
        write_json(stage/'pack.json',manifest);prepared.append((operation,stage,sources,manifest))
    def package(item):
        operation,stage,sources,manifest=item;path=output/(operation+'-textures-'+manifest['version']+'.mw3pack');temporary=path.with_suffix('.partial')
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
            archive.write(stage/'pack.json','pack.json')
            for name,source in sources.items():
                h=hashlib.sha256();before=source.stat()
                with source.open('rb') as stream,archive.open(name,'w',force_zip64=True) as dest:
                    while chunk:=stream.read(1048576):h.update(chunk);dest.write(chunk)
                after=source.stat()
                if h.hexdigest()!=manifest['files'][name]['sha256'] or (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Source changed during packaging')
        verify_archive(temporary);temporary.rename(path)
        print('Verified',path.name,flush=True)
        return dict(id=manifest['id'],path=str(path.resolve()),bytes=path.stat().st_size,sha256=sha(path),expanded_bytes=sum(p['bytes'] for p in manifest['files'].values()),banks=6*len(REGIONS[operation]),files=len(manifest['files']),operation=operation)
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(package,prepared))
    if sha(profile_path)!=profile_pin:raise ValueError('Profile changed while packaging')
    # Check original selected source identities again before the completion marker.
    for path,pin in provenance.items():
        if sha(path)!=pin:raise ValueError('Input changed before publication: '+path)
    write_json(output/'private-build-provenance.json',provenance)
    write_json(output/'packs.json',dict(verified=True,host_sha256=host['executable_sha256'],packs=results,game_launched=False))
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--profile',type=Path,default=ROOT/'local/remaster/launcher.json');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    print(json.dumps(build(args.profile,args.output),indent=2))
