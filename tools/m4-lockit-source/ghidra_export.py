"""Warm exact-SHA game decompiler corroboration; no saved metadata or runtime."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
GHIDRA=Path('C:/Users/jcbla/AppData/Local/Programs/REA/ghidra_12.1.4_PUBLIC');JDK=Path('C:/Users/jcbla/AppData/Local/Programs/REA/jdk-21.0.12.1+1')
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-lockit-source'/name;out.mkdir(parents=True,exist_ok=False);pins={};runs=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,v);pins[str(p)]=v;return p
 try:
  source=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/report.json','25a04a5a9e4cec894c5272d398794850aeab968a22f77b21494706680015fa4d').read_bytes());assert source['passed']
  graphs=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/game-new-graphs.json').read_bytes());entries=sorted(int(e)for e in graphs);assert len(entries)==10
  template=pin(ROOT/'reports/m4-container-ghidra/export-r1/scripts/MW34ContainerExport.java');scripts=out/'scripts';scripts.mkdir();script=scripts/'MW34LockitExport.java';script.write_text(template.read_text().replace('MW34ContainerExport','MW34LockitExport'));pin(script)
  target=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');h=sha(target);project=ROOT/'reports/m4-rea-evaluation/game-headless-r1/project';title='MW34Pilot';assert(project/(title+'.gpr')).exists()
  exported=out/'game-export.json';command=[str(GHIDRA/'support/analyzeHeadless.bat'),str(project),title,'-process',target.name,'-noanalysis','-readOnly','-scriptPath',str(scripts),'-postScript',script.name,str(exported),str(target),h,*[format(x,'x')for x in entries],'-log',str(out/'game-ghidra.log'),'-scriptlog',str(out/'game-script.log')]
  started=time.perf_counter()
  with(out/'game-console.log').open('wb')as log:r=subprocess.run(command,env=dict(os.environ,JAVA_HOME=str(JDK),GHIDRA_JAVA_HOME=str(JDK)),stdout=log,stderr=subprocess.STDOUT,timeout=300,creationflags=0x08000000)
  assert r.returncode==0 and exported.exists();data=json.loads(pin(exported).read_bytes());assert data['target_sha256']==data['imported_sha256']==h
  sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
  pe=PEImage(target.read_bytes());checked=0;missing=[];decompiled=0;coverage=[]
  for row in data['exports']:
   if not row['present']:missing.append(row['entry']);continue
   decompiled+=int(row['decompile_completed']);byteaddresses=set()
   for span in row['body_ranges']:
    off,_=pe.rva_range(span['start']-pe.image_base,span['length']);raw=pe.data[off:off+span['length']];assert raw.hex()==span['bytes_hex']and hashlib.sha256(raw).hexdigest()==span['sha256'];checked+=len(raw);byteaddresses.update(range(span['start'],span['start']+span['length']))
   physical={a for q in graphs[str(row['entry'])]['instructions']for a in range(q['pc'],q['pc']+q['size'])};coverage.append(dict(entry=row['entry'],literal_source_bytes=len(physical),Ghidra_body_bytes=len(byteaddresses),source_bytes_contained=len(physical&byteaddresses),source_bytes_not_in_Ghidra_body=len(physical-byteaddresses),Ghidra_not_a_source_narrowing_authority=True))
  pin(target,h);pin(__file__);pin(ROOT/'tools/analysis/pe.py');runs.append(dict(functions=len(entries),entries=entries,missing=missing,decompiled=decompiled,body_bytes_verified=checked,elapsed_seconds=time.perf_counter()-started,cold_import=False,project=str(project/(title+'.gpr')),database_save=False,command=command,export=str(exported),source_coverage=coverage));passed=not missing and decompiled==len(entries)
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Warm readOnly Ghidra exact game function/pseudocode corroboration. Literal physical303rows1048B and persistent execution remain primary; no providerDLL export/runtimecredit.',runs=runs,cold_imports=0,provider_export=False,static_only=True,native_executed=False,original_executed=False,initializer_credit=0,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),runs=[{k:v for k,v in row.items()if k not in('command','source_coverage')}for row in runs])),flush=True)
if __name__=='__main__':main(sys.argv[1])
