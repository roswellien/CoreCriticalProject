"""Actual identity/publication denials; no additional original guest body."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
def bind(path):
    p=Path(path).resolve()
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha}
worker,pack,image,out=map(lambda p:Path(p).resolve(),sys.argv[1:5])
if not out.is_relative_to(ROOT/'reports/m4-fp-transcendental') or out.exists():raise ValueError('Fresh private worker control directory required')
out.mkdir(parents=True);cases=[];original='reference' in worker.name
def run(name,args,cause,destination=None):
    result=subprocess.run([str(worker),*map(str,args)],cwd=ROOT,capture_output=True,timeout=35)
    (out/(name+'.stdout')).write_bytes(result.stdout);(out/(name+'.stderr')).write_bytes(result.stderr)
    if result.returncode!=1 or cause not in result.stderr.decode():raise ValueError('Wrong actual denial cause: '+name+': '+result.stderr.decode())
    if destination and destination.exists():raise ValueError('Denied worker published output')
    cases.append({'name':name,'command':[str(worker),*map(str,args)],'exit_code':result.returncode,'intended_cause':cause})
run('bad-cli',[],'Directed reference:' if original else 'Cosine directed native:')
changed=out/'changed-pack.bin';bytes_=bytearray(pack.read_bytes());bytes_[-1]^=1;changed.write_bytes(bytes_);destination=out/'changed-pack-output.bin'
run('changed-pack',[changed,image,destination],'Exact pack identity required' if original else 'Exact reviewed pack required',destination)
changed_image=out/'changed-image.exe';bytes_=bytearray(image.read_bytes());bytes_[-1]^=1;changed_image.write_bytes(bytes_);destination=out/'changed-image-output.bin'
run('changed-image',[pack,changed_image,destination],'Exact image identity required',destination)
destination=out/'missing-output.bin';run('missing-input',[out/'absent.bin',image,destination],'Input unavailable',destination)
destination=out/'existing-output.bin';destination.write_bytes(b'owned directed evidence sentinel');before=bind(destination)
run('existing-output',[pack,image,destination],'Output exists or cannot establish absence' if original else 'Fresh output required')
if bind(destination)!=before:raise ValueError('Existing evidence changed')
if list(out.glob('*.fp-stage-*')):raise ValueError('Denied worker left staging artifact')
report={'passed':True,'scope':'Actual directed original/native identity and sequential publication controls','additional_original_guest_bodies_executed':False,
        'controls':cases,'worker':bind(worker),'pack':bind(pack),'image':bind(image),'source':bind(__file__),'preserved_existing_output':before,
        'publication_domain':'Fresh ordinary sequential directories only; concurrent/reparse ownership not admitted'}
report['bindings']={str(p):bind(p)['sha256'] for p in out.iterdir() if p.is_file()}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('Actual directed worker controls:',len(cases))
