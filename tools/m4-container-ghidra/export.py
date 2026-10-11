"""Warm exact-image game/MFC exports for the additive seven-root batch."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
GHIDRA=Path('C:/Users/jcbla/AppData/Local/Programs/REA/ghidra_12.1.4_PUBLIC')
JDK=Path('C:/Users/jcbla/AppData/Local/Programs/REA/jdk-21.0.12.1+1')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-container-ghidra'/name;out.mkdir(parents=True,exist_ok=False);pins={};runs=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;assert str(p) not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 acceptance=json.loads(pin(ROOT/'reports/m4-joint-startup109-root/acceptance-r1/report.json','697765f750209d9bee79541b973494dca89692f4ec630057d282cbbb450266e0').read_bytes());assert acceptance['passed'] and acceptance['connected_roots']==109
 plan=json.loads(pin(ROOT/'reports/m4-fs-next-plan/plan-r3/plan.json','3b36152e670f08e6d030daa89537941ed63f25ebac65a49dd4eec4f1a4f31c81').read_bytes());assert len(plan['game_local_entry_union'])==23 and len(plan['new_provider_entries'])==2
 old=pin(ROOT/'reports/m4-fs-ghidra/export-r1/scripts/MW34FsExport.java');scripts=out/'scripts';scripts.mkdir();script=scripts/'MW34ContainerExport.java';script.write_text(old.read_text().replace('MW34FsExport','MW34ContainerExport'));pin(script)
 targets=[('game',ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf',ROOT/'reports/m4-rea-evaluation/game-headless-r1/project','MW34Pilot',plan['game_local_entry_union']),('mfc',ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8',ROOT/'reports/m4-mfc-ghidra/mfc-project','MW34Mfc',plan['new_provider_entries'])]
 try:
  for label,target,h,project,title,entries in targets:
   target=pin(target,h);assert(project/(title+'.gpr')).exists();exported=out/(label+'-export.json')
   command=[str(GHIDRA/'support/analyzeHeadless.bat'),str(project),title,'-process',target.name,'-noanalysis','-readOnly','-scriptPath',str(scripts),'-postScript',script.name,str(exported),str(target),h,*[format(x,'x') for x in entries],'-log',str(out/(label+'-ghidra.log')),'-scriptlog',str(out/(label+'-script.log'))]
   started=time.perf_counter()
   with(out/(label+'-console.log')).open('wb') as log:r=subprocess.run(command,env=dict(os.environ,JAVA_HOME=str(JDK),GHIDRA_JAVA_HOME=str(JDK)),stdout=log,stderr=subprocess.STDOUT,timeout=300)
   assert r.returncode==0 and exported.exists();data=json.loads(pin(exported).read_bytes());assert data['target_sha256']==data['imported_sha256']==h;pe=PEImage(target.read_bytes());checked=0;missing=[]
   for entry in data['exports']:
    if not entry['present']:missing.append(entry['entry']);continue
    for span in entry['body_ranges']:
     off,_=pe.rva_range(span['start']-pe.image_base,span['length']);raw=pe.data[off:off+span['length']];assert raw.hex()==span['bytes_hex'] and hashlib.sha256(raw).hexdigest()==span['sha256'];checked+=len(raw)
   pin(target,h);row=dict(name=label,functions=len(entries),missing=missing,body_bytes_verified=checked,elapsed_seconds=time.perf_counter()-started,cold_import=False,project=str(project/(title+'.gpr')),command=command,export=str(exported));runs.append(row);print(json.dumps({k:row[k] for k in ('name','functions','missing','body_bytes_verified','elapsed_seconds')}),flush=True)
  pin(__file__);pin(ROOT/'tools/analysis/pe.py');passed=True
 finally:
  report=dict(passed=passed,scope='Warm saved exact-SHA game/MFC functions and decompiler exports, body bytes checked against literal PE; missing exact-entry functions remain explicit',runs=runs,cold_imports=0,static_only=True,native_executed=False,original_executed=False,initializer_credit=False,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))),flush=True)
if __name__=='__main__':main(sys.argv[1])
