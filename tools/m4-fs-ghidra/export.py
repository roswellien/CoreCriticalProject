"""Focused warm exact-image Ghidra exports for the six normal FS roots."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
GHIDRA=Path('C:/Users/jcbla/AppData/Local/Programs/REA/ghidra_12.1.4_PUBLIC')
JDK=Path('C:/Users/jcbla/AppData/Local/Programs/REA/jdk-21.0.12.1+1')
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-fs-ghidra'/name;out.mkdir(parents=True,exist_ok=False);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 acceptance=json.loads(pin(ROOT/'reports/m4-joint-startup103-root/acceptance-r1/report.json','13cc2567f30f2dae2d12991a3a76aa6c953c70a49148dc4ed13df34837b14c7c').read_bytes());assert acceptance['passed']and acceptance['connected_roots']==103
 plan=json.loads(pin(ROOT/'reports/m4-mfc-source/normal-FS-plan-r1/plan.json','9b6cfa03ae9a0ffbdb85ccd1042baa54e21e0f2bdf5c3e276e986cdab44558bd').read_bytes());entries=sorted({e for r in plan['roots']for e in r['local_entries']});assert len(entries)==21
 prior=pin(ROOT/'tools/m4-rea-evaluation/MW34GhidraPilot.java');body=prior.read_text().split('    @Override public void run()')[0].replace('public class MW34GhidraPilot','public class MW34FsExport')
 body+='''    @Override public void run() throws Exception {
        String[] args=getScriptArgs();
        String digest=sha(Files.readAllBytes(Path.of(args[1])));
        if(!digest.equals(args[2]) || !digest.equalsIgnoreCase(currentProgram.getExecutableSHA256())) throw new IllegalStateException("Exact target identity mismatch");
        DecompInterface d=new DecompInterface();d.toggleCCode(true);d.toggleSyntaxTree(true);
        if(!d.openProgram(currentProgram))throw new IllegalStateException("Decompiler open failed");
        List<Object> rows=new ArrayList<>();
        try {for(int i=3;i<args.length;i++)rows.add(export(Long.parseLong(args[i],16),d));}finally{d.dispose();}
        Files.writeString(Path.of(args[0]),gson.toJson(map("target_sha256",digest,"imported_sha256",currentProgram.getExecutableSHA256(),"program",currentProgram.getName(),"native_executed",false,"initializer_credit",false,"exports",rows))+"\\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
}
'''
 scripts=out/'scripts';scripts.mkdir();script=scripts/'MW34FsExport.java';script.write_text(body);pin(script)
 target=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');digest=sha(target)
 project=ROOT/'reports/m4-rea-evaluation/game-headless-r1/project';assert(project/'MW34Pilot.gpr').exists();exported=out/'game-export.json'
 command=[str(GHIDRA/'support/analyzeHeadless.bat'),str(project),'MW34Pilot','-process',target.name,'-noanalysis','-readOnly','-scriptPath',str(scripts),'-postScript',script.name,str(exported),str(target),digest,*[format(x,'x')for x in entries],'-log',str(out/'game-ghidra.log'),'-scriptlog',str(out/'game-script.log')]
 started=time.perf_counter();passed=False;checked=0;missing=[]
 try:
  with(out/'console.log').open('wb')as log:completed=subprocess.run(command,env=dict(os.environ,JAVA_HOME=str(JDK),GHIDRA_JAVA_HOME=str(JDK)),stdout=log,stderr=subprocess.STDOUT,timeout=300)
  assert completed.returncode==0 and exported.exists();data=json.loads(pin(exported).read_bytes());pe=PEImage(target.read_bytes())
  assert data['target_sha256']==data['imported_sha256']==digest
  for f in data['exports']:
   if not f['present']:missing.append(f['entry']);continue
   for span in f['body_ranges']:
    offset,_=pe.rva_range(span['start']-pe.image_base,span['length']);raw=pe.data[offset:offset+span['length']]
    assert raw.hex()==span['bytes_hex']and hashlib.sha256(raw).hexdigest()==span['sha256'];checked+=len(raw)
  pin(target,digest);pin(__file__);passed=True
 finally:
  r=dict(passed=passed,scope='Warm saved exact-SHA game Ghidra functions/pseudocode and complete body-range byte verification; literal source recovery remains primary for tails and reached paths',functions=len(entries),missing=missing,body_bytes_verified=checked,elapsed_seconds=time.perf_counter()-started,cold_imports=0,project_reused=str(project/'MW34Pilot.gpr'),command=command,static_only=True,native_executed=False,original_executed=False,initializer_credit=0,files=pins)
  (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k]for k in('passed','functions','missing','body_bytes_verified','elapsed_seconds','cold_imports')}),flush=True)
if __name__=='__main__':main(sys.argv[1])
