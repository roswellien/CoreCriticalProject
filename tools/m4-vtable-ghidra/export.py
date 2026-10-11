"""Warm read-only exact game function export; no runtime proof or database save."""
from pathlib import Path
import hashlib, json, os, subprocess, sys, time, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
GHIDRA=Path('C:/Users/jcbla/AppData/Local/Programs/REA/ghidra_12.1.4_PUBLIC')
JDK=Path('C:/Users/jcbla/AppData/Local/Programs/REA/jdk-21.0.12.1+1')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
    out=ROOT/'reports/m4-vtable-ghidra'/name;out.mkdir(parents=True,exist_ok=False);pins={};passed=False;runs=[]
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,v);pins[str(p)]=v;return p
    try:
        p=pin(ROOT/'reports/m4-next-source/recovery-r1/report.json','99e59ac4b9adeb98f2227361f80db78e12eead87e35212d71b4147a8ba9effeb');source=json.loads(p.read_bytes())
        assert source['passed'] and source['root_count']==4
        entries=[x for x in source['all_game_entries'] if x not in(0x5AC110,0x5AC140,0x5AC580)];assert len(entries)==15
        template=pin(ROOT/'reports/m4-container-ghidra/export-r1/scripts/MW34ContainerExport.java')
        scripts=out/'scripts';scripts.mkdir();script=scripts/'MW34VtableExport.java';script.write_text(template.read_text().replace('MW34ContainerExport','MW34VtableExport'));pin(script)
        target=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');h=sha(target)
        project=ROOT/'reports/m4-rea-evaluation/game-headless-r1/project';title='MW34Pilot';assert(project/(title+'.gpr')).exists()
        exported=out/'game-export.json'
        command=[str(GHIDRA/'support/analyzeHeadless.bat'),str(project),title,'-process',target.name,'-noanalysis','-readOnly','-scriptPath',str(scripts),'-postScript',script.name,str(exported),str(target),h,*[format(x,'x') for x in entries],'-log',str(out/'game-ghidra.log'),'-scriptlog',str(out/'game-script.log')]
        started=time.perf_counter()
        with(out/'game-console.log').open('wb') as log:r=subprocess.run(command,env=dict(os.environ,JAVA_HOME=str(JDK),GHIDRA_JAVA_HOME=str(JDK)),stdout=log,stderr=subprocess.STDOUT,timeout=300,creationflags=0x08000000)
        assert r.returncode==0 and exported.exists();data=json.loads(pin(exported).read_bytes());assert data['target_sha256']==data['imported_sha256']==h
        sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
        pe=PEImage(target.read_bytes());checked=0;missing=[];decompiled=0
        for entry in data['exports']:
            if not entry['present']:missing.append(entry['entry']);continue
            decompiled+=entry['decompile_completed']
            for span in entry['body_ranges']:
                off,_=pe.rva_range(span['start']-pe.image_base,span['length']);raw=pe.data[off:off+span['length']];assert raw.hex()==span['bytes_hex'] and hashlib.sha256(raw).hexdigest()==span['sha256'];checked+=len(raw)
        pin(target,h);pin(__file__);pin(ROOT/'tools/analysis/pe.py')
        runs.append(dict(functions=len(entries),entries=entries,missing=missing,decompiled=decompiled,body_bytes_verified=checked,elapsed_seconds=time.perf_counter()-started,cold_import=False,project=str(project/(title+'.gpr')),database_save=False,command=command,export=str(exported)))
        passed=not missing
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        report=dict(passed=passed,scope='Warm exact-SHA retained Ghidra project function/pseudocode corroboration; literal source rows remain primary and decompiler omissions do not narrow source',runs=runs,cold_imports=0,static_only=True,native_executed=False,original_executed=False,initializer_credit=0,files=pins)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),runs=runs)),flush=True)
if __name__=='__main__':main(sys.argv[1])
