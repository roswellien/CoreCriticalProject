"""Causal early fresh-directory admission fixtures; no worker runs."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
PWSH=Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
RECIPE=Path(__file__).with_name('build_original.ps1')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory(root):
    return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file()} if root.exists() else None
def main():
    out=Path(sys.argv[1]).resolve();assert out.parent==ROOT/'reports/m4-mixed-startup' and out.name.startswith('original-') and not out.exists();out.mkdir()
    cases=[]
    for index,collision in enumerate(('report','extraction','build')):
        leaf=out.name+'-case-'+str(index);report=out.parent/leaf;extract=out.parent/('original-extract-'+leaf);build=ROOT/'build'/('m4-mixed-startup-'+leaf+'-x86');paths={'report':report,'extraction':extract,'build':build}
        assert all(not p.exists() for p in paths.values());fixture=paths[collision];fixture.mkdir(parents=True);(fixture/'authored-marker.bin').write_bytes(bytes.fromhex('4d57333400ff8042'))
        before={k:inventory(p) for k,p in paths.items()}
        command=[str(PWSH),'-NoLogo','-NoProfile','-File',str(RECIPE),'-OutputDirectory',str(report)]
        run=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=30);(out/(collision+'.stdout.log')).write_bytes(run.stdout);(out/(collision+'.stderr.log')).write_bytes(run.stderr)
        after={k:inventory(p) for k,p in paths.items()}
        assert run.returncode!=0 and before==after and b'Existing report/extraction/build directory rejected before mutation' in run.stdout+run.stderr
        cases.append({'case':collision,'exit_code':run.returncode,'command':command,'before':before,'after':after,'unchanged':True})
    result={'passed':True,'checks':3,'cases':cases,'bindings':{str(p):sha(p) for p in (Path(__file__),RECIPE,PWSH)}}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print('3 actual recipe no-mutation admission controls passed')
if __name__=='__main__':main()
