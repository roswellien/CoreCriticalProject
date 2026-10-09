"""Exercise real early fresh-directory guards without any compilation."""
import argparse,hashlib,json,subprocess,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def inventory(p):
    if not p.exists():return None
    return {x.relative_to(p).as_posix():('directory' if x.is_dir() else hashlib.sha256(x.read_bytes()).hexdigest()) for x in sorted(p.rglob('*'))}
def main():
    p=argparse.ArgumentParser();p.add_argument('--powershell',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();a.output.mkdir()
    checks=[];recipe=ROOT/'tools/m4-fp-sqrt/build_sqrt.ps1'
    for target in ('report','x86','O0','O2'):
        leaf='admission-'+uuid.uuid4().hex;candidate=ROOT/'reports/m4-fp-sqrt'/leaf
        paths={'report':candidate,**{l:ROOT/'build'/('m4-fp-sqrt-'+leaf+'-'+l) for l in ('x86','O0','O2')}};assert all(not x.exists() for x in paths.values())
        existing=paths[target];existing.mkdir();(existing/'nested').mkdir();(existing/'marker.bin').write_bytes(b'MW34 pre-existing evidence\0\xff');(existing/'nested/keep.txt').write_text('Keep literal bytes.\n')
        before={k:inventory(v) for k,v in paths.items()};command=[str(a.powershell),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(recipe),'-OutputDirectory',str(candidate)]
        run=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=30);after={k:inventory(v) for k,v in paths.items()};log=a.output/(target+'.log');log.write_bytes(run.stdout+run.stderr)
        diagnostic=b'Existing report directory rejected before mutation' if target=='report' else b'Existing build directory rejected before mutation'
        assert run.returncode!=0 and diagnostic in run.stdout+run.stderr and before==after
        checks.append({'target':target,'command':command,'exit_code':run.returncode,'diagnostic':diagnostic.decode(),'paths':{k:str(v) for k,v in paths.items()},'before':before,'after':after,'log':str(log.resolve()),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()})
    report={'passed':True,'checks':checks,'actual_checks':4,'scope':'Real PowerShell early directory guards with partial-report and all3derived-build marker fixtures'}
    (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'actual_directory_guards':4}))
if __name__=='__main__':main()
