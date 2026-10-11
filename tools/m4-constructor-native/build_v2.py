"""Compile only the complete constructor Component and namespaced literal IRs."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(prep,expected,name):
 need(sha(prep)==expected,'Exact current unexecuted preparation');v=json.loads(prep.read_bytes());need(v['passed']and not v['native_executed'],'Prepared compile-only source');out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh constructor build');out.mkdir(parents=True);pins={str(prep):expected};commands=[];levels={};passed=False;started=time.perf_counter()
 def pin(p,h=None):
  p=Path(p).resolve();q=sha(p);need(h is None or h==q,'Exact physical compiler input/output '+str(p));pins[str(p)]=q;return p
 for p,h in v['files'].items():pin(p,h)
 llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';clang=pin(llvm/'clang.exe');lib=pin(llvm/'llvm-lib.exe');nm=pin(llvm/'llvm-nm.exe');pin(__file__);pin(R/'tools/m4-constructor-native/build.ps1')
 def run(args,name):
  result=subprocess.run([str(a)for a in args],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE);a=out/(name+'.stdout');b=out/(name+'.stderr');a.write_bytes(result.stdout);b.write_bytes(result.stderr);commands.append(dict(argv=[str(x)for x in args],exit_code=result.returncode,stdout_sha256=sha(a),stderr_sha256=sha(b)));need(result.returncode==0,'Actual constructor compilation '+name)
 try:
  for level in('O0','O2'):
   folder=out/level;folder.mkdir();objects=[]
   for index,ir in enumerate(v['IRs']):
    p=Path(ir);obj=folder/(p.stem.replace('-host','')+'.obj');run([clang,'--target=x86_64-pc-windows-msvc','-'+level,'-c',p,'-o',obj],level+'-literal-'+str(index));objects.append(obj)
   cpp=folder/'component.obj';dep=folder/'component.d';run([clang,'--target=x86_64-pc-windows-msvc','-'+level,'-std=c++20','-fexceptions','-fcxx-exceptions','-fms-runtime-lib=dll','-MD','-MF',dep,'-c',prep.parent/'component.cpp','-I',prep.parent,'-I',R/'tools/m4-runtime','-I',R/'tools/m4-startup','-I',R/'runtime','-I',R/'local/tools/remill-v6.0.1/remill-6.0.1/include','-o',cpp],level+'-component');objects.append(cpp)
   asm=folder/'native_api.obj';run([clang,'--target=x86_64-pc-windows-msvc','-c',prep.parent/'native_api.s','-o',asm],level+'-asm');objects.append(asm);archive=folder/'mw34_constructor_native.lib';run([lib,'/out:'+str(archive),*objects],level+'-archive');run([nm,'--defined-only',archive],level+'-symbols')
   raw=dep.read_text();parts=raw.split(': ',1)[1].replace('\\\n',' ').split();joined=[]
   for token in parts:
    if joined and joined[-1].endswith('\\'):joined[-1]=joined[-1][:-1]+' '+token
    else:joined.append(token)
   deps=[]
   for item in joined:p=Path(item.replace('\\ ',' '));p=p if p.is_absolute()else R/p;pin(p);deps.append(str(p.resolve()))
   for p in objects+[archive,dep]:pin(p)
   symbols=(out/(level+'-symbols.stdout')).read_text();need(all('mw34_constructor_game_f_%x_body'%x['entry']in symbols for x in v['namespace_relations'])and'mw34_constructor_hardware_call'in symbols,'All33 actual literal bodies and whole caller hardware bridge in compiled library')
   levels[level]=dict(objects=[dict(path=str(p),sha256=sha(p))for p in objects],library=str(archive),library_sha256=sha(archive),literal_objects=33,component_objects=1,hardware_objects=1,actual_compiler_header_dependencies=deps)
  passed=True
 except BaseException as e:error=str(e)
 finally:
  for p,h in pins.items():need(sha(p)==h,'Input/output physical conservation')
  r=dict(passed=passed,scope='Compile-only three constructor Component/66literal COFFs and caller boundary; no Session service link/runtime/source/native credit',preparation_path=str(prep),preparation_sha256=expected,levels=levels,commands=commands,native_executed=False,initializer_credit=0,whole_source_equivalence_pending=True,seconds=time.perf_counter()-started,files=pins)
  if not passed:r['error']=error
  p=out/'build.json';p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),error=r.get('error'))))
 return 0 if passed else 1
if __name__=='__main__':sys.exit(main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3]))
