"""Compile namespaced literal objects and a real provider-backed component.

Only static libraries are produced. No fixture/worker is linked or executed.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def main():
 prep=(R/sys.argv[1]).resolve();need(sha(prep)==sys.argv[2],'Exact preparation');data=json.loads(prep.read_text());need(data['passed']and not data['native_executed'],'Compile-only preparation')
 out=(R/sys.argv[3]).resolve();need(not out.exists(),'Fresh widget build');out.mkdir(parents=True);start=time.perf_counter();files={str(prep):sha(prep)}
 for p,h in data['files'].items():p=Path(p);need(sha(p)==h,'Unchanged preparation input '+str(p));files[str(p)]=h
 directory=prep.parent;LLVM=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';clang=LLVM/'clang.exe';lib=LLVM/'llvm-lib.exe';nm=LLVM/'llvm-nm.exe'
 for p in (clang,lib,nm,Path(__file__).resolve(),R/'tools/m4-widget-native/build.ps1'):files[str(p)]=sha(p)
 commands=[];levels={};failed=False
 def run(args,stem):
  p=subprocess.run([str(a)for a in args],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE);(out/(stem+'.stdout')).write_bytes(p.stdout);(out/(stem+'.stderr')).write_bytes(p.stderr);commands.append({'argv':[str(a)for a in args],'exit_code':p.returncode,'stdout_sha256':sha(out/(stem+'.stdout')),'stderr_sha256':sha(out/(stem+'.stderr'))});need(p.returncode==0,'Actual compiler/library command '+stem)
 try:
  for level in ('O0','O2'):
   dst=out/level;dst.mkdir();objects=[]
   for k,ir in enumerate(data['IRs']):
    p=Path(ir);obj=dst/(p.stem.replace('-host','')+'.obj');run([clang,'--target=x86_64-pc-windows-msvc','-'+level,'-c',p,'-o',obj],level+'-literal-'+str(k));objects.append(obj)
   cpp=dst/'component.obj';dep=dst/'component.d';run([clang,'--target=x86_64-pc-windows-msvc','-'+level,'-std=c++20','-fexceptions','-fcxx-exceptions','-MD','-MF',dep,'-c',directory/'component.cpp','-I',directory,'-I',R/'tools/m4-runtime','-I',R/'runtime','-I',R/'local/tools/remill-v6.0.1/remill-6.0.1/include','-o',cpp],level+'-component');objects.append(cpp)
   asm=dst/'native_api.obj';run([clang,'--target=x86_64-pc-windows-msvc','-c',directory/'native_api.s','-o',asm],level+'-asm');objects.append(asm)
   archive=dst/'mw34_widget_native.lib';run([lib,'/out:'+str(archive),*objects],level+'-archive');run([nm,'--defined-only',archive],level+'-symbols')
   # Actual clang-generated dependency paths, including consumed SDK headers.
   raw=dep.read_text();paths=raw.split(': ',1)[1].replace('\\\n',' ').split();joined=[]
   for token in paths:
    if joined and joined[-1].endswith('\\'):joined[-1]=joined[-1][:-1]+' '+token
    else:joined.append(token)
   deps=[]
   for v in joined:
    p=Path(v.replace('\\ ', ' '));p=p if p.is_absolute()else R/p;need(p.is_file(),'Actual clang dependency '+str(p));files[str(p.resolve())]=sha(p);deps.append(str(p.resolve()))
   for p in objects+[archive,dep]:files[str(p)]=sha(p)
   symbols=(out/(level+'-symbols.stdout')).read_text();need(all('mw34_widget_game_f_%x_body'%v['entry']in symbols for v in data['namespace_relations']),'All 51 actual library literal definitions');need('mw34_widget_native_api'in symbols and'mw34_widget_hardware_call'in symbols,'Actual API/caller hardware assembly definitions')
   levels[level]={'objects':[{'path':str(p),'sha256':sha(p)}for p in objects],'library':str(archive),'library_sha256':sha(archive),'literal_objects':51,'compiled_component_objects':1,'assembly_objects':1,'actual_header_dependencies':deps}
 except Exception as e:failed=True;error=str(e)
 for p,h in list(files.items()):need(sha(Path(p))==h,'Build input/output conservation '+p)
 report={'passed':not failed,'scope':'Compile-only reusable six-root widget component and 102 namespaced literal COFFs; no linked worker or runtime acceptance','preparation_sha256':sha(prep),'levels':levels,'commands':commands,'files':files,'native_executed':False,'initializer_credit':0,'source_native_equivalence':False,'seconds':time.perf_counter()-start}
 if failed:report['error']=error
 (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':not failed,'report':str(out/'build.json'),'sha256':sha(out/'build.json'),'error':report.get('error')}));sys.exit(int(failed))
if __name__=='__main__':main()
