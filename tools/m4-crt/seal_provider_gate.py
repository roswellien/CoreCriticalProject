"""Author-side physical evidence association; independent gate review still required."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def need(ok,why):
 if not ok:raise ValueError(why)
def bind(p):p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);out=Path(p.parse_args().out).resolve();need(out.is_relative_to(ROOT/'reports/m4-crt') and not out.exists(),'Fresh private CRT author closure');files={};replacements=[];checks=[]
 def add(path,h=None):
  q=Path(path).resolve();s=sha(q);need(h is None or s==h,'Exact immutable bytes '+str(q));old=files.get(str(q));need(old is None or old==s,'No inconsistent physical binding');files[str(q)]=s
 def map_build(path):
  m=load(path);need(m['passed'],'Passed worker build');copies={x['original_path']:x for x in m['literal_source_copies']}
  for group in ('source_files','tool_files','artifacts'):
   for name,h in m[group].items():add(name,h)
  for name,h in m['source_files'].items():need(name in copies and copies[name]['sha256']==h,'Exact literal source association');add(copies[name]['preserved_path'],h)
  add(path);checks.append({'build':bind(path),'source_files':len(m['source_files']),'tool_files':len(m['tool_files']),'artifacts':len(m['artifacts'])});return m
 ob=ROOT/'reports/m4-crt/provider-probe-build-r1/build.json';nb=ROOT/'reports/m4-crt/native-replay-build-r2/build.json';omap=map_build(ob);nmap=map_build(nb)
 peer=ROOT/'reports/m4-runtime/independent-service-r9';need(sha(peer/'report.json')=='27a48065b1d9e046a138379d6ded99bc691e4813a0337a9b7709afe920035886','Exact independent runtime r9 acceptance')
 for name,h in load(peer/'pins.json')['files'].items():add(name,h)
 add(peer/'pins.json');add(peer/'report.json');need(nmap['runtime_build_sha256']=='12bd0f42d7fba2cc8b9f7cc4d6b9db795c98e196ae305ac23dbd7fe38b21abf5','Fresh r9 source consumption')
 dirs=('provider-probe-extraction-r1','provider-probe-build-r1','provider-original-run-r1','native-replay-build-r1','native-replay-build-r2','native-replay-run-r1','native-driver-newline-attempt','native-replay-run-r2','provider-comparison-r1')
 for name in dirs:
  for q in (ROOT/'reports/m4-crt'/name).rglob('*'):
   if q.is_file():add(q)
 # Changed build-recipe source of the preserved failed compile and changed
 # runner source of the failed diagnostic attempt receive literal replacements.
 failed=load(ROOT/'reports/m4-crt/native-replay-build-r1/build.json');need(not failed['passed'] and 'exit=1' in failed['failure'],'Preserved build path failure')
 copies={x['original_path']:x for x in failed['literal_source_copies']}
 for name,h in failed['source_files'].items():
  q=Path(name)
  if sha(q)!=h:add(copies[name]['preserved_path'],h);replacements.append({'historical_path':name,'historical_sha256':h,'physical_path':copies[name]['preserved_path'],'reason':'Failed native compile recipe before absolute include repair'})
  else:add(q,h)
 badrun=load(ROOT/'reports/m4-crt/native-replay-run-r1/report.json');need(not badrun['passed'] and badrun['failure']=='Exact intended causal diagnostic O0-bad-cli','Preserved runner newline failure');oldscript=ROOT/'reports/m4-crt/native-driver-newline-attempt/run_native.py';add(oldscript,badrun['source']['sha256']);replacements.append({'historical_path':badrun['source']['path'],'historical_sha256':badrun['source']['sha256'],'physical_path':str(oldscript),'reason':'Failed control-runner CRLF-only assertion'})
 original=load(ROOT/'reports/m4-crt/provider-original-run-r1/report.json');native=load(ROOT/'reports/m4-crt/native-replay-run-r2/report.json');comparison=load(ROOT/'reports/m4-crt/provider-comparison-r1/report.json');need(original['passed'] and native['passed'] and comparison['passed'],'All actual gates passed');need(original['controls']==6 and native['controls']==12 and len(comparison['observer_controls'])==118,'Exact independent control layers');need(comparison['original_records']==1728 and comparison['native_records']==3456 and comparison['exact_guest_repeats']==864,'Exact record corpus')
 for report in (original,native):
  for c in report['commands']:add(c['stdout']['path'],c['stdout']['sha256']);add(c['stderr']['path'],c['stderr']['sha256'])
 add(original['original']['path'],original['original']['sha256']);need(original['worker']['sha256']==omap['artifacts'][original['worker']['path']],'Actual original worker association')
 for c in native['commands']:need(c['worker']['sha256']==nmap['artifacts'][c['worker']['path']],'Actual freshly compiled native worker association')
 # Compilers generated distinct service objects with O0/O2 switches. Literal
 # recipe and Ninja build files bind their Session-to-library-to-worker linkage.
 need('crt_services.cpp.obj' in (ROOT/'build/m4-crt-native-replay-build-r2/build.ninja').read_text(),'Real native service object linkage')
 for q in (ROOT/'tools/m4-crt').rglob('*'):
  if q.is_file() and '__pycache__' not in q.parts:add(q)
 for q in (ROOT/'tests/m4-crt').rglob('*'):
  if q.is_file():add(q)
 add(ROOT/'docs/m4-crt-contract.md');add(ROOT/'docs/m4-crt-provider-experiment.md');add(__file__)
 out.mkdir(parents=True);report={'passed':True,'scope':'Author CRT four-body provider-contract closure; independent review required before actual game service admission','comparison':bind(ROOT/'reports/m4-crt/provider-comparison-r1/report.json'),'runtime_peer_acceptance':bind(peer/'report.json'),'build_associations':checks,'original_records':1728,'native_records':3456,'guest_repeats':864,'actual_causal_controls':18,'observer_controls':118,'historical_source_replacements':replacements,'physical_bindings_before_report':len(files),'guest_game_code_executed':False,'DLL_loaded':False,'original_callback_fixture':'Authored machine-code callbacks; no actual game slot substitution','original_event_trace':False,'whole_M4_complete':False,'limits':comparison['limits']};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');add(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n');print('Author CRT provider gate sealed:',len(files),'physical bindings')
if __name__=='__main__':main()
