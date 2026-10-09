"""Focused, byte-verified warm Ghidra export; no new binary imports."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
GHIDRA=Path('C:/Users/jcbla/AppData/Local/Programs/REA/ghidra_12.1.4_PUBLIC')
JDK=Path('C:/Users/jcbla/AppData/Local/Programs/REA/jdk-21.0.12.1+1')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(out):
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
 old=ROOT/'tools/m4-rea-evaluation/MW34GhidraPilot.java'
 text=old.read_text().split('    @Override public void run()')[0].replace('public class MW34GhidraPilot','public class MW34StringsExport')
 text+='''    @Override public void run() throws Exception {
        String[] args=getScriptArgs();
        Path target=Path.of(args[1]);
        String digest=sha(Files.readAllBytes(target));
        if(!digest.equals(args[2]) || !digest.equalsIgnoreCase(currentProgram.getExecutableSHA256())) throw new IllegalStateException("Target identity mismatch");
        DecompInterface d=new DecompInterface();d.toggleCCode(true);d.toggleSyntaxTree(true);
        if(!d.openProgram(currentProgram))throw new IllegalStateException("Decompiler open failed");
        List<Object> rows=new ArrayList<>();
        try {for(int i=3;i<args.length;i++)rows.add(export(Long.parseLong(args[i],16),d));}finally{d.dispose();}
        Files.writeString(Path.of(args[0]),gson.toJson(map("target_sha256",digest,"imported_sha256",currentProgram.getExecutableSHA256(),"program",currentProgram.getName(),"native_executed",false,"initializer_credit",false,"exports",rows))+"\\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
}
'''
 scriptdir=out/'scripts';scriptdir.mkdir();script=scriptdir/'MW34StringsExport.java';script.write_text(text)
 recovery=ROOT/'reports/m4-strings-source/recovery-r6/report.json';contract=json.loads(recovery.read_text())
 gameentries=sorted(set(e for r in contract['roots'] for e in r['normal']['local_entries']))
 targets=[('game',ROOT/'MW3/Mech3.exe',ROOT/'reports/m4-rea-evaluation/game-headless-r1/project',gameentries),('crt',ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',ROOT/'reports/m4-rea-evaluation/provider-headless-r1/project',[0x78010a6d,0x78002f32,0x78002fab])]
 report=dict(passed=False,static_only=True,native_executed=False,initializer_credit=False,inputs={str(p):sha(p)for p in(old,Path(__file__),recovery,script)},runs=[])
 try:
  for name,target,project,entries in targets:
   digest=sha(target);report['inputs'][str(target)]=digest
   exported=out/(name+'-export.json')
   command=[str(GHIDRA/'support/analyzeHeadless.bat'),str(project),'MW34Pilot','-process',target.name,'-noanalysis','-readOnly','-scriptPath',str(scriptdir),'-postScript',script.name,str(exported),str(target),digest,*[format(x,'x')for x in entries],'-log',str(out/(name+'-ghidra.log')),'-scriptlog',str(out/(name+'-script.log'))]
   start=time.perf_counter()
   with (out/(name+'-console.log')).open('wb')as log:
    p=subprocess.run(command,env=dict(os.environ,JAVA_HOME=str(JDK),GHIDRA_JAVA_HOME=str(JDK)),stdout=log,stderr=subprocess.STDOUT,timeout=300)
   row=dict(name=name,command=command,exit_code=p.returncode,elapsed_seconds=time.perf_counter()-start);report['runs'].append(row)
   assert p.returncode==0 and exported.exists(),row
   data=json.loads(exported.read_text());pe=PEImage(target.read_bytes());checked=0;missing=[]
   for f in data['exports']:
    if not f['present']:missing.append(f['entry']);continue
    for r in f['body_ranges']:
     off,_=pe.rva_range(r['start']-pe.image_base,r['length']);raw=pe.data[off:off+r['length']]
     assert raw.hex()==r['bytes_hex'] and hashlib.sha256(raw).hexdigest()==r['sha256'];checked+=len(raw)
   row.update(export=str(exported),export_sha256=sha(exported),functions=len(data['exports']),body_bytes_verified=checked,missing=missing)
   assert sha(target)==digest
  report['passed']=True
 finally:
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],report=str(out/'report.json'),sha256=sha(out/'report.json'),runs=report['runs'])))
if __name__=='__main__':main(sys.argv[1])
