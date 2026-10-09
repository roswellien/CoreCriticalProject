"""Run exact compiled guest-CW workers; retain intended admission diagnostics."""
import argparse, hashlib, json, pathlib, shutil, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def run(build_path,out):
 build=json.loads(build_path.read_text(encoding='utf-8-sig'));assert build['passed']
 for group in ('source_files','tool_files','artifacts'):
  for p,h in build[group].items():assert sha(p)==h,(group,p)
 assert sha(build['hardware_path'])==build['hardware_sha256']
 assert not out.exists();out.mkdir(parents=True)
 hardware=pathlib.Path(build['hardware_path']);folder=pathlib.Path(build['build_directory']);commands=[];controls=[];raws={}
 def call(name,args):
  r=subprocess.run([str(a) for a in args],capture_output=True,timeout=180)
  so=out/(name+'.stdout');se=out/(name+'.stderr');so.write_bytes(r.stdout);se.write_bytes(r.stderr)
  row={'name':name,'arguments':[str(a) for a in args],'exit_code':r.returncode,'stdout':str(so),'stdout_sha256':sha(so),'stderr':str(se),'stderr_sha256':sha(se)};commands.append(row);return r
 def denied(name,args,diagnostic,result=None):
  before=set(out.iterdir());r=call(name,args);assert r.returncode==1 and r.stdout==b'' and r.stderr.replace(b'\r\n',b'\n')==diagnostic.encode()+b'\n',(name,r.returncode,r.stderr)
  if result is not None:assert not result.exists()
  assert not any('.crt-stage-' in p.name for p in out.iterdir())
  controls.append({'name':name,'intended_diagnostic':diagnostic,'passed':True})
 try:
  changed=out/'changed-hardware.bin';shutil.copyfile(hardware,changed)
  with changed.open('r+b') as f:f.seek(40);b=f.read(1);f.seek(40);f.write(bytes([b[0]^1]))
  for level in ('O0','O2'):
   worker=folder/f'mw34_guest_cw_replay_{level}.exe';raw=out/f'native-{level}.bin';r=call('positive-'+level,[worker,hardware,raw]);assert r.returncode==0 and r.stderr==b'' and r.stdout.replace(b'\r\n',b'\n')==b'65536 actual native guest CW outputs; numerical/provider integration pending\n'
   assert raw.stat().st_size==24+65536*8120;raws[level]={'path':str(raw),'size_bytes':raw.stat().st_size,'sha256':sha(raw)}
   r=call('hash-'+level,[worker,'--check-hash']);assert r.returncode==0 and r.stderr==b'' and r.stdout.replace(b'\r\n',b'\n')==b'2 SHA controls passed\n';controls.append({'name':'hash-'+level,'passed':True})
   denied('bad-cli-'+level,[worker],'Guest CW replay: exact-hardware-prestates fresh-output')
   denied('extra-'+level,[worker,hardware,out/'unused', 'extra'],'Guest CW replay: exact-hardware-prestates fresh-output',out/'unused')
   denied('missing-'+level,[worker,out/'missing',out/'unused'],'Input unavailable',out/'unused')
   denied('changed-'+level,[worker,changed,out/'unused'],'Exact hardware input identity rejected',out/'unused')
   existing=out/f'existing-{level}.bin';sentinel=b'External owned CW evidence must survive.\n';existing.write_bytes(sentinel)
   denied('existing-file-'+level,[worker,hardware,existing],'Output exists or cannot establish absence');assert existing.read_bytes()==sentinel
   directory=out/f'existing-directory-{level}';directory.mkdir();marker=directory/'marker';marker.write_bytes(sentinel)
   denied('existing-directory-'+level,[worker,hardware,directory],'Output exists or cannot establish absence');assert marker.read_bytes()==sentinel and list(directory.iterdir())==[marker]
  for group in ('source_files','tool_files','artifacts'):
   for p,h in build[group].items():assert sha(p)==h,(group,p)
  report={'passed':True,'scope':'Actual native typed CW transfer only; no original/provider/numerical execution','build_path':str(build_path),'build_sha256':sha(build_path),'hardware_path':str(hardware),'hardware_sha256':sha(hardware),'raws':raws,'actual_controls':controls,'commands':commands,'whole_M4_complete':False}
  write(out/'report.json',report);write(out/'pins.json',{str(p):sha(p) for p in sorted(out.rglob('*')) if p.is_file()})
 except BaseException as e:
  write(out/'failure.json',{'passed':False,'failure':str(e),'commands':commands,'controls':controls});raise
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('build',type=pathlib.Path);a.add_argument('output',type=pathlib.Path);v=a.parse_args();run(v.build.resolve(),v.output.resolve())
