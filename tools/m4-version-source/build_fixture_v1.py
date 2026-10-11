"""Link both admitted-image version candidates; never execute a worker."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def dependencies(p):
 parts=p.read_text().split(': ',1)[1].replace('\\\n',' ').split();paths=[]
 for v in parts:
  if paths and paths[-1].endswith('\\'):paths[-1]=paths[-1][:-1]+' '+v
  else:paths.append(v)
 return [(Path(v)if Path(v).is_absolute()else R/v).resolve()for v in paths]
def main(preparation,expected,output):
 prep=(R/preparation).resolve();need(sha(prep)==expected,'Exact current version fixture recipe');d=json.loads(prep.read_bytes());out=(R/output).resolve();need(d['passed']and not out.exists(),'Fresh linked version candidate output');out.mkdir(parents=True);pins={};commands=[];workers={};error=None;start=time.perf_counter()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Entire actual version compile/link physical input '+str(p));pins[str(p)]=v;return p
 pin(prep,expected)
 for p,h in d['files'].items():pin(p,h)
 llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';clang=pin(llvm/'clang++.exe');link=pin(llvm/'lld-link.exe');readobj=pin(llvm/'llvm-readobj.exe');nm=pin(llvm/'llvm-nm.exe');pin(__file__);pin(R/'tools/m4-version-source/build_fixture_v1.ps1')
 includes=[prep.parent,Path(d['component_include']),Path(d['native_include']),Path(d['parent_include']),R/'tools/m4-runtime',R/'tools/m4-startup',R/'runtime',R/'tools/m4-fp-numeric-max',R/'tools/m4-crt',R/'tools/m4-crt-fdiv',R/'tools/m4-crt-commandline-native',R/'tools/m4-guest-cw',R/'local/tools/remill-v6.0.1/remill-6.0.1/include']
 def run(argv,name):
  c=subprocess.run([str(x)for x in argv],cwd=R,capture_output=True,timeout=240,creationflags=0x08000000);a=out/(name+'.stdout');b=out/(name+'.stderr');a.write_bytes(c.stdout);b.write_bytes(c.stderr);pin(a);pin(b);commands.append(dict(argv=[str(x)for x in argv],exit_code=c.returncode,stdout=str(a),stderr=str(b)));need(c.returncode==0,'Actual version compiler/linker '+name)
 try:
  for level in('O0','O2'):
   dst=out/level;dst.mkdir();v=d['levels'][level];obj=dst/'fixture.obj';dep=dst/'fixture.d';args=[clang,'--target=x86_64-pc-windows-msvc','-'+level,'-std=c++20','-fexceptions','-fcxx-exceptions','-fms-runtime-lib=dll','-frounding-math','-DADDRESS_SIZE_BITS=32','-DHAS_FEATURE_AVX=0','-DHAS_FEATURE_AVX512=0','-DVERSION_COMPONENT_LIBRARY_SHA="'+v['component_library_sha256']+'"','-MD','-MF',dep]
   for inc in [Path(d['native_include'])/level,Path(d['parent_include'])/level,*includes]:args+=['-I',inc]
   args+=['-c',prep.parent/'fixture.cpp','-o',obj];run(args,level+'-fixture');pin(obj);pin(dep);consumed=dependencies(dep)
   for p in consumed:pin(p)
   need(Path(d['component_include'])/'component.hpp'in consumed and Path(d['native_include'])/'session.hpp'in consumed,'Actual current component and version service headers consumed')
   fixed=[pin(p,d['files'][str(Path(p).resolve())])for p in v['objects']];need(len(fixed)==427,'Exact unchanged427 inherited COFFs');component=pin(v['component_library'],v['component_library_sha256']);service=pin(v['service_library'],v['service_library_sha256']);worker=dst/'mw34_version.exe';mapfile=dst/'mw34_version.map'
   link_args=['/subsystem:console','/defaultlib:msvcrt','/defaultlib:oldnames','/verbose','/map:'+str(mapfile),obj,*fixed,component,service,'/out:'+str(worker),'bcrypt.lib','user32.lib','gdi32.lib'];rsp=dst/'link.rsp';rsp.write_text('\n'.join('"'+str(a).replace('\\','/').replace('"','\\"')+'"'for a in link_args)+'\n');pin(rsp);run([link,'@'+str(rsp)],level+'-link');commands[-1]['expanded_response_arguments']=[str(a)for a in link_args];pin(worker);pin(mapfile)
   logs=(out/(level+'-link.stdout')).read_text()+'\n'+(out/(level+'-link.stderr')).read_text();libraries=[]
   for row in logs.splitlines():
    match=re.search(r'\bReading (.+?\.lib)(?:\(|$)',row,re.IGNORECASE)
    if match:
     p=Path(match.group(1).strip()).resolve()
     if p.is_file()and p not in libraries:pin(p);libraries.append(p)
   need(libraries,'Actual linker-selected physical library paths recorded')
   run([readobj,'--file-headers','--coff-imports',worker],level+'-PE');header=(out/(level+'-PE.stdout')).read_text();need('IMAGE_FILE_MACHINE_AMD64'in header,'Actual linked x64 version candidate machine')
   run([nm,'--defined-only',component],level+'-component-symbols');symbols=(out/(level+'-component-symbols.stdout')).read_text();need(all('mw34_version_game_f_%x_body'%x in symbols for x in(0x4af0a0,0x4af0f0,0x4af1a0,0x4af240,0x4af250,0x4eac90,0x4eac96,0x4eac9c,0x5ac110,0x5ac140)),'All ten literal definitions supplied by exact current version component')
   workers[level]=dict(path=str(worker),sha256=sha(worker),machine='AMD64',root=0x4af240,root_count=1,literal_bodies=10,fixed_objects=427,current_fixture_objects=1,component_library_sha256=sha(component),service_library_sha256=sha(service),actual_compiler_header_dependencies=[str(p)for p in consumed],actual_linker_libraries=[dict(path=str(p),sha256=sha(p))for p in libraries],expanded_link_arguments_frozen=True,worker_executed=False)
 except BaseException:error=traceback.format_exc();(out/'failure.txt').write_text(error)
 for p,h in pins.items():need(sha(p)==h,'Exact entire version build closure remains unchanged')
 report=dict(passed=error is None,scope='Both current one-root ten-body x64 version initializer candidates linked only; no worker/capture or initializer credit',preparation_sha256=expected,workers=workers,commands=commands,files=pins,linker_LIB_environment=os.environ.get('LIB',''),native_executed=False,original_executed=False,worker_cwd=d['worker_cwd'],first_writer_admission_required=True,initializer_credit=0,seconds=time.perf_counter()-start,error=error)
 q=out/'build.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=error is None,path=str(q),sha256=sha(q),error=error)));sys.exit(int(error is not None))
if __name__=='__main__':main(*sys.argv[1:])
