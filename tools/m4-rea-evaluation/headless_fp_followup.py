"""Read-only saved-project FP export; no duplicate full-program analysis."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 parent=ROOT/'reports/m4-rea-evaluation/game-headless-r1/report.json'
 expected='3fe2990c597a172b0dba4a9080d445ad33bcf35fb31153d8747c9c52e077333b'
 assert sha(parent)==expected
 p=json.loads(parent.read_text());assert p['passed']
 for q,digest in p['files'].items():assert sha(q)==digest
 out=ROOT/'reports/m4-rea-evaluation/game-fp-followup-r1';out.mkdir(exist_ok=False)
 scriptdir=out/'scripts';scriptdir.mkdir()
 source=ROOT/'tools/m4-rea-evaluation/MW34GhidraPilot.java'
 original=source.read_text()
 marker='else if(args[1].equals("provider")) selected=new long[]{0x78004a36L,0x7800151dL};'
 assert original.count(marker)==1
 code=original.replace('public class MW34GhidraPilot extends GhidraScript','public class MW34GhidraFP extends GhidraScript').replace(marker,marker+'\n        else if(args[1].equals("fp")) selected=new long[]{0x4c58c0L,0x4c5960L};')
 script=scriptdir/'MW34GhidraFP.java';script.write_text(code,encoding='utf-8')
 exported=out/'export.json'
 command=[str(Path(p['ghidra'])/'support/analyzeHeadless.bat'),str(parent.parent/'project'),'MW34Pilot','-process','Mech3.exe','-noanalysis','-readOnly','-scriptPath',str(scriptdir),'-postScript',script.name,str(exported),'fp',p['target'],p['target_sha256'],'-log',str(out/'ghidra.log'),'-scriptlog',str(out/'script.log')]
 result=dict(passed=False,parent_report=str(parent),parent_sha256=expected,command=command,native_executed=False,initializer_credit=False,full_analysis_repeated=False,project_changed=False)
 started=time.perf_counter()
 try:
  with (out/'console.log').open('wb')as log:
   run=subprocess.run(command,env=dict(os.environ,JAVA_HOME=p['java_home'],GHIDRA_JAVA_HOME=p['java_home']),stdout=log,stderr=subprocess.STDOUT,timeout=120)
  result.update(wall_seconds=time.perf_counter()-started,exit_code=run.returncode)
  assert run.returncode==0 and exported.exists()
  data=json.loads(exported.read_text());assert data['target_sha256']==p['target_sha256']
  pe=PEImage(Path(p['target']).read_bytes());checked=0
  for f in data['exports']:
   assert f['present'] and f['decompile_completed']
   for body in f['body_ranges']:
    off,_=pe.rva_range(body['start']-pe.image_base,body['length']);actual=pe.data[off:off+body['length']]
    assert actual.hex()==body['bytes_hex'] and hashlib.sha256(actual).hexdigest()==body['sha256']
    checked+=len(actual)
  fp=data['exports'][1];fp_mnemonics=[i['text']for i in fp['instructions']if i['text'].split()[0].upper()in('FLD','FLDZ','FSUB','FSTP','FXCH','FCHS','FADD','FMUL','FCOMP','FNSTSW')]
  assert fp_mnemonics,'representative constructor has no captured x87 instructions'
  result.update(passed=True,functions_exported=2,body_bytes_verified=checked,exports_seconds=data['exports_seconds'],script_seconds=data['script_seconds'],fp_instructions=fp_mnemonics,export_sha256=sha(exported))
 except Exception as e:result['error']=repr(e)
 result['files']={str(q):sha(q)for q in(parent,source,script,Path(__file__),Path(p['target']))}
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(report=str(out/'report.json'),sha256=sha(out/'report.json'),**{k:v for k,v in result.items()if k not in('command','files','fp_instructions')}),indent=2))
 return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
