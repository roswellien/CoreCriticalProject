"""Link current two-level constructor37 candidates; no execution."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,traceback,shlex
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def dependencies(p):
 parts=p.read_text().split(': ',1)[1].replace('\\\n',' ').split();paths=[]
 for v in parts:
  if paths and paths[-1].endswith('\\'):paths[-1]=paths[-1][:-1]+' '+v
  else:paths.append(v)
 return [(Path(v)if Path(v).is_absolute()else R/Path(v)).resolve()for v in paths]
def main():
 prep=(R/sys.argv[1]).resolve();need(sha(prep)==sys.argv[2],'Exact constructor37 recipe');d=json.loads(prep.read_bytes());need(d['passed']and not d['native_executed'],'Unexecuted frozen fixture');out=(R/sys.argv[3]).resolve();need(not out.exists(),'Fresh fixture build');out.mkdir(parents=True);files={};commands=[];workers={};error=None;start=time.perf_counter()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact linked source input '+str(p));files[str(p)]=v;return p
 pin(prep,sys.argv[2])
 for p,h in d['files'].items():pin(p,h)
 llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';clang=pin(llvm/'clang++.exe');pin(__file__)
 includes=[prep.parent,Path(d['component_include']),Path(d['native_include']),Path(d['parent_include']),R/'tools/m4-runtime',R/'tools/m4-startup',R/'runtime',R/'tools/m4-fp-numeric-max',R/'tools/m4-crt',R/'tools/m4-crt-fdiv',R/'tools/m4-crt-commandline-native',R/'tools/m4-guest-cw',R/'local/tools/remill-v6.0.1/remill-6.0.1/include']
 def run(args,name):
  argv=[str(a)for a in args];rsp=out/(name+'.rsp');rsp.write_text('\n'.join(json.dumps(a.replace('\\','/'))for a in argv[1:])+'\n');pin(rsp);result=subprocess.run([argv[0],'@'+str(rsp)],cwd=R,capture_output=True,timeout=240,creationflags=0x08000000);a=out/(name+'.stdout');b=out/(name+'.stderr');a.write_bytes(result.stdout);b.write_bytes(result.stderr);pin(a);pin(b);commands.append(dict(argv=[str(x)for x in args],exit_code=result.returncode,stdout=str(a),stderr=str(b)));need(result.returncode==0,'Actual compile/link '+name)
 try:
  for level in('O0','O2'):
   dst=out/level;dst.mkdir();v=d['levels'][level];flags=['--target=x86_64-pc-windows-msvc','-'+level,'-std=c++20','-fexceptions','-fcxx-exceptions','-fms-runtime-lib=dll','-frounding-math','-DADDRESS_SIZE_BITS=32','-DHAS_FEATURE_AVX=0','-DHAS_FEATURE_AVX512=0','-include',prep.parent/level/'constructor_gate.hpp']
   for inc in [prep.parent/level,*includes]:flags+=['-I',inc]
   objects=[];deps={}
   for name,source in [('fixture',prep.parent/'fixture.cpp'),('mfc_component',prep.parent/'connected_component.cpp')]:
    obj=dst/(name+'.obj');dep=dst/(name+'.d');run([clang,*flags,'-MD','-MF',dep,'-c',source,'-o',obj],level+'-'+name);objects.append(obj);pin(obj);pin(dep);consumed=dependencies(dep)
    for p in consumed:pin(p)
    deps[name]=[str(p)for p in consumed]
   asm=dst/'connected_hardware_boundary.obj';run([clang,'--target=x86_64-pc-windows-msvc','-c',prep.parent/'connected_hardware_boundary.s','-o',asm],level+'-hardware');pin(asm);objects.append(asm)
   worker=dst/'mw34_constructor37.exe';run([clang,'--target=x86_64-pc-windows-msvc','-fms-runtime-lib=dll',*objects,*v['objects'],v['component_library'],v['service_library'],'-o',worker,'-lbcrypt','-luser32','-lgdi32'],level+'-link');pin(worker)
   need(str((prep.parent/'constructor_session.hpp').resolve())in deps['fixture'],'Actual new same-Session public declaration consumed')
   workers[level]=dict(path=str(worker),sha256=sha(worker),fixed_literal_objects=410,current_core_objects=30,current_fixture_objects=3,component_library_sha256=v['component_library_sha256'],service_library_sha256=v['service_library_sha256'],compiler_dependencies=deps,whole_link_review_pending=True)
 except BaseException:error=traceback.format_exc();(out/'failure.txt').write_text(error)
 for p,h in files.items():need(sha(p)==h,'Unchanged build inputs/outputs')
 report=dict(passed=error is None,scope='Linked two-level native constructor37 candidates only; no worker execution, source equivalence, connected134 or144 credit',preparation_path=str(prep),preparation_sha256=sha(prep),workers=workers,commands=commands,files=files,native_executed=False,initializer_credit=0,seconds=time.perf_counter()-start,error=error)
 p=out/'build.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=error is None,sha256=sha(p),error=error)));sys.exit(int(error is not None))
if __name__=='__main__':main()
