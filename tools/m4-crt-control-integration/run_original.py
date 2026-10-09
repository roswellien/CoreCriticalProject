"""Actual original connected worker, with exact causal input/publication controls."""
import hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-control-integration'
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def need(v,w):
 if not v:raise ValueError(w)
def run(build,out):
 need(not out.exists() and out.is_relative_to(BASE),'Fresh private connected run required');m=read(build);need(m['passed'],'Passed exact original build')
 for k in ('source_files','tool_files','artifacts'):
  for p,h in m[k].items():need(sha(p)==h,'Frozen original dependency '+p)
 out.mkdir();commands=[];worker=m['worker'];pack=m['pack_path'];provider=m['provider_path'];game=ROOT/'MW3/Mech3.exe';raw=out/'original.bin';args=[pack,provider,str(game),str(raw)]
 def execute(name,argv,diagnostic=None):
  cp=subprocess.run([worker]+argv,capture_output=True,timeout=60);so=out/(name+'.stdout');se=out/(name+'.stderr');so.write_bytes(cp.stdout);se.write_bytes(cp.stderr);commands.append({'name':name,'program':worker,'arguments':argv,'exit_code':cp.returncode,'stdout':str(so),'stdout_sha256':sha(so),'stderr':str(se),'stderr_sha256':sha(se),'expected_diagnostic':diagnostic});need(cp.returncode==(0 if diagnostic is None else 1) and (diagnostic is None or diagnostic in cp.stderr.decode()),'Exact intended actual outcome '+name);return cp
 try:
  execute('positive',args);need(raw.stat().st_size==24+192*10444,'Actual original final extent');controls=[]
  execute('hash',['--check-hash']);controls.append({'name':'hash','passed':True})
  for name,argv,why in [('bad-cli',args[:-1],'Connected control reference: exact-pack exact-provider exact-game fresh-output'),('extra',args+['extra'],'Connected control reference: exact-pack exact-provider exact-game fresh-output'),('missing-pack',[str(out/'absent.bin')]+args[1:],'Input unavailable')]:execute(name,argv,why);controls.append({'name':name,'passed':True,'intended_diagnostic':why})
  for name,index,source,why in [('changed-pack',0,pack,'Pack identity rejected'),('changed-provider',1,provider,'Provider identity rejected'),('changed-game',2,game,'Game identity rejected')]:
   b=bytearray(pathlib.Path(source).read_bytes());b[100]^=1;changed=out/(name+'.bin');changed.write_bytes(b);argv=args.copy();argv[index]=str(changed);argv[-1]=str(out/(name+'-result.bin'));execute(name,argv,why);need(not pathlib.Path(argv[-1]).exists(),'Denied original result absent');controls.append({'name':name,'passed':True,'intended_diagnostic':why})
  for name,directory in [('existing-file',False),('existing-directory',True)]:
   p=out/name
   if directory:p.mkdir();marker=p/'sentinel';marker.write_bytes(b'owned connected sentinel\n')
   else:marker=p;marker.write_bytes(b'owned connected sentinel\n')
   before=marker.read_bytes();execute(name,args[:-1]+[str(p)],'Output exists or cannot establish absence');need(marker.read_bytes()==before,'External destination preserved');controls.append({'name':name,'passed':True,'intended_diagnostic':'Output exists or cannot establish absence'})
 except Exception as e:(out/'failure.json').write_text(json.dumps({'passed':False,'reason':str(e),'commands':commands},indent=2)+'\n');raise
 report={'passed':True,'scope':'Actual original connected game control wrapper/thunk/provider only; native comparison pending','build_path':str(build),'build_sha256':sha(build),'raw':{'path':str(raw),'size_bytes':raw.stat().st_size,'sha256':sha(raw)},'records':192,'actual_controls':controls,'commands':commands,'native_execution_accepted':False,'whole_M4_complete':False};rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');files={str(p.resolve()):sha(p)for p in out.rglob('*')if p.is_file()};files[str(pathlib.Path(__file__).resolve())]=sha(__file__);files[str(build)]=sha(build);(out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n');print('192 actual original connected records captured with9 actual controls',sha(rp))
if __name__=='__main__':run(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve())
