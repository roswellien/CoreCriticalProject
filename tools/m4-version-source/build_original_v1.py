"""Compile the frozen original32 version observer; never launch a worker."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(preparation,expected,output):
 prep=(R/preparation).resolve();need(sha(prep)==expected,'Exact frozen original version preparation');d=json.loads(prep.read_bytes());out=(R/output).resolve();need(d['passed']and not out.exists(),'Fresh original32 compiler output');out.mkdir(parents=True);pins={};commands=[];error=None;started=time.perf_counter();worker=out/'original-worker.exe';objects=[];headers=[];libraries=[]
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader in original build');v=sha(p);need(h is None or h==v,'Exact physical original32 compiler input '+str(p));pins[str(p)]=v;return p
 pin(prep,expected)
 for p,h in d['files'].items():pin(p,h)
 pin(__file__);pin(R/'tools/m4-version-source/build_original_v1.ps1')
 cl=pin(shutil.which('cl.exe'));ml=pin(shutil.which('ml.exe'));link=pin(shutil.which('link.exe'));readobj=pin(R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-readobj.exe')
 for f in('c1xx.dll','c2.dll','mspdb140.dll'):
  p=cl.parent/f
  if p.is_file():pin(p)
 def run(argv,name):
  c=subprocess.run([str(x)for x in argv],cwd=out,capture_output=True,timeout=240,creationflags=0x08000000);a=out/(name+'.stdout');b=out/(name+'.stderr');a.write_bytes(c.stdout);b.write_bytes(c.stderr);pin(a);pin(b);commands.append(dict(argv=[str(x)for x in argv],exit_code=c.returncode,stdout=str(a),stderr=str(b)));need(c.returncode==0,'Actual original32 compile/link '+name);return c.stdout.decode(errors='replace')+'\n'+c.stderr.decode(errors='replace')
 try:
  for src in(prep.parent/'reference.cpp',R/'tools/m4-capture-direct/capture_direct_v3.cpp'):
   pin(src);obj=out/(src.stem+'.obj');log=run([cl,'/nologo','/std:c++20','/O2','/EHsc','/W4','/WX','/MD','/showIncludes','/c','/I'+str(prep.parent),'/I'+str(R/'tools/m4-capture-direct'),'/Fo'+str(obj),src],src.stem);pin(obj);objects.append(obj)
   for row in log.splitlines():
    if 'Note: including file:'in row:
     p=Path(row.split('Note: including file:',1)[1].strip()).resolve();pin(p)
     if p not in headers:headers.append(p)
  need(prep.parent/'version_observer.hpp'in headers and prep.parent/'spec.hpp'in headers,'Actual compiled frozen version observer and physical source spec headers')
  for src in sorted(prep.parent.glob('*.asm')):
   pin(src);obj=out/(src.stem+'.obj');run([ml,'/nologo','/c','/coff','/Fo'+str(obj),src],src.stem);pin(obj);objects.append(obj)
  need(len(objects)==9,'Two C++ plus seven exact original32 assembly objects')
  mapfile=out/'original-worker.map';args=['/nologo','/subsystem:console','/machine:x86','/base:0x18000000','/dynamicbase:no','/fixed:no','/largeaddressaware','/verbose:lib','/defaultlib:msvcrt','/defaultlib:oldnames','/map:'+str(mapfile),'/out:'+str(worker),*objects,'bcrypt.lib','kernel32.lib'];rsp=out/'link.rsp';rsp.write_text('\n'.join('"'+str(x).replace('\\','/')+'"'for x in args)+'\n');pin(rsp);log=run([link,'@'+str(rsp)],'link');commands[-1]['expanded_response_arguments']=[str(x)for x in args];pin(worker);pin(mapfile)
  for row in log.splitlines():
   m=re.search(r'Searching\s+(.+?\.lib):?\s*$',row,re.I)
   if m:
    p=Path(m.group(1).strip()).resolve()
    if p.is_file()and p not in libraries:pin(p);libraries.append(p)
  need(len(libraries)>=5,'Actual linker-selected physical library input paths')
  pe=run([readobj,'--file-headers','--coff-imports',worker],'PE');need('IMAGE_FILE_MACHINE_I386'in pe,'Actual original observer PE32 machine')
 except BaseException:error=traceback.format_exc();(out/'failure.txt').write_text(error)
 for p,h in pins.items():need(sha(p)==h,'Actual original32 compiler input/output conservation')
 report=dict(passed=error is None,scope='Original32 actual source instruction observer with genuine provider load/bootstrap and explicit relocated short conditional branches, compile and link only',preparation=str(prep),preparation_sha256=expected,worker=str(worker),worker_sha256=sha(worker)if worker.is_file()else None,machine='I386',root=0x4af240,root_count=1,objects=[dict(path=str(p),sha256=sha(p))for p in objects],actual_compiler_headers=[str(p)for p in headers],actual_linker_libraries=[dict(path=str(p),sha256=sha(p))for p in libraries],commands=commands,files=pins,LIB_environment=os.environ.get('LIB',''),original_executed=False,native_executed=False,archive_reader_opened=False,writer_admission_required=True,initializer_credit=0,error=error,seconds=time.perf_counter()-started)
 q=out/'build.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=error is None,path=str(q),sha256=sha(q),error=error)));sys.exit(int(error is not None))
if __name__=='__main__':main(*sys.argv[1:])
