"""Actual worker admission/publication controls; no extra game-body launches."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]

def bind(path):
    path=Path(path).resolve()
    with path.open('rb') as f: sha=hashlib.file_digest(f,'sha256').hexdigest()
    return {'path':str(path),'size_bytes':path.stat().st_size,'sha256':sha}

worker,pack,image,out=map(lambda p:Path(p).resolve(),sys.argv[1:5])
if out.exists():raise ValueError('Fresh worker control directory required')
out.mkdir(parents=True)
cases=[]
def run(name,args,expected,cause=None,destination=None):
    p=subprocess.run([str(worker),*map(str,args)],cwd=ROOT,capture_output=True,timeout=35)
    (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr)
    if p.returncode!=expected or (cause is not None and cause not in p.stderr.decode()):
        raise ValueError('Wrong actual control cause: '+name+': '+p.stderr.decode())
    if destination is not None and destination.exists():raise ValueError('Rejected worker published output: '+name)
    cases.append({'name':name,'command':[str(worker),*map(str,args)],'exit_code':p.returncode,
                  'intended_cause':cause,'stdout':bind(out/(name+'.stdout')),'stderr':bind(out/(name+'.stderr'))})
run('hash-kat',['--check-hash'],0)
run('bad-cli',[],1,'FP reference:')
changed=out/'changed-pack.bin';b=bytearray(pack.read_bytes());b[-1]^=1;changed.write_bytes(b)
destination=out/'changed-pack-output.bin'
run('changed-pack',[changed,image,destination],1,'Pack identity rejected',destination)
changed_image=out/'changed-image.exe';b=bytearray(image.read_bytes());b[-1]^=1;changed_image.write_bytes(b)
destination=out/'changed-image-output.bin'
run('changed-image',[pack,changed_image,destination],1,'Image identity rejected',destination)
destination=out/'missing-input-output.bin'
run('missing-input',[out/'absent.bin',image,destination],1,'Input unavailable',destination)
destination=out/'existing-output.bin';destination.write_bytes(b'owned pre-existing evidence sentinel')
before=bind(destination)
run('existing-output',[pack,image,destination],1,'Output exists or cannot establish absence')
if bind(destination)!=before:raise ValueError('Existing output was modified')
if list(out.glob('*.fp-stage-*')):raise ValueError('Rejected request left a staging artifact')
report={'passed':True,'scope':'Actual original worker admission and fresh output ownership controls',
        'controls':cases,'worker':bind(worker),'pack':bind(pack),'image':bind(image),
        'modified_inputs':[bind(changed),bind(changed_image)],'preserved_existing_output':before,'source':bind(__file__),
        'additional_original_game_bodies_executed':False,
        'publication_domain':'Sequential fresh ordinary directories; no concurrent publisher/reparse-link/atomic ownership claim'}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('Actual worker admission/publication controls:',len(cases))
