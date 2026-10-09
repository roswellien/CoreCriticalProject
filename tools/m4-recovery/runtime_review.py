"""Root review of authored runtime foundation; no game execution credit."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    out=ROOT/'reports/m4-runtime/independent-root-r4'
    if out.exists():raise ValueError('Fresh runtime review output required')
    candidate=ROOT/'reports/m4-runtime/context-r4/build.json'
    if sha(candidate)!='1c37ebebcf8e347b438b9af9170d6db487dfc613dc65cf2ff3db19e5703e7815':raise ValueError('Runtime r4 report changed')
    report=json.loads(candidate.read_text())
    checked={}
    for group in ('source_files','tool_files','artifacts'):
        for path,expected in report[group].items():
            if sha(path)!=expected:raise ValueError('Runtime binding changed: '+path)
            checked[path]=expected
    for copy in report['literal_source_copies']:
        if Path(copy['original_path']).read_bytes()!=Path(copy['preserved_path']).read_bytes():raise ValueError('Literal source mismatch')
        checked[copy['preserved_path']]=copy['sha256']
    if not report['passed'] or report['milestone_M4_complete']:raise ValueError('Incorrect author scope')
    out.mkdir(parents=True)
    commands=[]
    def run(name,args,exit_code=0):
        p=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,timeout=90)
        (out/(name+'.stdout')).write_bytes(p.stdout);(out/(name+'.stderr')).write_bytes(p.stderr)
        commands.append({'name':name,'command':list(map(str,args)),'exit_code':p.returncode})
        if p.returncode!=exit_code:raise ValueError('Review command failed '+name)
        return p
    test=ROOT/'build/m4-runtime-context-r4/mw34_m4_runtime_tests.exe'
    p=run('author-authored-replay',[test])
    if p.stdout.strip()!=b'Runtime authored contract checks: 65':raise ValueError('Author contract controls differ')
    run('author-actual-replay',[sys.executable,ROOT/'tests/m4-runtime/check_runtime.py','--host',
                              ROOT/'build/m4-runtime-context-r4/mw34_m4_runtime_host.exe','--image',ROOT/'MW3/Mech3.exe','--out',out/'actual-replay'])
    result={'passed':True,'scope':'Independent source/identity/actual-control review of runtime foundation only',
            'author_binding':{'path':str(candidate),'sha256':sha(candidate)},
            'rehashes':len(checked),'literal_sources':len(report['literal_source_copies']),
            'authored_checks_replayed':65,'actual_image_causal_checks_replayed':6,'commands':commands,
            'reviewed_invariants':['Owned immutable admitted input before loading','Private bounded stack/arena/TIB fields with unmapped guards/holes',
                'Persistent opaque3504 State and FX512 views','Separate authored/game registry domains and code span hashing',
                'Typed routing rejects unresolved entries/imports before CALL mutation','ABI exit checks and no-skip initializer ordering',
                'Unsupported SEH dispatch remains an explicit fault'],
            'limitations':['Native callback/source/artifact association needs each actual adapter gate; hash syntax does not prove it',
                'No actual game translation, CRT, import implementation, SEH dispatch or native menu execution',
                'FX512 is not a complete observed legacy FPU metadata representation; adapters must separately preserve ENV fields',
                'Runtime poison catches its typed failures and propagated exceptions; a trusted callback can swallow a raw GuestMemory fault. Required adapters must prove propagation/faultescape until checked-memory fault tracking exists.'],
            'full_M4_complete':False,'game_execution_admitted_by_this_review':False}
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    checked[str(candidate)]=sha(candidate);checked[str(Path(__file__).resolve())]=sha(__file__)
    for path in sorted(out.rglob('*')):
        if path.is_file():checked[str(path.resolve())]=sha(path)
    (out/'pins.json').write_text(json.dumps({'files':checked},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'passed':True,'bindings':len(checked),'controls_replayed':71,'M4_complete':False}))

if __name__=='__main__':main()
