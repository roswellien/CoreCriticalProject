"""Real worker input/publication and recipe early-directory denials only."""
from pathlib import Path
import hashlib,json,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-spi-workarea'
PWSH=Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def inventory(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()} if p.exists() else None
def main(build_path,out):
    bp=Path(build_path).resolve();out=Path(out).resolve();assert out.parent==BASE and not out.exists();b=json.loads(bp.read_text());assert b['passed']
    for group in ('sources','tools','artifacts'):
        for p,h in b[group].items():assert sha(p)==h
    out.mkdir();commands=[];passed=False
    def run(label,args):
        q=subprocess.run(list(map(str,args)),cwd=ROOT,capture_output=True,timeout=60);log=out/(label+'.log');log.write_bytes(q.stdout+q.stderr);commands.append(dict(label=label,command=list(map(str,args)),exit_code=q.returncode,log=str(log),log_sha256=sha(log)));assert q.returncode!=0,label+' unexpectedly succeeded';return q.stdout+q.stderr
    try:
        pack=Path(b['extraction'])/'pack.bin';image=ROOT/'MW3/Mech3.exe'
        wrong_pack=out/'wrong-pack.bin';v=bytearray(pack.read_bytes());v[-1]^=1;wrong_pack.write_bytes(v)
        wrong_image=out/'wrong-image.bin';v=bytearray(image.read_bytes());v[-1]^=1;wrong_image.write_bytes(v)
        for name,exe in b['workers'].items():
            for label,p,i in (('image',pack,wrong_image),('pack',wrong_pack,image)):
                dst=out/(name+'-'+label+'.bin');text=run(name+'-'+label,[exe,p,i,dst]);assert not dst.exists() and not list(out.glob(dst.name+'.spi-stage-*'));assert b'identity' in text or b'private pack' in text
            dst=out/(name+'-existing-result.bin');dst.write_bytes(b'EXTERNAL-'+name.encode());old=sha(dst)
            text=run(name+'-existing',[exe,pack,image,dst]);assert sha(dst)==old and b'Fresh output required' in text and not list(out.glob(dst.name+'.spi-stage-*'))
            absent=out/(name+'-missing-parent');dst=absent/'result.bin';text=run(name+'-missing-parent',[exe,pack,image,dst]);assert not absent.exists() and b'Fresh owned stage required' in text
        for case in range(4):
            name=out.name+'-recipe-'+str(case);dst=BASE/name;derived=[ROOT/'build'/('m4-spi-'+name+'-'+suffix) for suffix in ('x86','O0','O2')];assert not dst.exists() and not any(p.exists() for p in derived)
            collision=dst if case==0 else derived[case-1];collision.mkdir();(collision/'external-sentinel.bin').write_bytes(b'EXTERNAL-PARTIAL-DIRECTORY');(collision/'nested').mkdir();(collision/'nested'/'second.bin').write_bytes(b'EXTERNAL-NESTED');before=inventory(collision)
            text=run('recipe-'+str(case),[PWSH,'-NoLogo','-NoProfile','-File',ROOT/'tools/m4-spi-workarea/build.ps1','-OutputDirectory',dst,'-ExtractionDirectory',out/'unavailable-extraction']);assert b'Existing report or derived build directory rejected before writes' in text;assert inventory(collision)==before
            assert not dst.exists() if case else inventory(dst)==before
            for p in derived:
                if p!=collision:assert not p.exists()
        for group in ('sources','tools','artifacts'):
            for p,h in b[group].items():assert sha(p)==h,'Frozen build mutated '+p
        passed=True
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        artifacts={str(p):sha(p) for p in out.rglob('*') if p.is_file()};(out/'report.json').write_text(json.dumps(dict(passed=passed,scope='Real negative controls: 12worker identity/publication denials before original body/native query, four early fresh-directory recipe denials; ordinary private sequential paths',build=str(bp),build_sha256=sha(bp),checker_sha256=sha(__file__),commands=commands,artifacts=artifacts),indent=2)+'\n')
if __name__=='__main__':main(*sys.argv[1:])
