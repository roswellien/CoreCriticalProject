"""Actual isolated original capture and causal input/output admissions."""
from pathlib import Path
import hashlib,json,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[3]
def need(ok,w):
 if not ok:raise ValueError(w)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(build,out):
 need(out.is_relative_to(ROOT/'reports/m4-crt-matherr') and not out.exists(),'Fresh entire original run')
 b=json.loads(build.read_text(encoding='utf-8-sig'));need(b['passed'],'Passing original build')
 for k in ('source_files','tool_files','artifacts'):
  for p,h in b[k].items():need(sha(p)==h,'Frozen original build dependency '+p)
 out.mkdir(parents=True);(out/'run-source.py').write_bytes(Path(__file__).read_bytes());commands=[]
 def call(name,args,why=None):
  q=subprocess.run([b['worker'],*args],capture_output=True,timeout=180);stdout=out/(name+'.stdout');stderr=out/(name+'.stderr');stdout.write_bytes(q.stdout);stderr.write_bytes(q.stderr)
  commands.append({'name':name,'program':b['worker'],'program_sha256':sha(b['worker']),'arguments':args,'exit_code':q.returncode,'stdout':str(stdout),'stdout_sha256':sha(stdout),'stderr':str(stderr),'stderr_sha256':sha(stderr),'expected_diagnostic':why})
  need(q.returncode==(1 if why else 0),'Exact actual original exit '+name)
  if why:need(why.encode() in q.stderr,'Intended original diagnostic '+name)
  return q
 try:
  raw=out/'original.bin';args=[b['pack_path'],b['provider_path'],str(ROOT/'MW3/Mech3.exe'),str(raw)];call('positive',args)
  need(raw.stat().st_size==24+1536*26836,'Complete original protocol extent');controls=[]
  call('hash',['--check-hash']);controls.append({'name':'hash','passed':True})
  for name,argv,why in [('bad-cli',args[:-1],'Matherr original: exact-pack exact-provider exact-game fresh-output'),('extra',args+['extra'],'Matherr original: exact-pack exact-provider exact-game fresh-output'),('missing-pack',[str(out/'absent.bin')]+args[1:-1]+[str(out/'missing-result.bin')],'Input unavailable')]:call(name,argv,why);controls.append({'name':name,'passed':True,'intended_diagnostic':why})
  for name,index,why in [('changed-pack',0,'Pack identity rejected'),('changed-provider',1,'Provider identity rejected'),('changed-game',2,'Game identity rejected')]:
   data=bytearray(Path(args[index]).read_bytes());data[100]^=1;bad=out/(name+'.bin');bad.write_bytes(data);argv=args.copy();argv[index]=str(bad);argv[-1]=str(out/(name+'-result.bin'));call(name,argv,why);need(not Path(argv[-1]).exists(),'Denied original new result absent');controls.append({'name':name,'passed':True,'intended_diagnostic':why})
  for name,directory in [('existing-file',False),('existing-directory',True)]:
   dest=out/name
   if directory:dest.mkdir();marker=dest/'sentinel'
   else:marker=dest
   marker.write_bytes(b'matherr original owned sentinel\n');call(name,args[:-1]+[str(dest)],'Output exists or cannot establish absence');need(marker.read_bytes()==b'matherr original owned sentinel\n','Prior original destination sentinel survives');controls.append({'name':name,'passed':True,'intended_diagnostic':'Output exists or cannot establish absence'})
  report={'passed':True,'scope':'Actual original isolated complete four-instruction matherr leaf; callback not invoked, static CRT call not executed','build_path':str(build),'build_sha256':sha(build),'raw':{'path':str(raw),'sha256':sha(raw),'size_bytes':raw.stat().st_size},'records':1536,'record_stride':26836,'commands':commands,'actual_controls':controls,'native_equivalence_accepted':False,'whole_M4_complete':False}
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
  pins={str(p.resolve()):sha(p) for p in out.rglob('*') if p.is_file()};pins[str(build)]=sha(build);pins[str(Path(__file__).resolve())]=sha(__file__);(out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n')
  print(json.dumps({'passed':True,'records':1536,'actual_controls':len(controls),'raw_sha256':sha(raw),'report_sha256':sha(out/'report.json')}))
 except Exception:
  (out/'failure.json').write_text(json.dumps({'passed':False,'commands':commands,'exception':traceback.format_exc()},indent=2)+'\n');raise
if __name__=='__main__':run(*(Path(x).resolve() for x in sys.argv[1:3]))
