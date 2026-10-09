"""Actual compiled connected bodies and causal native worker admission controls."""
import hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-control-integration'
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def need(v,w):
 if not v:raise ValueError(w)
def run(build,original,out):
 need(not out.exists() and out.is_relative_to(BASE),'Fresh private native run');m=read(build);om=read(original);need(m['passed'] and om['passed'],'Exact passed build/original')
 for k in ('source_files','tool_files','artifacts'):
  for p,h in m[k].items():need(sha(p)==h,'Frozen native dependency '+p)
 need(sha(om['raw']['path'])==om['raw']['sha256'],'Exact original input')
 out.mkdir();commands=[];controls=[];raws={};pack=BASE/'research-r1/pack.bin';provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';game=ROOT/'MW3/Mech3.exe'
 def execute(level,name,worker,args,diagnostic=None):
  cp=subprocess.run([worker]+args,capture_output=True,timeout=60);so=out/(level+'-'+name+'.stdout');se=out/(level+'-'+name+'.stderr');so.write_bytes(cp.stdout);se.write_bytes(cp.stderr);commands.append({'level':level,'name':name,'program':worker,'arguments':args,'exit_code':cp.returncode,'stdout':str(so),'stdout_sha256':sha(so),'stderr':str(se),'stderr_sha256':sha(se),'expected_diagnostic':diagnostic});need(cp.returncode==(0 if diagnostic is None else 1) and (diagnostic is None or cp.stderr.decode().strip()==diagnostic),'Exact intended native outcome '+level+' '+name)
 try:
  for level,worker in m['workers'].items():
   raw=out/('native-'+level+'.bin');args=[str(pack),om['raw']['path'],str(provider),str(game),str(raw)];execute(level,'positive',worker,args);need(raw.stat().st_size==24+192*17764,'Actual native final extent');raws[level]={'path':str(raw),'sha256':sha(raw),'size_bytes':raw.stat().st_size}
   execute(level,'hash',worker,['--check-hash']);controls.append({'level':level,'name':'hash','passed':True})
   for name,argv,why in [('bad-cli',args[:-1],'Connected control native: exact-pack actual-original exact-provider exact-game fresh-output'),('extra',args+['extra'],'Connected control native: exact-pack actual-original exact-provider exact-game fresh-output'),('missing-pack',[str(out/'absent.bin')]+args[1:],'Input unavailable')]:execute(level,name,worker,argv,why);controls.append({'level':level,'name':name,'passed':True,'intended_diagnostic':why})
   for name,index,source,why in [('changed-pack',0,pack,'Pack identity rejected'),('changed-original',1,om['raw']['path'],'Actual original input identity rejected'),('changed-provider',2,provider,'Provider identity rejected'),('changed-game',3,game,'Game identity rejected')]:
    p=out/(level+'-'+name+'.bin');b=bytearray(pathlib.Path(source).read_bytes());b[100]^=1;p.write_bytes(b);argv=args.copy();argv[index]=str(p);argv[-1]=str(out/(level+'-'+name+'-result.bin'));execute(level,name,worker,argv,why);need(not pathlib.Path(argv[-1]).exists(),'Denied native result absent');controls.append({'level':level,'name':name,'passed':True,'intended_diagnostic':why})
   for name,directory in [('existing-file',False),('existing-directory',True)]:
    p=out/(level+'-'+name)
    if directory:p.mkdir();marker=p/'sentinel';marker.write_bytes(b'owned native connected sentinel\n')
    else:marker=p;marker.write_bytes(b'owned native connected sentinel\n')
    b=marker.read_bytes();execute(level,name,worker,args[:-1]+[str(p)],'Output exists or cannot establish absence');need(marker.read_bytes()==b,'External native destination preserved');controls.append({'level':level,'name':name,'passed':True,'intended_diagnostic':'Output exists or cannot establish absence'})
 except Exception as e:(out/'failure.json').write_text(json.dumps({'passed':False,'reason':str(e),'commands':commands},indent=2)+'\n');raise
 report={'passed':True,'scope':'Actual complete static game/provider execution with r9 typed tail-frame port; differential acceptance pending','build_path':str(build),'build_sha256':sha(build),'original_report_path':str(original),'original_report_sha256':sha(original),'original_raw_sha256':om['raw']['sha256'],'raws':raws,'records_per_level':192,'actual_controls':controls,'commands':commands,'whole_M4_complete':False};rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');files={str(p.resolve()):sha(p)for p in out.rglob('*')if p.is_file()};files[str(pathlib.Path(__file__).resolve())]=sha(__file__);files[str(build)]=sha(build);files[str(original)]=sha(original);(out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n');print('384 actual native connected records;20 actual controls',sha(rp))
if __name__=='__main__':run(*(pathlib.Path(a).resolve()for a in sys.argv[1:4]))
