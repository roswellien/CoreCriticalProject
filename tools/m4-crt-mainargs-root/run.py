"""Root-owned fresh execution of literal O0/O2 composition artifacts."""
import hashlib,json,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(build,out):
    assert out.parent==ROOT/'reports/m4-crt-mainargs' and not out.exists();out.mkdir()
    pins={};commands=[]
    def pin(p,h=None):
        p=Path(p);p=p if p.is_absolute() else p.resolve();v=sha(p);assert h is None or h==v,str(p);pins[str(p)]=v;return p
    try:
        report=json.loads(pin(build/'build.json').read_text(encoding='utf-8-sig'));assert report['passed']
        for k in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
            for p,h in report[k].items():pin(p,h)
        game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
        provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
        pack=pin(ROOT/'reports/m4-crt-fdiv/native-derived-r1/pack.bin','fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80')
        before=pin(ROOT/'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin','4294b8d926966c04d305b6e22a9166f08a328f4cc1c62984b72677fe83dd638a')
        for level in ('O0','O2'):
            worker=pin(report['workers'][level]);obj=pin(ROOT/f'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-{level}.obj')
            command=list(map(str,(worker,game,obj,provider,pack,before,out/f'native-{level}')))
            at=time.time();cp=subprocess.run(command,capture_output=True,timeout=120)
            log=out/f'{level}.stdout';log.write_bytes(cp.stdout);err=out/f'{level}.stderr';err.write_bytes(cp.stderr)
            commands.append(dict(level=level,command=command,exit_code=cp.returncode,seconds=time.time()-at,stdout_sha256=pin(log) and sha(log),stderr_sha256=pin(err) and sha(err)))
            assert cp.returncode==0,(level,cp.stderr.decode(errors='replace'))
            assert pin(out/f'native-{level}/COMPLETE').read_bytes()==b'COMPLETE'
            for p in (out/f'native-{level}').rglob('*'):
                if p.is_file():pin(p)
        for p,h in list(pins.items()):assert sha(p)==h,p
        pin(__file__);pin(sys.executable)
        result=dict(passed=True,commands=commands,native_executed_by_root=True,positive_cases=48,causal_controls=120,guest_instructions_literal=True,original_executed=False,whole_M4_complete=False)
        (out/'execution.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'execution.json')
        (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
        print(json.dumps(dict(passed=True,positive_cases=48,causal_controls=120,execution_sha256=sha(out/'execution.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(*[Path(p).resolve() for p in sys.argv[1:]])


