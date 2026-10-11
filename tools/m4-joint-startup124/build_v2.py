"""Compile one immutable changed124 corpus, reusing exact accepted literal COFFs."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint-startup124'
VS=Path('C:/Program Files/Microsoft Visual Studio/18/Community');CMAKE=VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe';LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(prep,expected,out):
 started=time.perf_counter()
 prep=Path(prep).resolve();out=Path(out).resolve();assert sha(prep/'report.json')==expected and out.parent==BASE and not out.exists();out.mkdir(parents=True);p=json.loads((prep/'report.json').read_text());assert p['passed'];pins=json.loads((prep/'pins.json').read_text())['files'];sources=dict(pins)
 inherited_archives={pp:h for pp,h in pins.items() if Path(pp).suffix=='.mwb'}
 for pp,h in pins.items():
  if pp not in inherited_archives:assert sha(pp)==h,(pp,h)
 writer=ROOT/'reports/m4-capture-direct/build-r4/build.json';assert sha(writer)=='909955901c310e5fcf5eb0713e48a20bf896d13ea335e9d8093dec25ba232e96';w=json.loads(writer.read_text());assert w['passed']
 for pp,h in w['sources'].items()|w['objects'].items():assert sha(pp)==h,(pp,h);sources[pp]=h
 commands=[];failure=None;workers={};tools={};artifacts={}
 def run(args,log):
  args=list(map(str,args));command_started=time.perf_counter();r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=240);elapsed=time.perf_counter()-command_started;(out/log).write_bytes(r.stdout+r.stderr);tools[args[0]]=sha(args[0]);commands.append({'arguments':args,'exit_code':r.returncode,'log':log,'elapsed_seconds':elapsed});print(json.dumps({'log':log,'exit_code':r.returncode,'elapsed_seconds':elapsed}),flush=True);assert r.returncode==0,r.stderr.decode(errors='replace')[-6000:]
 try:
  os.environ['TEMP']=os.environ['TMP']=str(out)
  for level in('O0','O2'):
   tree=out/f'build-{level}';flags=('/Od'if level=='O0'else'/O2')+' /DNDEBUG /showIncludes -Wno-invalid- offsetof'.replace('- offsetof','-offsetof')
   run([CMAKE,'-G','Ninja','-S',prep,'-B',tree,f'-DMW34_ROOT={ROOT}',f'-DMW34_PREP={prep}',f'-DMW34_LEVEL={level}',f'-DMW34_REGISTRY={p['native_library']}',f'-DMW34_REGISTRY_INCLUDE={p['native_include']}',f'-DMW34_OBJECTS={";".join(p["objects"][level])}',f'-DMW34_WRITER={ROOT}/reports/m4-capture-direct/build-r4/capture_direct-{level}.obj',f'-DCMAKE_CXX_COMPILER={LLVM}/clang-cl.exe','-DCMAKE_BUILD_TYPE=Release',f'-DCMAKE_CXX_FLAGS_RELEASE={flags}'],f'{level}-configure.log')
   run([CMAKE,'--build',tree,'--parallel','6'],f'{level}-build.log');worker=tree/'mw34_joint_startup124.exe';workers[level]={'path':str(worker),'sha256':sha(worker),'objects':p['objects'][level]}
  for pp,h in sources.items():
   if pp not in inherited_archives:assert sha(pp)==h,('Source changed',pp)
 except BaseException:failure=traceback.format_exc();(out/'failure.txt').write_text(failure)
 artifacts={str(pp):sha(pp)for pp in out.rglob('*')if pp.is_file()}
 report={'passed':failure is None,'failure':failure,'scope':'Changed connected124 native compile only','preparation':str(prep/'report.json'),'preparation_sha256':expected,'sources':sources,'tools':tools,'commands':commands,'workers':workers,'artifacts':artifacts,'elapsed_seconds':time.perf_counter()-started,'inherited_capture_payload_hashes_reused':inherited_archives,'full_dependency_acceptance_rehash_required':True,'guest_executed':False,'whole_M4_complete':False}
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps({'files':sources|artifacts|tools|{str(out/'build.json'):sha(out/'build.json')}},indent=2)+'\n')
 if failure:raise RuntimeError(failure)
 print(json.dumps({'passed':True,'build':str(out/'build.json'),'sha256':sha(out/'build.json')}))
if __name__=='__main__':main(*sys.argv[1:])

