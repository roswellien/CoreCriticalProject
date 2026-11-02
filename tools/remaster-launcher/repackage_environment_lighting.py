"""Add authored lighting to verified local environment packs without regenerating textures."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
from pathlib import Path
import zipfile

from mission_lighting import MISSIONS, validate
from prepared_environment_packs import select, sha, REGISTRY


def build(roots, profile_path, output):
    profile_path=Path(profile_path);profile_bytes=profile_path.read_bytes()
    profile=json.loads(profile_bytes);host=profile['native'];output=Path(output)
    if output.exists():raise ValueError('Choose a fresh output directory')
    if 1 not in host.get('mission_environment_versions',[]) or sha(host['executable'])!=host['executable_sha256']:
        raise ValueError('A verified mission lighting host is required')
    selected=select([str(p) for p in roots],host)
    source=Path(__file__).with_name('mission-lighting.json');source_bytes=source.read_bytes()
    missions=json.loads(source_bytes)['missions'];output.mkdir(parents=True)
    catalog_source=Path(host['sun_preset']['source'])
    if not catalog_source.is_absolute():catalog_source=Path(__file__).resolve().parents[2]/catalog_source
    catalog_bytes=catalog_source.read_bytes();training=json.loads(catalog_bytes)

    def package(item):
        operation,pack=item
        data=dict(schema_version=1,missions={key:missions[key] for key in sorted(MISSIONS[operation])},maps={})
        if operation=='training':
            # Preserve the catalog's map default even when the build profile
            # happens to be running a different preview preset.
            selection=host['sun_preset'];entry=copy.deepcopy(training['maps'][selection['map']])
            data['maps']={selection['map']:entry}
        validate(data,operation)
        registry=copy.deepcopy(pack['registry']);previous_lighting=registry.get('lighting');registry['lighting']='environment/lighting.json'
        generated={REGISTRY:(json.dumps(registry,indent=2)+'\n').encode(),
                   'environment/lighting.json':(json.dumps(data,indent=2)+'\n').encode()}
        manifest=json.loads((Path(pack['root'])/'pack.json').read_bytes());manifest['version']='1.2.0' if operation=='training' else '1.1.0'
        if previous_lighting and previous_lighting!='environment/lighting.json':manifest['files'].pop(previous_lighting)
        manifest['native_payload']['reference_host_sha256']=host['executable_sha256']
        manifest['native_payload']['required_formats']=sorted(set(manifest['native_payload']['required_formats'])|{'MW34-lighting-v1'})
        for name,raw in generated.items():
            manifest['files'][name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        manifest['files']['environment/lighting.json']['format']='MW34-lighting-v1'
        path=output/(operation+'-textures-'+manifest['version']+'.mw3pack');partial=path.with_suffix('.partial')
        with zipfile.ZipFile(partial,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as archive:
            archive.writestr('pack.json',json.dumps(manifest,indent=2))
            for name,pin in manifest['files'].items():
                if name in generated:archive.writestr(name,generated[name]);continue
                source_path=Path(pack['paths'][name]);before=source_path.stat();digest=hashlib.sha256()
                with source_path.open('rb') as stream,archive.open(name,'w',force_zip64=True) as dest:
                    while chunk:=stream.read(1048576):digest.update(chunk);dest.write(chunk)
                after=source_path.stat()
                if digest.hexdigest()!=pin['sha256'] or (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
                    raise ValueError('Source changed while packaging: '+name)
        with zipfile.ZipFile(partial) as archive:
            if len(archive.namelist())!=len(set(archive.namelist())) or set(archive.namelist())!={'pack.json',*manifest['files']}:
                raise ValueError('Archive member closure mismatch')
            for name,pin in manifest['files'].items():
                with archive.open(name) as stream:
                    if archive.getinfo(name).file_size!=pin['bytes'] or hashlib.file_digest(stream,'sha256').hexdigest()!=pin['sha256']:
                        raise ValueError('Archive verification failed: '+name)
        partial.rename(path);print('Verified',path.name,flush=True)
        return dict(operation=operation,id=manifest['id'],path=str(path.resolve()),bytes=path.stat().st_size,sha256=sha(path),files=len(manifest['files']))
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(package,selected.items()))
    if profile_path.read_bytes()!=profile_bytes or source.read_bytes()!=source_bytes or catalog_source.read_bytes()!=catalog_bytes:
        raise ValueError('Authoring inputs changed during packaging')
    (output/'packs.json').write_text(json.dumps(dict(verified=True,host_sha256=host['executable_sha256'],packs=results),indent=2)+'\n')
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roots',nargs='+',type=Path,required=True)
    parser.add_argument('--profile',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(build(args.roots,args.profile,args.output),indent=2))
