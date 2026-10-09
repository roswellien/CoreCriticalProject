"""Author seal for original writer observation and reference-only data ownership."""
import hashlib,importlib.util,json,pathlib,re,struct,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3];BASE=ROOT/'reports/m4-crt-data'
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def need(v,w):
 if not v:raise ValueError(w)
def seal(out):
 need(not out.exists() and out.is_relative_to(BASE),'Fresh private author seal required')
 files={};resolutions=[];checks=[];documents=[];copies={}
 def bind(p,h=None):
  p=pathlib.Path(p).resolve();got=sha(p);need(h is None or got==h,'Physical identity '+str(p));need(str(p) not in files or files[str(p)]==got,'Conflicting identity');files[str(p)]=got;return got
 for p in sorted(BASE.rglob('*.json')):
  try:j=read(p)
  except json.JSONDecodeError:continue
  documents.append((p,j));bind(p)
  if isinstance(j,dict):
   for row in j.get('literal_source_copies',[]):
    bind(row['preserved_path'],row['sha256']);copies[(str(pathlib.Path(row['original_path']).resolve()).casefold(),row['sha256'])]=row['preserved_path']
 for p,j in documents:
  if not isinstance(j,dict):continue
  for key in ('source_files','tool_files','artifacts','immutable_files','files'):
   for original,h in j.get(key,{}).items():
    if not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h):continue
    actual=pathlib.Path(original)
    if actual.is_file() and sha(actual)==h:bind(actual,h);continue
    replacement=copies.get((str(actual.resolve()).casefold(),h))
    need(replacement is not None,'No explicit preserved literal resolution for '+str(p)+' '+original)
    bind(replacement,h);resolutions.append({'historical_map':str(p),'historical_map_sha256':sha(p),'original_path':original,'recorded_sha256':h,'physical_path':str(pathlib.Path(replacement).resolve()),'reason':'Exact preserved literal historical source; live source subsequently repaired'})
 checks.append({'name':'All original failed/diagnostic/current maps physically rehashed with explicit literal historical resolutions','maps':len(documents),'historical_resolutions':len(resolutions),'passed':True})
 build=BASE/'ownership-build-r3/build.json';bm=read(build);need(bm['passed'],'Actual both-level ownership build')
 need(len(bm['source_files'])==16 and len(bm['tool_files'])==8,'Final exact source/tool inventory')
 for row in bm['literal_source_copies']:bind(row['original_path'],row['sha256']);bind(row['preserved_path'],row['sha256'])
 for key in ('tool_files','artifacts'):
  for p,h in bm[key].items():bind(p,h)
 need(all(c['exit_code']==0 for c in bm['commands']) and len(bm['commands'])==4,'Actual build and both positive controls')
 for level in ('O0','O2'):need((BASE/'ownership-build-r3'/('test-'+level+'.log')).read_text(encoding='utf-8-sig').strip()=='251 authored reference data ownership/admission checks passed; production service false','Exact actual authored controls '+level)
 checks.append({'name':'Fresh complete helper/runtime libraries and controls at both optimizations','checks_per_level':251,'semantic_scenarios_per_level':24,'actual_game_association_is_declared_reference_fixture':True,'passed':True})
 analysis=BASE/'commandline-analysis-r3/report.json';a=read(analysis);run=BASE/'commandline-run-r1/report.json';r=read(run);need(a['passed'] and r['passed'] and a['records']==r['records']==192 and len(a['observer_controls'])==24 and len(r['actual_controls'])==8,'Actual original writer observations and causal controls')
 need(a['run_sha256']==bind(run) and a['raw_sha256']==bind(a['raw_path'])==r['raw']['sha256'],'Exact actual original stream association')
 module=pathlib.Path(a['actual_OS_API_module_path_resolution']['physical_path']);bind(module,a['actual_OS_API_module_sha256'])
 spec=importlib.util.spec_from_file_location('author_commandline_analysis',ROOT/'tools/m4-crt-data/analyze_commandline.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 raw=pathlib.Path(a['raw_path']).read_bytes();h=m.header(raw)
 for i in range(192):m.row(raw[h['record_start']+i*h['stride']:h['record_start']+(i+1)*h['stride']],i,h)
 provider=pathlib.Path(bm['inputs']['provider']['path']);pb=provider.read_bytes();bind(provider,bm['inputs']['provider']['sha256']);bind(bm['inputs']['game']['path'],bm['inputs']['game']['sha256'])
 research=read(BASE/'commandline-research-r1/report.json');fragment=(BASE/'commandline-research-r1/original-fragment.bin').read_bytes();pack=(BASE/'commandline-research-r1/pack.bin').read_bytes();need(pb[research['original_file_offset']:research['original_file_offset']+11]==fragment==pack[16+0x88c:16+0x88c+11] and hashlib.sha256(fragment).hexdigest()==research['original_sha256'],'Exact literal source/provider/pack writer equality')
 checks.append({'name':'192 complete actual original records replayed through author observer; exact source11 bytes equal admitted provider and RX pack; actual module physical identity','records':192,'worker_controls':8,'observer_controls':24,'full_DllMain_executed':False,'native_writer_executed':False,'passed':True})
 # These controls execute authored ownership/admission code only; no vendor instructions.
 out.mkdir();control=out/'controls';control.mkdir();changed={}
 for label,source in [('provider',provider),('game',pathlib.Path(bm['inputs']['game']['path'])),('raw',pathlib.Path(a['raw_path']))]:
  b=bytearray(source.read_bytes());b[100]^=1;p=control/('changed-'+label+'.bin');p.write_bytes(b);changed[label]=p
 missing=control/'absent.bin';actual=[]
 for level in ('O0','O2'):
  exe=ROOT/('build/m4-crt-data-ownership-build-r3/Release/data_reference_tests_'+level+'.exe');args=[str(provider),bm['inputs']['game']['path'],a['raw_path']]
  cases=[('extra',args+['extra'],'Data tests require private exact provider/game/original observation'),('missing',args[:-1]+[str(missing)],'Private test input required'),('changed-raw',args[:-1]+[str(changed['raw'])],'Exact frozen original observation required'),('changed-provider',[str(changed['provider'])]+args[1:],'Exact reference data admission failed'),('changed-game',[args[0],str(changed['game']),args[2]],'Wrong M4 image identity')]
  for label,argv,diagnostic in cases:
   cp=subprocess.run([str(exe)]+argv,capture_output=True);so=control/(level+'-'+label+'.stdout');se=control/(level+'-'+label+'.stderr');so.write_bytes(cp.stdout);se.write_bytes(cp.stderr);need(cp.returncode==1 and cp.stdout==b'' and cp.stderr.decode().strip()==diagnostic,'Intended actual authored admission failure '+level+' '+label);actual.append({'level':level,'name':label,'program':str(exe),'arguments':argv,'exit_code':cp.returncode,'intended_diagnostic':diagnostic,'stdout':str(so),'stderr':str(se),'passed':True})
 checks.append({'name':'Ten actual entry/input admission controls with exact intended diagnostics','controls':10,'original_or_provider_code_executed':False,'passed':True})
 # The earlier failed MSVC builds remain preserved with literal dependencies.
 need(read(BASE/'ownership-build-r1/build.json')['passed'] is False and read(BASE/'ownership-build-r2/build.json')['passed'] is False,'Both compile-only failed baselines retained')
 need('warning C4324' in (BASE/'ownership-build-r1/build.log').read_text(encoding='utf-8-sig') and 'make_authored_fixture' in (BASE/'ownership-build-r2/build.log').read_text(encoding='utf-8-sig'),'Actual compiler failures retained')
 for p in (ROOT/'tools/m4-crt-data').rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:bind(p)
 for directory in [BASE]+list((ROOT/'build').glob('m4-crt-data-*')):
  for p in directory.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:bind(p)
 for p in [ROOT/'tests/m4-crt-data/ownership_tests.cpp',ROOT/'docs/m4-crt-data-admission.md',ROOT/'tools/m4-crt/probe_common.hpp',ROOT/'tools/m4-crt/probe_io.hpp',ROOT/'tools/m4-crt/recover_provider.py',ROOT/'reports/m4-runtime/context-r9/build.json',ROOT/'reports/m4-runtime/independent-service-r9/report.json',ROOT/'reports/m4-runtime/independent-service-r9/pins.json',pathlib.Path(sys.executable)]:bind(p)
 rb=read(ROOT/'reports/m4-runtime/context-r9/build.json')
 for p,h in rb['source_files'].items():bind(p,h)
 # Actual Lib.exe path was recorded in build logs before this supplemental current hash.
 lib=pathlib.Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/lib.exe');bind(lib)
 report={'passed':True,'scope':'Original-only process-attach command-line writer observation plus typed reference/projection ownership/admission; no native command-line service or writer implementation','checks':checks,'original_analysis_path':str(analysis),'original_analysis_sha256':sha(analysis),'ownership_build_path':str(build),'ownership_build_sha256':sha(build),'historical_source_resolutions':resolutions,'actual_authored_worker_controls':actual,'tool_identity_note':'Build records bind post-build current provider hashes and actual logged invocation paths; no claim of historical per-instruction tool hash attestation','supplemental_lib_current_sha256':sha(lib),'reference_projection_only':True,'production_initialized_service':False,'shared_Runtime_r9_changed':False,'whole_M4_complete':False,'limitations':['Only eleven original provider writer bytes and actual Windows GetCommandLineA execute; preceding/following process attach is open','Measured command-line buffer is the probe process input; reference projection is explicitly declared observation input, not native OS/provider execution','Trusted stable Runtime outlives registry; no concurrent callers or host mapping replacement; no arbitrary swallowed raw MemoryFault prevention','_adjust_fdiv, complete data/import routing, actual native writer with own command-line input, full CRT/SEH/startup and menu are unresolved']}
 rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');bind(rp)
 (out/'pins.json').write_text(json.dumps({'files':dict(sorted(files.items()))},indent=2)+'\n');print('Author seal passed:',len(files),'durable files;',len(resolutions),'explicit historical resolutions;',sha(rp),sha(out/'pins.json'))
if __name__=='__main__':seal(pathlib.Path(sys.argv[1]).resolve())
