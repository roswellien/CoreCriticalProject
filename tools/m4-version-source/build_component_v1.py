"""Compile ten exact namespaced literals plus finite version route; no worker."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def dependencies(p):
 parts=p.read_text().split(': ',1)[1].replace('\\\n',' ').split();a=[]
 for v in parts:
  if a and a[-1].endswith('\\'):a[-1]=a[-1][:-1]+' '+v
  else:a.append(v)
 return [(Path(v)if Path(v).is_absolute()else R/v).resolve()for v in a]
def main(preparation,expected,output):
 prep=(R/preparation).resolve();need(sha(prep)==expected,'Current exact version component recipe');d=json.loads(prep.read_bytes());out=(R/output).resolve();need(d['passed']and not out.exists(),'Fresh native component build');out.mkdir(parents=True);pins={};levels={};commands=[];error=None;started=time.perf_counter()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact physical compiler input '+str(p));pins[str(p)]=v;return p
 pin(prep,expected)
 for p,h in d['files'].items():pin(p,h)
 llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';cc=pin(llvm/'clang++.exe');clang=pin(llvm/'clang.exe');lib=pin(llvm/'llvm-lib.exe');nm=pin(llvm/'llvm-nm.exe');pin(__file__);pin(R/'tools/m4-version-source/build_component_v1.ps1')
 def run(argv,name):
  c=subprocess.run([str(x)for x in argv],cwd=R,capture_output=True,timeout=240,creationflags=0x08000000);a=out/(name+'.stdout');b=out/(name+'.stderr');a.write_bytes(c.stdout);b.write_bytes(c.stderr);pin(a);pin(b);commands.append(dict(argv=[str(x)for x in argv],exit_code=c.returncode,stdout=str(a),stderr=str(b)));need(c.returncode==0,'Actual compiler/library '+name)
 try:
  for level in ('O0','O2'):
   dst=out/level;dst.mkdir();objects=[]
   for ir in d['IRs']:
    p=Path(ir);obj=dst/(p.stem.replace('-host','')+'.obj');run([clang,'--target=x86_64-pc-windows-msvc','-'+level,'-c',p,'-o',obj],level+'-'+p.stem);pin(obj);objects.append(obj)
   obj=dst/'component.obj';dep=dst/'component.d';argv=[cc,'--target=x86_64-pc-windows-msvc','-'+level,'-std=c++20','-fexceptions','-fcxx-exceptions','-fms-runtime-lib=dll','-DADDRESS_SIZE_BITS=32','-DHAS_FEATURE_AVX=0','-DHAS_FEATURE_AVX512=0','-MD','-MF',dep]
   for p in [prep.parent,Path(d['service_include']),R/'tools/m4-runtime',R/'tools/m4-startup',R/'runtime',R/'local/tools/remill-v6.0.1/remill-6.0.1/include']:argv+=['-I',p]
   argv+=['-c',prep.parent/'component.cpp','-o',obj];run(argv,level+'-component');pin(obj);pin(dep);objects.append(obj);consumed=dependencies(dep)
   for p in consumed:pin(p)
   need(Path(d['service_include'])/'session.hpp'in consumed,'Actual current version service header consumed')
   asm=dst/'caller_hardware.obj';run([clang,'--target=x86_64-pc-windows-msvc','-c',prep.parent/'caller_hardware.s','-o',asm],level+'-caller-hardware');pin(asm);objects.append(asm)
   archive=dst/'mw34_version_native.lib';run([lib,'/out:'+str(archive),*objects],level+'-library');pin(archive);run([nm,'--defined-only',archive],level+'-symbols');symbols=(out/(level+'-symbols.stdout')).read_text();need(all('mw34_version_game_f_%x_body'%x['entry']in symbols for x in d['namespace_relations'])and'mw34_version_hardware_call'in symbols,'All ten actual literal definitions and caller assembly')
   levels[level]=dict(objects=[dict(path=str(p),sha256=sha(p))for p in objects],library=str(archive),library_sha256=sha(archive),literal_objects=10,component_objects=1,assembly_objects=1,actual_header_dependencies=[str(p)for p in consumed])
 except BaseException:error=traceback.format_exc();(out/'failure.txt').write_text(error)
 for p,h in pins.items():need(sha(p)==h,'Actual physical input/output closure conservation')
 report=dict(passed=error is None,preparation_sha256=expected,scope='Both actual optimization-level ten-body version libraries, real typed service ABI, preserved caller hardware; no worker linked or executed',levels=levels,commands=commands,files=pins,worker_linked=False,native_executed=False,original_executed=False,initializer_credit=0,seconds=time.perf_counter()-started,error=error)
 q=out/'build.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=error is None,path=str(q),sha256=sha(q),error=error)));sys.exit(int(error is not None))
if __name__=='__main__':main(*sys.argv[1:])
