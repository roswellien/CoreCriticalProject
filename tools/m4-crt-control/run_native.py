import argparse,hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def main(build_path,out):
 b=json.loads(build_path.read_text(encoding='utf-8-sig'));assert b['passed'] and not out.exists() and out.is_relative_to(ROOT/'reports/m4-crt-control')
 for k in ('source_files','tool_files','artifacts'):
  for p,h in b[k].items():assert sha(p)==h,(k,p)
 out.mkdir(parents=True);pack=ROOT/'reports/m4-crt-control/research-r1/pack.bin';original=ROOT/'reports/m4-crt-control/original-run-r1/original.bin';assert sha(original)=='dae8247764fcf2261e0bde93d04a7885a01ba3c3f68f68dc361dabb67fcfeb9e';commands=[];controls=[];raws={}
 def call(name,args):
  r=subprocess.run([str(a) for a in args],capture_output=True,timeout=180);so=out/(name+'.stdout');se=out/(name+'.stderr');so.write_bytes(r.stdout);se.write_bytes(r.stderr);commands.append({'name':name,'arguments':[str(a) for a in args],'exit_code':r.returncode,'stdout':str(so),'stdout_sha256':sha(so),'stderr':str(se),'stderr_sha256':sha(se)});return r
 def denied(name,args,message,result=None):
  r=call(name,args);assert r.returncode==1 and r.stdout==b'' and r.stderr.replace(b'\r\n',b'\n')==message.encode()+b'\n',(name,r.returncode,r.stderr)
  if result is not None:assert not result.exists()
  assert not any('.crt-stage-' in p.name for p in out.iterdir());controls.append({'name':name,'intended_diagnostic':message,'passed':True})
 try:
  changed_pack=out/'changed-pack.bin';data=bytearray(pack.read_bytes());data[100]^=1;changed_pack.write_bytes(data);changed_original=out/'changed-original.bin';data=bytearray(original.read_bytes());data[100]^=1;changed_original.write_bytes(data)
  for level,worker in b['workers'].items():
   raw=out/f'native-{level}.bin';r=call('positive-'+level,[worker,pack,original,raw]);assert r.returncode==0 and not r.stderr and r.stdout.replace(b'\r\n',b'\n')==b'3264 actual native complete CRT control records captured; integration pending\n';assert raw.stat().st_size==24+3264*17596;raws[level]={'path':str(raw),'size_bytes':raw.stat().st_size,'sha256':sha(raw)}
   r=call('hash-'+level,[worker,'--check-hash']);assert r.returncode==0 and not r.stderr and r.stdout.replace(b'\r\n',b'\n')==b'2 SHA controls passed\n';controls.append({'name':'hash-'+level,'passed':True})
   denied('bad-cli-'+level,[worker],'CRT control native: exact-pack actual-original fresh-output');denied('extra-'+level,[worker,pack,original,out/'unused','extra'],'CRT control native: exact-pack actual-original fresh-output',out/'unused')
   denied('missing-'+level,[worker,pack,out/'missing',out/'unused'],'Input unavailable',out/'unused');denied('changed-pack-'+level,[worker,changed_pack,original,out/'unused'],'Pack identity rejected',out/'unused');denied('changed-original-'+level,[worker,pack,changed_original,out/'unused'],'Actual original input identity rejected',out/'unused')
   existing=out/f'existing-{level}.bin';sentinel=b'External owned control evidence survives.\n';existing.write_bytes(sentinel);denied('existing-file-'+level,[worker,pack,original,existing],'Output exists or cannot establish absence');assert existing.read_bytes()==sentinel
   directory=out/f'existing-directory-{level}';directory.mkdir();marker=directory/'marker';marker.write_bytes(sentinel);denied('existing-directory-'+level,[worker,pack,original,directory],'Output exists or cannot establish absence');assert marker.read_bytes()==sentinel and list(directory.iterdir())==[marker]
  for k in ('source_files','tool_files','artifacts'):
   for p,h in b[k].items():assert sha(p)==h,(k,p)
  report={'passed':True,'scope':'Actual four-body compiled native CRT control execution; original differential/independent acceptance pending','build_path':str(build_path),'build_sha256':sha(build_path),'original_path':str(original),'original_sha256':sha(original),'raws':raws,'records_per_optimization':3264,'actual_controls':controls,'commands':commands,'whole_M4_complete':False};write(out/'report.json',report);write(out/'pins.json',{'files':{str(p):sha(p) for p in out.rglob('*') if p.is_file()}});print('6528 actual native records and16 causal controls captured')
 except BaseException as e:write(out/'failure.json',{'passed':False,'failure':str(e),'commands':commands,'controls':controls});raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('build',type=pathlib.Path);p.add_argument('output',type=pathlib.Path);a=p.parse_args();main(a.build.resolve(),a.output.resolve())
