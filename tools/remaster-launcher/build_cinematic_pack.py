"""Author a local cinematic pack from a JSON description and user-owned media.

Source JSON: id, name, version, reference_host_sha256, clips (id, title,
source, replaces). Null replaces makes an MP4 library addition; an original
lowercase AVI stem makes a replacement. The launcher validates the actual formats
before installation. No media conversion, scripts or custom triggers are included.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile


def build(description, output):
    description = Path(description).resolve(strict=True)
    data = json.loads(description.read_text(encoding='utf-8-sig'))
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,127}', data['id']) or data['id'].endswith('.'):
        raise ValueError('Invalid pack identity')
    if not 1 <= len(data['clips']) <= 64:
        raise ValueError('A cinematic pack needs 1–64 clips')
    sources, clips, formats, ids, targets = {}, [], set(), set(), set()
    for clip in data['clips']:
        identity, target = clip['id'], clip['replaces']
        if not re.fullmatch('[a-z0-9][a-z0-9_-]{0,63}', identity) or identity in ids:
            raise ValueError('Invalid or duplicate clip identity')
        ids.add(identity)
        if target is not None:
            if not re.fullmatch('[a-z0-9_]{1,64}', target) or target in targets:
                raise ValueError('Invalid or duplicate original movie target')
            targets.add(target)
        source = (description.parent/clip['source']).resolve(strict=True)
        suffix, fmt = ('.mp4','MP4-library-v1') if target is None else ('.avi','AVI-IV50-original-v1')
        if source.suffix.lower() != suffix:
            raise ValueError('Source extension does not match cinematic role')
        name = 'cinematics/media/'+identity+suffix
        sources[name] = source
        formats.add(fmt)
        clips.append(dict(id=identity, title=clip['title'], source=name, replaces=target))
    def sha(path):
        with path.open('rb') as stream:
            return hashlib.file_digest(stream,'sha256').hexdigest()
    registry = json.dumps(dict(schema_version=2, payload_profile='prepared-cinematic-v1', clips=clips),indent=2).encode()
    files = {name:dict(bytes=p.stat().st_size,sha256=sha(p),format='MP4-library-v1' if name.endswith('.mp4') else 'AVI-IV50-original-v1') for name,p in sources.items()}
    files['cinematics/cinematics.json'] = dict(bytes=len(registry),sha256=hashlib.sha256(registry).hexdigest())
    if sum(f['bytes'] for f in files.values()) > 16*1024**3:
        raise ValueError('Cinematic pack exceeds expanded size limit')
    host=data.get('reference_host_sha256','')
    if targets and not re.fullmatch('[0-9a-f]{64}',host):
        raise ValueError('In-game replacements require a matched native runtime identity')
    manifest=dict(schema_version=2,id=data['id'],name=data['name'],version=data.get('version','1.0.0'),category='Cinematics',
                  native_payload=dict(profile='prepared-cinematic-v1',registry='cinematics/cinematics.json',path_base='pack-root',reference_host_sha256=host,required_formats=sorted(formats)),files=files)
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_STORED) as archive:
        archive.writestr('pack.json',json.dumps(manifest,indent=2))
        archive.writestr('cinematics/cinematics.json',registry)
        for name,path in sources.items(): archive.write(path,name)
    with zipfile.ZipFile(output) as archive:
        for name,pin in files.items():
            with archive.open(name) as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=pin['sha256']:
                    raise ValueError('Archive integrity check failed')
    if any(sha(p)!=files[name]['sha256'] for name,p in sources.items()):
        raise ValueError('Source changed while packaging')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--description',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(build(args.description,args.output))
