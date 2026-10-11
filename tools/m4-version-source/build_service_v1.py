"""Compile genuine version MFC/buffer service objects only; never link/run a worker."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def deps(p):
 parts=p.read_text().split(': ',1)[1].replace('\\\n',' ').split();result=[]
 for v in parts:
  if result and result[-1].endswith('\\'):result[-1]=result[-1][:-1]+' '+v
  else:result.append(v)
 return [(Path(v)if Path(v).is_absolute()else R/Path(v)).resolve()for v in result]
def main(preparation,expected,output):
 prep=(R/preparation).resolve();need(sha(prep)==expected,'Exact version service preparation');d=json.loads(prep.read_bytes());need(d['passed']and not d['native_executed'],'Compile-only service preparation')
 out=(R/output).resolve();need(not out.exists(),'Fresh version service build');out.mkdir(parents=True);files={};commands=[];levels={};error=None;start=time.perf_counter()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Unchanged source/header '+str(p));files[str(p)]=v;return p
 pin(prep,expected)
 for p,h in d['files'].items():pin(p,h)
 recipe=pin(R/'reports/m4-widget-native/fixture-preparation-r16/report.json','58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401');parent=json.loads(recipe.read_bytes());parent_include=Path(parent['parent_include'])
 llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';clang=pin(llvm/'clang++.exe');lib=pin(llvm/'llvm-lib.exe');nm=pin(llvm/'llvm-nm.exe');pin(__file__);pin(R/'tools/m4-version-source/build_service_v1.ps1')
 includes=[prep.parent,parent_include,R/'tools/m4-runtime',R/'tools/m4-startup',R/'runtime',R/'tools/m4-fp-numeric-max',R/'tools/m4-crt',R/'tools/m4-crt-fdiv',R/'tools/m4-crt-commandline-native',R/'tools/m4-guest-cw',R/'local/tools/remill-v6.0.1/remill-6.0.1/include']
 def run(argv,name):
  p=subprocess.run([str(x)for x in argv],cwd=R,capture_output=True,timeout=240,creationflags=0x08000000);a=out/(name+'.stdout');b=out/(name+'.stderr');a.write_bytes(p.stdout);b.write_bytes(p.stderr);pin(a);pin(b);commands.append(dict(argv=[str(x)for x in argv],exit_code=p.returncode,stdout=str(a),stderr=str(b)));need(p.returncode==0,'Actual compiler/archive '+name)
 try:
  for level in ('O0','O2'):
   dst=out/level;dst.mkdir();v=parent['levels'][level];forced=pin(v['forced_registry_header'],parent['files'][str(Path(v['forced_registry_header']).resolve())]);obj=dst/'version_registry_service.obj';dep=dst/'version_registry_service.d';args=[clang,'--target=x86_64-pc-windows-msvc','-'+level,'-std=c++20','-fexceptions','-fcxx-exceptions','-fms-runtime-lib=dll','-frounding-math','-DADDRESS_SIZE_BITS=32','-DHAS_FEATURE_AVX=0','-DHAS_FEATURE_AVX512=0','-MD','-MF',dep,'-include',forced]
   for inc in [prep.parent/level,parent_include/level,*includes]:args+=['-I',inc]
   args+=['-c',d['native_library'],'-o',obj];run(args,level+'-service');pin(obj);pin(dep)
   consumed=deps(dep)
   for p in consumed:pin(p)
   need(prep.parent/'session.hpp'in consumed and prep.parent/'session_impl.inc'in consumed,'Actual current extension headers consumed')
   archive=dst/'mw34_version_registry_service.lib';run([lib,'/out:'+str(archive),obj],level+'-archive');pin(archive);run([nm,'--defined-only',archive],level+'-symbols');symbols=(out/(level+'-symbols.stdout')).read_text();need(all(x in symbols for x in ['borrow_version_mfc','borrow_version_buffer','commit_version_buffer']),'Three concrete compiled typed service methods')
   levels[level]=dict(object=str(obj),object_sha256=sha(obj),library=str(archive),library_sha256=sha(archive),actual_header_dependencies=[str(p)for p in consumed],forced_registry_header=str(forced),actual_service_methods=3)
 except BaseException:error=traceback.format_exc();(out/'failure.txt').write_text(error)
 for p,h in files.items():need(sha(p)==h,'Compiler source/output closure unchanged')
 report=dict(passed=error is None,scope='Both optimization levels compile concrete genuine borrowed MFC823/825 and same-generation entire native-buffer lease/commit. Static service libraries only; no initializer worker linked or executed',preparation_sha256=expected,levels=levels,commands=commands,files=files,native_executed=False,original_executed=False,worker_linked=False,initializer_credit=0,seconds=time.perf_counter()-start,error=error)
 q=out/'build.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=error is None,path=str(q),sha256=sha(q),error=error)));sys.exit(int(error is not None))
if __name__=='__main__':main(*sys.argv[1:])
