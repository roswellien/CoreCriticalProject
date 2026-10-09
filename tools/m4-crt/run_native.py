"""Fresh native O0/O2 provider replay and intended-diagnostic admission controls."""
from pathlib import Path
import argparse,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def need(ok,why):
 if not ok:raise ValueError(why)
def main():
 p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--original',required=True);p.add_argument('--out',required=True);a=p.parse_args();build=Path(a.build).resolve();raw=Path(a.original).resolve();out=Path(a.out).resolve()
 need(out.is_relative_to(ROOT/'reports/m4-crt') and not out.exists(),'Fresh private native CRT run required');m=json.loads(build.read_text(encoding='utf-8-sig'));need(m['passed'],'Passed native build required')
 for group in ('source_files','tool_files','artifacts'):
  for path,h in m[group].items():need(sha(path)==h,'Exact frozen native '+group)
 provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';folder=Path(next(x['arguments'][x['arguments'].index('-B')+1] for x in m['commands'] if '-B' in x['arguments']));out.mkdir(parents=True);commands=[];streams=[];passed=False;failure=None
 def run(worker,name,args,code,diagnostic=None):
  result=subprocess.run([str(worker),*map(str,args)],capture_output=True,timeout=180);stdout=out/(name+'.stdout');stderr=out/(name+'.stderr');stdout.write_bytes(result.stdout);stderr.write_bytes(result.stderr);commands.append({'name':name,'worker':bind(worker),'command':[str(worker),*map(str,args)],'exit_code':result.returncode,'stdout':bind(stdout),'stderr':bind(stderr)})
  need(result.returncode==code,'Exact exit '+name)
  if diagnostic:need(result.stderr.replace(b'\r\n',b'\n')==diagnostic.encode()+b'\n','Exact intended causal diagnostic '+name)
 try:
  for level in ('O0','O2'):
   worker=folder/('mw34_m4_crt_replay_'+level+'.exe');output=out/(level+'.bin');ledger=out/(level+'-ledger.json');run(worker,level+'-positive',[provider,raw,output,ledger],0);need(output.stat().st_size==24+1728*17588,'Complete native stream '+level);streams.append({'level':level,'raw':bind(output),'ledger':bind(ledger)})
   run(worker,level+'-hash',['--check-hash'],0);run(worker,level+'-bad-cli',[],1,'CRT replay: exact-provider exact-original-prestates fresh-raw fresh-ledger')
   for name,source,diagnostic in [('changed-provider',provider,'Provider identity rejected'),('changed-original',raw,'Original input identity rejected')]:
    q=out/(level+'-'+name+'.input');data=bytearray(source.read_bytes());data[-1]^=1;q.write_bytes(data);r=out/(level+'-'+name+'.bin');l=out/(level+'-'+name+'.json');args=[q if name=='changed-provider' else provider,q if name=='changed-original' else raw,r,l];run(worker,level+'-'+name,args,1,diagnostic);need(not r.exists() and not l.exists(),'No partial outputs on causal denial')
   run(worker,level+'-missing',[out/'absent.input',raw,out/(level+'-missing.bin'),out/(level+'-missing.json')],1,'Input unavailable');need(not(out/(level+'-missing.bin')).exists() and not(out/(level+'-missing.json')).exists(),'No missing-input outputs')
   sentinel=out/(level+'-existing.bin');sentinel.write_bytes(b'owned native CRT evidence sentinel\r\n');before=bind(sentinel);run(worker,level+'-existing',[provider,raw,sentinel,out/(level+'-existing.json')],1,'Output exists or cannot establish absence');need(bind(sentinel)==before and not(out/(level+'-existing.json')).exists(),'Native existing output preserved')
  need(not list(out.glob('*.crt-stage-*')),'No native abandoned staging');passed=True
 except Exception as e:failure=str(e);raise
 finally:
  report={'passed':passed,'failure':failure,'scope':'Native four-body model outputs from original before-state fields; authored callbacks only','build':bind(build),'original':bind(raw),'provider':bind(provider),'source':bind(__file__),'commands':commands,'streams':streams,'native_records':3456 if passed else None,'controls':12 if passed else None,'whole_M4_complete':False};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files=[x for x in out.iterdir() if x.is_file()]+[build,raw,provider,Path(__file__)];(out/'pins.json').write_text(json.dumps({'files':{str(x.resolve()):sha(x) for x in files}},indent=2)+'\n')
 print('3456 native CRT outputs and twelve causal controls passed')
if __name__=='__main__':main()
