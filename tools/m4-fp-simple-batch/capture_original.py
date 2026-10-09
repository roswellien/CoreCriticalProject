"""Run only the admitted two-root hardware probe, in a new private folder."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    build_path,out=map(lambda s:Path(s).resolve(),sys.argv[1:3]);build=json.loads(build_path.read_text(encoding='utf-8-sig'))
    assert build['passed'] and out.is_relative_to(ROOT/'reports/m4-fp-simple-batch') and not out.exists()
    # Historical build source paths may later change, but this invocation uses
    # only literal compiled worker, reviewed pack/image, unchanged raw helpers.
    worker=Path(build['original_worker']);assert sha(worker)==build['bindings'][str(worker)]
    pack=ROOT/'reports/m4-fp-startup/research-r1/pages.bin';image=ROOT/'MW3/Mech3.exe'
    assert sha(pack)=='9fc04ae9905bb2aef1ad6a60b61494e64560baad1be4cda14346b61410a7882e'
    assert sha(image)=='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
    out.mkdir();command=[str(worker),str(pack),str(image),str(out/'original.bin')]
    run=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=180)
    (out/'stdout.log').write_bytes(run.stdout);(out/'stderr.log').write_bytes(run.stderr)
    result={'passed':run.returncode==0,'scope':'Only two complete initializer routines, authored float/int input fixtures; no full game launch',
            'command':command,'exit_code':run.returncode,'expected_records':5952,'build_sha256':sha(build_path),
            'bindings':{str(p):sha(p) for p in (build_path,worker,pack,image,Path(__file__),out/'stdout.log',out/'stderr.log')}}
    if (out/'original.bin').exists():result['bindings'][str(out/'original.bin')]=sha(out/'original.bin')
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'exit_code':run.returncode,'stdout':run.stdout.decode(errors='replace'),'stderr':run.stderr.decode(errors='replace')}))
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
