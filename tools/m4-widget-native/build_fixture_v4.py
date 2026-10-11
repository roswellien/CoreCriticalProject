"""Link both first-writer candidates without launching either."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def dependencies(p):
 raw=p.read_text().split(': ',1)[1].replace('\\\n',' ');parts=raw.split();paths=[]
 for v in parts:
  if paths and paths[-1].endswith('\\'):paths[-1]=paths[-1][:-1]+' '+v
  else:paths.append(v)
 return [(Path(v)if Path(v).is_absolute()else R/Path(v)).resolve()for v in paths]
def main():
 prep=(R/sys.argv[1]).resolve();need(sha(prep)==sys.argv[2],'Exact widget fixture recipe');d=json.loads(prep.read_text());out=(R/sys.argv[3]).resolve();need(not out.exists(),'Fresh linked widget build');out.mkdir(parents=True);files={str(prep):sha(prep)};commands=[];workers={};error=None;start=time.perf_counter()
 for p,h in d['files'].items():p=Path(p);need(sha(p)==h,'Exact frozen fixture input '+str(p));files[str(p)]=h
 LLVM=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';clang=LLVM/'clang++.exe';link=LLVM/'lld-link.exe'
 for p in [clang,link,Path(__file__).resolve(),R/'tools/m4-widget-native/build_fixture_v4.ps1']:files[str(p)]=sha(p)
 includes=[prep.parent,Path(d['component_include']),Path(d['native_include']),Path(d['parent_include']),R/'tools/m4-runtime',R/'tools/m4-startup',R/'runtime',R/'tools/m4-fp-numeric-max',R/'tools/m4-crt',R/'tools/m4-crt-fdiv',R/'tools/m4-crt-commandline-native',R/'tools/m4-guest-cw',R/'local/tools/remill-v6.0.1/remill-6.0.1/include']
 def run(args,name):
  c=subprocess.run([str(a)for a in args],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE);(out/(name+'.stdout')).write_bytes(c.stdout);(out/(name+'.stderr')).write_bytes(c.stderr);commands.append({'argv':[str(a)for a in args],'exit_code':c.returncode,'stdout':str(out/(name+'.stdout')),'stderr':str(out/(name+'.stderr'))});need(c.returncode==0,'Actual widget compiler/linker '+name)
 try:
  for level in ('O0','O2'):
   dst=out/level;dst.mkdir();v=d['levels'][level];flags=['--target=x86_64-pc-windows-msvc','-'+level,'-std=c++20','-fexceptions','-fcxx-exceptions','-fms-runtime-lib=dll','-frounding-math','-DADDRESS_SIZE_BITS=32','-DHAS_FEATURE_AVX=0','-DHAS_FEATURE_AVX512=0']
   for inc in includes:flags+=['-I',inc]
   objects=[]
   for name,source in [('fixture',prep.parent/'fixture.cpp'),('registry',Path(d['native_library']))]:
    obj=dst/(name+'.obj');dep=dst/(name+'.d');args=[clang,*flags,'-MD','-MF',dep,'-c',source,'-o',obj]
    if name=='fixture':args+=['-DWIDGET_COMPONENT_LIBRARY_SHA="'+v['component_library_sha256']+'"']
    else:args+=['-include',v['forced_registry_header']]
    run(args,level+'-'+name);objects.append(obj)
    for p in dependencies(dep):need(p.is_file(),'Complete actual compiler header '+str(p));files[str(p)]=sha(p)
    files[str(dep)]=sha(dep);files[str(obj)]=sha(obj)
   worker=dst/'mw34_widget6.exe';link_args=['/subsystem:console','/defaultlib:msvcrt','/defaultlib:oldnames',*objects,*v['objects'],v['component_library'],'/out:'+str(worker),'bcrypt.lib','user32.lib','gdi32.lib'];rsp=dst/'link.rsp';rsp.write_text('\n'.join('"'+str(a).replace('\\','/').replace('"','\\"')+'"'for a in link_args)+'\n');files[str(rsp)]=sha(rsp);run([link,'@'+str(rsp)],level+'-link');commands[-1]['expanded_response_arguments']=[str(a)for a in link_args];files[str(worker)]=sha(worker);workers[level]={'path':str(worker),'sha256':sha(worker),'fixed_objects':427,'current_fixture_objects':2,'component_library_sha256':v['component_library_sha256'],'all_arguments_frozen':True}
 except Exception as e:error=str(e)
 for p,h in files.items():need(sha(Path(p))==h,'Linked build unchanged-input closure '+p)
 report={'passed':error is None,'scope':'Current six registered widget first-writer candidates linked only; no native execution or initializer acceptance','preparation_sha256':sha(prep),'workers':workers,'commands':commands,'files':files,'native_executed':False,'initializer_credit':0,'seconds':time.perf_counter()-start,'error':error}
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':error is None,'report':str(out/'build.json'),'sha256':sha(out/'build.json'),'error':error}));sys.exit(int(error is not None))
if __name__=='__main__':main()
