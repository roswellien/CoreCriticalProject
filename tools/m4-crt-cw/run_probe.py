"""Execute immutable authored hardware worker with exact causal diagnostics."""
from pathlib import Path
import argparse,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def need(ok,why):
 if not ok:raise ValueError(why)
def main():
 a=argparse.ArgumentParser();a.add_argument('--build',required=True);a.add_argument('--out',required=True);args=a.parse_args();build=Path(args.build).resolve();out=Path(args.out).resolve();need(out.is_relative_to(ROOT/'reports/m4-crt-cw') and not out.exists(),'Fresh private CW run required');m=json.loads(build.read_text(encoding='utf-8-sig'));need(m['passed'],'Passed CW build')
 for group in ('source_files','tool_files','artifacts'):
  for name,h in m[group].items():need(sha(name)==h,'Exact frozen CW '+group)
 worker=Path(m['worker']);out.mkdir(parents=True);commands=[];passed=False;failure=None
 def run(name,args,exit,diag=None):
  r=subprocess.run([str(worker),*map(str,args)],capture_output=True,timeout=180);so=out/(name+'.stdout');se=out/(name+'.stderr');so.write_bytes(r.stdout);se.write_bytes(r.stderr);commands.append({'name':name,'command':[str(worker),*map(str,args)],'exit_code':r.returncode,'stdout':bind(so),'stderr':bind(se)});need(r.returncode==exit,'Intended CW exit '+name)
  if diag:need(r.stderr.replace(b'\r\n',b'\n')==diag.encode()+b'\n','Exact intended CW diagnostic '+name)
 try:
  raw=out/'original.bin';run('positive',[raw],0);need(raw.stat().st_size==24+131072*2176,'Complete exhaustive CW hardware stream')
  run('hash',['--check-hash'],0);run('bad-cli',[],1,'CW reference: fresh-output');run('extra-argument',[out/'extra.bin','extra'],1,'CW reference: fresh-output');need(not(out/'extra.bin').exists(),'No extra-argument output')
  sentinel=out/'existing.bin';sentinel.write_bytes(b'owned authored CW evidence sentinel\r\n');before=bind(sentinel);run('existing-file',[sentinel],1,'Output exists or cannot establish absence');need(bind(sentinel)==before,'Exact existing CW sentinel preservation')
  directory=out/'existing-directory';directory.mkdir();run('existing-directory',[directory],1,'Output exists or cannot establish absence');need(not list(directory.iterdir()),'No mutation to existing directory')
  need(not list(out.glob('*.crt-stage-*')),'No leftover owned staging');passed=True
 except Exception as e:failure=str(e);raise
 finally:
  report={'passed':passed,'failure':failure,'scope':'Authored FLDCW/FNSTCW hardware normalization only; no vendor/game/native service code','source':bind(__file__),'build':bind(build),'worker':bind(worker),'commands':commands,'raw':bind(raw) if 'raw' in locals() and raw.exists() else None,'records':131072 if passed else None,'actual_causal_controls':5 if passed else None,'whole_M4_complete':False};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files=[x for x in out.rglob('*') if x.is_file()]+[build,worker,Path(__file__)];(out/'pins.json').write_text(json.dumps({'files':{str(x.resolve()):sha(x) for x in files}},indent=2)+'\n')
 print('131072 actual hardware CW records and five admission controls complete; analysis pending')
if __name__=='__main__':main()
