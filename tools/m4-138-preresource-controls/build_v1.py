"""Compile one new control TU; reuse every current138 provider/literal object."""
from pathlib import Path
import hashlib,json,re,subprocess,os,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def words(s):return [x.replace('$:',':').replace('$ ',' ')for x in re.findall(r'(?:\$ |[^\s])+',s.strip())]
def main(preparation,digest,name):
 out=R/'reports/m4-138-preresource-controls'/name;assert not out.exists();out.mkdir(parents=True);pins={};commands=[];workers={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or h==v,(p,h,v);pins[str(p)]=v;return p
 def run(args,label):
  args=list(map(str,args));pin(args[0]);r=subprocess.run(args,capture_output=True,cwd=R,timeout=180,creationflags=0x08000000);(out/label).write_bytes(r.stdout+r.stderr);commands.append(dict(arguments=args,exit_code=r.returncode,log=label));print(label,r.returncode,flush=True);assert r.returncode==0,(r.stdout+r.stderr)[-6000:];return (r.stdout+r.stderr).decode(errors='replace')
 try:
  pr=json.loads(pin(preparation,digest).read_bytes());assert pr['passed'] and pr['worker_executed']is False and pr['execution_admitted']is False;prep=Path(preparation).parent
  for p,h in pr['files'].items():pin(p,h)
  build=json.loads(pin(pr['parent_build'],pr['parent_build_sha256']).read_bytes());assert build['passed']
  llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';pin(__file__);pin(Path(__file__).with_suffix('.ps1'));pin(sys.executable)
  for level,w in build['workers'].items():
   assert level in('O0','O2');bf=Path(w['path']).parent;pin(w['path'],w['sha256']);graph=pin(bf/'build.ninja').read_text()
   native_block=next(x for x in graph.split('\n\n')if x.startswith('build CMakeFiles\\mw34_joint_startup138.dir\\native_main.cpp.obj:'))
   flags=next(x.split(' = ',1)[1]for x in native_block.splitlines()if x.strip().startswith('FLAGS = '));includes=next(x.split(' = ',1)[1]for x in native_block.splitlines()if x.strip().startswith('INCLUDES = '));defines=next(x.split(' = ',1)[1]for x in native_block.splitlines()if x.strip().startswith('DEFINES = '))
   folder=out/level;folder.mkdir();obj=folder/'controls_main.obj'
   args=[llvm/'clang-cl.exe','/nologo','-TP']+words(defines)+['-I'+str(prep)]+words(includes)+['-I'+str(R/'tools/m4-crt-commandline-carry'),'-I'+str(R/'tools/m4-crt-locale-batch')]+words(flags)+['/Fo'+str(obj),'/Fd'+str(folder/'controls_main.pdb'),'-c','--',prep/'controls_main.cpp']
   log=run(args,level+'-compile.log');deps=[]
   for line in log.splitlines():
    if 'Note: including file:'in line:
     q=Path(line.split('Note: including file:',1)[1].strip());assert q.is_file();deps.append(str(pin(q)))
   assert str((prep/'native_main.cpp').resolve())in deps and str((Path(pr['parent_preparation']).parent/'widget_services.hpp').resolve())in deps
   link_block=next(x for x in graph.split('\n\n')if x.startswith('build mw34_joint_startup138.exe:'))
   first=link_block.splitlines()[0];rhs=first.split(': CXX_EXECUTABLE_LINKER__mw34_joint_startup138_Release ',1)[1].split(' | ',1)[0];inputs=[];relations=[]
   for x in words(rhs):
    p=Path(x);p=p if p.is_absolute()else bf/p;p=p.resolve();pin(p,build['files'][str(p)])
    replacement=obj if p.name=='native_main.cpp.obj' and p.parent.name=='mw34_joint_startup138.dir'else p
    inputs.append(replacement);relations.append(dict(parent=str(p),parent_sha256=pins[str(p)],current=str(replacement.resolve()),reused_whole_bytes=replacement==p))
   assert sum(not x['reused_whole_bytes']for x in relations)==1
   libline=next(x.split(' = ',1)[1]for x in link_block.splitlines()if x.strip().startswith('LINK_LIBRARIES = '));libs=words(libline)
   for lib in libs:
    p=Path(lib)
    if p.is_absolute():pin(p,build['files'][str(p)])
    else:
     candidates=[Path(x)/lib for x in os.environ['LIB'].split(';')if x and (Path(x)/lib).is_file()];assert candidates;pin(candidates[0])
   flags_link=next(x.split(' = ',1)[1]for x in link_block.splitlines()if x.strip().startswith('LINK_FLAGS = '));worker=folder/'preresource-controls.exe';rsp=folder/'link.rsp';tokens=[str(x)for x in inputs]+libs+words(flags_link)+['/out:'+str(worker),'/pdb:'+str(folder/'worker.pdb'),'/nologo']
   rsp.write_text('\n'.join('"'+x+'"'for x in tokens)+'\n');pin(rsp)
   run([llvm/'lld-link.exe','@'+str(rsp)],level+'-link.log');pin(obj);pin(worker)
   workers[level]=dict(path=str(worker),sha256=sha(worker),object=str(obj),object_sha256=sha(obj),compiler_dependencies=sorted(set(deps)),linked_input_relations=relations,reused_provider_and_literal_objects=True,positive_hardware_object_reused=True)
  for p,h in pins.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Compile/link only current138 pre-resource modes1..12; all linked inputs reused except exact new control main TU',preparation=str(Path(preparation).resolve()),preparation_sha256=digest,workers=workers,commands=commands,files=pins,worker_executed=False,execution_admitted=False,initializer_credit=0)
  q=out/'build.json';q.write_text(json.dumps(report,indent=2)+'\n');print(sha(q),flush=True)
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
