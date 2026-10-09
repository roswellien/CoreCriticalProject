"""Launch only the hash-admitted isolated connected original worker."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    build_path,out=map(lambda s:Path(s).resolve(),sys.argv[1:3]);build=json.loads(build_path.read_text(encoding='utf-8-sig'))
    assert build['passed'] and out.parent==ROOT/'reports/m4-mixed-startup' and out.name.startswith('original-') and not out.exists()
    worker,pack,image=map(Path,(build['worker'],build['pack'],build['image']))
    for p in (worker,pack,image):assert sha(p)==build['bindings'][str(p)]
    out.mkdir();command=[str(worker),str(pack),str(image),str(out/'original.bin')]
    run=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=190)
    (out/'stdout.log').write_bytes(run.stdout);(out/'stderr.log').write_bytes(run.stderr)
    result={'passed':run.returncode==0,'scope':'48 default connected original26-root sequences only; no ordinary game launch or native equivalence',
            'command':command,'exit_code':run.returncode,'expected_sequences':48,'expected_records':1248,'expected_record_size':92388,'build_sha256':sha(build_path),
            'bindings':{str(p):sha(p) for p in (build_path,worker,pack,image,Path(__file__),out/'stdout.log',out/'stderr.log')}}
    if (out/'original.bin').exists():result['bindings'][str(out/'original.bin')]=sha(out/'original.bin')
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'exit_code':run.returncode,'stdout':run.stdout.decode(errors='replace'),'stderr':run.stderr.decode(errors='replace')}))
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
