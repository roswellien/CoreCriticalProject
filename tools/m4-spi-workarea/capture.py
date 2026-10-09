"""Run only the separately admitted read-only work-area experiment."""
from pathlib import Path
import hashlib,json,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(build_path,out):
    bp=Path(build_path).resolve();out=Path(out).resolve();out.relative_to(ROOT/'reports/m4-spi-workarea');assert not out.exists();b=json.loads(bp.read_text(encoding='utf-8-sig'));assert b['passed']
    for p,h in b['sources'].items():assert sha(p)==h,'changed compiled input '+p
    out.mkdir(parents=True);commands=[];passed=False
    def run(name,args):
        worker=Path(b['workers'][name]);assert sha(worker)==b['artifacts'][str(worker)];argv=[str(worker),*map(str,args)];q=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=60);log=out/(name+('-controls.log' if args[-1]=='--controls' else '.log'));log.write_bytes(q.stdout+q.stderr);commands.append(dict(command=argv,exit_code=q.returncode,log=str(log),log_sha256=sha(log)));assert q.returncode==0,'worker failed '+name+' '+str(log)
    try:
        pack=Path(b['extraction'])/'pack.bin';image=ROOT/'MW3/Mech3.exe'
        for name in ['original','O0','O2']:run(name,[pack,image,out/(name+'.bin')])
        for name in ['O0','O2']:run(name,[pack,image,'--controls'])
        passed=True
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        artifacts={str(p):sha(p) for p in out.iterdir() if p.is_file()};r=dict(passed=passed,scope='Actual isolated original/provider and native host-query observations; defined-output comparator and peer review still required, no connected startup credit',build=str(bp),build_sha256=sha(bp),commands=commands,artifacts=artifacts);(out/'capture.json').write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
