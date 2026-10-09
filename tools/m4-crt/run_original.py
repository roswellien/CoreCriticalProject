"""Run the frozen x86 CRT worker and six causal admission controls, fresh only."""
from pathlib import Path
import argparse,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def need(ok,why):
 if not ok:raise ValueError(why)
def main():
 p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--extraction',required=True);p.add_argument('--out',required=True);a=p.parse_args();build=Path(a.build).resolve();ext=Path(a.extraction).resolve();out=Path(a.out).resolve()
 need(out.is_relative_to(ROOT/'reports/m4-crt') and not out.exists(),'Fresh private original CRT run required');m=json.loads(build.read_text(encoding='utf-8-sig'));need(m['passed'],'Passed original build required')
 for group in ('source_files','tool_files','artifacts'):
  for path,h in m[group].items():need(sha(path)==h,'Exact frozen original '+group)
 worker=Path(m['worker']);pack=ext/'provider-pages.bin';provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';out.mkdir(parents=True);commands=[]
 def run(name,args,code,diagnostic=None):
  r=subprocess.run([str(worker),*map(str,args)],capture_output=True,timeout=180);stdout=out/(name+'.stdout');stderr=out/(name+'.stderr');stdout.write_bytes(r.stdout);stderr.write_bytes(r.stderr)
  commands.append({'name':name,'command':[str(worker),*map(str,args)],'exit_code':r.returncode,'stdout':bind(stdout),'stderr':bind(stderr)});need(r.returncode==code,'Exact exit '+name)
  if diagnostic:need(diagnostic.encode() in r.stderr,'Intended causal diagnostic '+name)
  return r
 passed=False;failure=None
 try:
  result=out/'original.bin';run('positive',[pack,provider,result],0);need(result.stat().st_size==24+1728*18668,'Complete original raw stream')
  run('hash',['--check-hash'],0);run('bad-cli',[],1,'CRT reference: exact-pack exact-provider fresh-output')
  changes=[]
  for name,source,args,diagnostic in [('changed-pack',pack,lambda q:[q,provider,out/'changed-pack.bin'],'Pack identity rejected'),('changed-provider',provider,lambda q:[pack,q,out/'changed-provider.bin'],'Provider identity rejected')]:
   raw=bytearray(source.read_bytes());raw[-1]^=1;q=out/(name+'.input');q.write_bytes(raw);changes.append({'original':bind(source),'changed':bind(q),'changed_offset':len(raw)-1});run(name,args(q),1,diagnostic);need(not (out/(name+'.bin')).exists(),'No result on '+name)
  run('missing-input',[out/'absent.input',provider,out/'missing.bin'],1,'Input unavailable');need(not(out/'missing.bin').exists(),'No missing-input result')
  sentinel=out/'existing.bin';sentinel.write_bytes(b'owned original CRT evidence sentinel\r\n');before=bind(sentinel);run('existing-output',[pack,provider,sentinel],1,'Output exists or cannot establish absence');need(bind(sentinel)==before,'Existing output bytes preserved');need(not list(out.glob('*.crt-stage-*')),'No abandoned worker staging')
  (out/'replay_spec.hpp').write_text('#pragma once\nnamespace mw34::m4_crt_probe { inline constexpr auto original_sha="'+sha(result)+'"; }\n');passed=True
 except Exception as e:failure=str(e);raise
 finally:
  report={'passed':passed,'failure':failure,'scope':'Original staged CRT provider bodies on authored callbacks; no game code or native equivalence','build':bind(build),'extraction':bind(ext/'report.json'),'worker':bind(worker),'provider':bind(provider),'source':bind(__file__),'commands':commands,'changed_inputs':changes if 'changes' in locals() else [],'original_records':1728 if passed else None,'controls':6 if passed else None,'whole_M4_complete':False}
  if (out/'original.bin').exists():report['original']=bind(out/'original.bin')
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files=[x for x in out.iterdir() if x.is_file()]+[build,ext/'report.json',pack,worker,provider,Path(__file__),ROOT/'tools/m4-crt/probe_common.hpp',ROOT/'tools/m4-crt/probe_io.hpp']
  (out/'pins.json').write_text(json.dumps({'files':{str(x.resolve()):sha(x) for x in files}},indent=2)+'\n')
 print('1728 original CRT records and six causal controls passed')
if __name__=='__main__':main()
