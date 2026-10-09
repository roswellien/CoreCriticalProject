"""Byte-checked focused game/MFC exports; save the first MFC project for reuse."""
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
 out=ROOT/'reports/m4-mfc-ghidra'/name;out.mkdir(parents=True,exist_ok=False)
 prior=ROOT/'tools/m4-rea-evaluation/MW34GhidraPilot.java'
 body=prior.read_text().split('    @Override public void run()')[0].replace('public class MW34GhidraPilot','public class MW34MfcExport')
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
 scripts=out/'scripts';scripts.mkdir();script=scripts/'MW34MfcExport.java';script.write_text(body)
 closure=ROOT/'reports/m4-strings-native/next-mfc-r1/game-closure.json';gameentries=json.loads(closure.read_bytes())['entries']
 local=ROOT/'reports/m4-strings-native/next-mfc-r1/provider-local.json';provider=json.loads(local.read_bytes());mfcentries=[provider[k]['entry']for k in('ordinal823','ordinal825')]
 mfcproject=ROOT/'reports/m4-mfc-ghidra/mfc-project';cold=not(mfcproject/'MW34Mfc.gpr').exists();mfcproject.mkdir(parents=True,exist_ok=True)
 targets=[('game',ROOT/'MW3/Mech3.exe',ROOT/'reports/m4-rea-evaluation/game-headless-r1/project','MW34Pilot',gameentries,False),('mfc',ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL',mfcproject,'MW34Mfc',mfcentries,cold)]
 report=dict(passed=False,static_only=True,native_executed=False,initializer_credit=False,cold_imports=int(cold),files={str(p):sha(p)for p in(prior,Path(__file__),closure,local,script)},runs=[])
 try:
  for label,target,project,projectname,entries,is_cold in targets:
   digest=sha(target);report['files'][str(target)]=digest;exported=out/(label+'-export.json')
   command=[str(GHIDRA/'support/analyzeHeadless.bat'),str(project),projectname]
   command+=['-import',str(target)]if is_cold else ['-process',target.name,'-noanalysis','-readOnly']
   command+=['-scriptPath',str(scripts),'-postScript',script.name,str(exported),str(target),digest,*[format(x,'x')for x in entries],'-log',str(out/(label+'-ghidra.log')),'-scriptlog',str(out/(label+'-script.log'))]
   started=time.perf_counter()
   with(out/(label+'-console.log')).open('wb')as log:
    completed=subprocess.run(command,env=dict(os.environ,JAVA_HOME=str(JDK),GHIDRA_JAVA_HOME=str(JDK)),stdout=log,stderr=subprocess.STDOUT,timeout=600)
   row=dict(name=label,command=command,exit_code=completed.returncode,elapsed_seconds=time.perf_counter()-started,cold_import=is_cold);report['runs'].append(row)
   assert completed.returncode==0 and exported.exists(),row
   data=json.loads(exported.read_bytes());pe=PEImage(target.read_bytes());checked=0;missing=[]
   for f in data['exports']:
    if not f['present']:missing.append(f['entry']);continue
    for span in f['body_ranges']:
     offset,_=pe.rva_range(span['start']-pe.image_base,span['length']);raw=pe.data[offset:offset+span['length']]
     assert raw.hex()==span['bytes_hex'] and hashlib.sha256(raw).hexdigest()==span['sha256'];checked+=len(raw)
   row.update(export=str(exported),export_sha256=sha(exported),functions=len(data['exports']),body_bytes_verified=checked,missing=missing)
   report['files'][str(exported)]=sha(exported);assert sha(target)==digest
   print(json.dumps({k:row[k]for k in('name','elapsed_seconds','cold_import','functions','missing','body_bytes_verified')}),flush=True)
  report['passed']=True
 finally:
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],report=str(out/'report.json'),sha256=sha(out/'report.json'))),flush=True)
if __name__=='__main__':main(sys.argv[1])
