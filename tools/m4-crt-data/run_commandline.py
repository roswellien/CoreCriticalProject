"""Isolated exact original provider execution with causal admission controls."""
import argparse,hashlib,json,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main(build_path,out):
 b=json.loads(build_path.read_text(encoding='utf-8-sig'));assert b['passed'];assert not out.exists() and out.is_relative_to(ROOT/'reports/m4-crt-data')
 for k in ('source_files','tool_files','artifacts'):
  for p,h in b[k].items():assert sha(p)==h,(k,p)
 out.mkdir(parents=True);worker=pathlib.Path(b['worker']);pack=pathlib.Path(b['pack_path']);provider=pathlib.Path(b['provider_path']);assert sha(pack)==b['pack_sha256'] and sha(provider)==b['provider_sha256'];commands=[];controls=[]
 def call(name,args):
  r=subprocess.run([str(a) for a in args],capture_output=True,timeout=180);so=out/(name+'.stdout');se=out/(name+'.stderr');so.write_bytes(r.stdout);se.write_bytes(r.stderr);commands.append({'name':name,'arguments':[str(a) for a in args],'exit_code':r.returncode,'stdout':str(so),'stdout_sha256':sha(so),'stderr':str(se),'stderr_sha256':sha(se)});return r
 def denied(name,args,message,result=None):
  r=call(name,args);lines=r.stderr.decode().splitlines();assert r.returncode==1 and r.stdout==b'' and lines.count(message)==1,(name,r.returncode,lines)
  if result is not None:assert not result.exists()
  assert not any('.crt-stage-' in p.name for p in out.iterdir());controls.append({'name':name,'intended_diagnostic':message,'passed':True})
 try:
  raw=out/'original.bin';r=call('positive',[worker,pack,provider,raw]);assert r.returncode==0 and r.stdout.replace(b'\r\n',b'\n')==b'192 actual original command-line writer observations captured; full DllMain and native admission pending\n';assert re.fullmatch(rb'Original broker parent mapping: [^\r\n]+\r?\nOriginal broker child finished: pid=\d+ exit=0\r?\n',r.stderr);assert raw.stat().st_size>44+192*18636
  r=call('hash',[worker,'--check-hash']);assert r.returncode==0 and not r.stderr and r.stdout.replace(b'\r\n',b'\n')==b'2 SHA controls passed\n';controls.append({'name':'hash','passed':True})
  denied('bad-cli',[worker],'CRT command-line reference: exact-pack exact-provider fresh-output');denied('extra',[worker,pack,provider,out/'unused','extra'],'CRT command-line reference: exact-pack exact-provider fresh-output',out/'unused')
  denied('missing-pack',[worker,out/'missing',provider,out/'unused'],'Input unavailable',out/'unused')
  changed=out/'changed-pack.bin';data=bytearray(pack.read_bytes());data[100]^=1;changed.write_bytes(data);denied('changed-pack',[worker,changed,provider,out/'unused'],'Pack identity rejected',out/'unused')
  changed_provider=out/'changed-provider.bin';data=bytearray(provider.read_bytes());data[100]^=1;changed_provider.write_bytes(data);denied('changed-provider',[worker,pack,changed_provider,out/'unused'],'Provider identity rejected',out/'unused')
  existing=out/'existing.bin';sentinel=b'External control provider evidence survives.\n';existing.write_bytes(sentinel);denied('existing-file',[worker,pack,provider,existing],'Output exists or cannot establish absence');assert existing.read_bytes()==sentinel
  directory=out/'existing-directory';directory.mkdir();marker=directory/'marker';marker.write_bytes(sentinel);denied('existing-directory',[worker,pack,provider,directory],'Output exists or cannot establish absence');assert marker.read_bytes()==sentinel and list(directory.iterdir())==[marker]
  for k in ('source_files','tool_files','artifacts'):
   for p,h in b[k].items():assert sha(p)==h,(k,p)
  report={'passed':True,'scope':'Actual original initialization writer fragment with real GetCommandLineA; full DllMain and native admission pending','build_path':str(build_path),'build_sha256':sha(build_path),'raw':{'path':str(raw),'size_bytes':raw.stat().st_size,'sha256':sha(raw)},'records':192,'actual_controls':controls,'commands':commands,'whole_M4_complete':False};write(out/'report.json',report);write(out/'pins.json',{'files':{str(p):sha(p) for p in out.rglob('*') if p.is_file()}});print('192 actual original writer records and8 causal controls captured')
 except BaseException as e:write(out/'failure.json',{'passed':False,'failure':str(e),'commands':commands,'controls':controls});raise
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('build',type=pathlib.Path);a.add_argument('out',type=pathlib.Path);v=a.parse_args();main(v.build.resolve(),v.out.resolve())
