"""Workspace-local exact completed-entry cache repair, compile/link only.

Uses existing compile_commands/build.ninja/library toolchain; replaces no
installed or previously admitted lifter. ROOT admission precedes any retry.
"""
from pathlib import Path
import hashlib,json,os,re,shlex,subprocess,sys,time,traceback
R=Path(__file__).resolve().parents[2]
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-loader-message-review/recursive-lifter-build-r1';need(not out.exists(),'Fresh local lifter clone');out.mkdir(parents=True);pins={};commands=[];passed=False;started=time.monotonic();libraries=[];compiler='';linkargs=[]
 def pin(p):
  p=Path(p).resolve();v=sha(p);need(str(p)not in pins or pins[str(p)]==v,'Stable recursive tool dependency');pins[str(p)]=v;return p
 def run(argv,label,cwd=None):
  t=time.monotonic();p=subprocess.run(argv,cwd=cwd,capture_output=True,timeout=180,creationflags=0x08000000);(out/(label+'.stdout')).write_bytes(p.stdout);(out/(label+'.stderr')).write_bytes(p.stderr);commands.append(dict(argv=argv,cwd=str(cwd)if cwd else None,exit_code=p.returncode,seconds=time.monotonic()-t));need(p.returncode==0,'Local clone build '+label);return p
 try:
  source=pin(R/'local/tools/remill-x87-control-repair/source/bin/lift/Lift.cpp');original=source.read_text();before='''    // The entry function needs to be lifted by the TraceLifter
    if (addr == entry) {
      return nullptr;
    }''';after='''    // A completed trace must be reused, including recursive entry calls.
    // SetLiftedTraceDefinition publishes this cache only after body closure.
    auto completed = traces.find(addr);
    if (completed != traces.end()) {
      return completed->second;
    }
    // The first entry discovery still needs to be lifted by TraceLifter.
    if (addr == entry) {
      return nullptr;
    }''';need(original.count(before)==1,'Exact old recursive-entry deficiency');patched=original.replace(before,after);need(patched.replace(after,before)==original,'Exact source inverse');local=out/'Lift.cpp';local.write_text(patched);pin(local)
  base=R/'local/tools/remill-v6.0.1/remill-6.0.1';build=base/'build';recipe=pin(build/'compile_commands.json');ninja=pin(build/'build.ninja');pin(base/'lib/BC/TraceLifter.cpp');pin(R/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe');pin(R/'local/tools/remill-x87-control-repair/semantics/x86.bc');pin(R/'tools/x87-repair/prepare_toolchain.py');pin(R/'reports/m4-loader-message-review/literal-sorter-lifts-r1/report.json')
  entry=[e for e in json.loads(recipe.read_bytes())if e['file'].replace('\\','/').endswith('/bin/lift/Lift.cpp')];need(len(entry)==1,'One retained lifter compile recipe');compiler=entry[0]['command'];obj=out/'Lift.cpp.obj';compiler,n=re.subn(r'/Fo\S+','/Fo'+obj.as_posix(),compiler);need(n==1,'Exact isolated object output');compiler,n=re.subn(r'/Fd\S+','/Fd'+out.as_posix()+'/',compiler);need(n==1,'Exact isolated PDB output');oldsrc=Path(entry[0]['file']);compiler=compiler.replace(str(oldsrc),str(local)).replace(oldsrc.as_posix(),local.as_posix());need(str(local)in compiler or local.as_posix()in compiler,'Exact isolated lifter source');compiler+=' /showIncludes';p=run(compiler,'compile',build)
  for line in p.stdout.decode('utf-8',errors='replace').splitlines():
   match=re.search(r'Note: including file:\s*(.+)$',line)
   if match:pin(match[1].strip())
  block=re.search(r'^build bin/lift/remill-lift-21.exe:[^\n]*\n((?:  [^\n]*\n)+)',ninja.read_text(),re.M);need(block,'Exact retained lifter link block');match=re.search(r'^  LINK_LIBRARIES = (.+)$',block[1],re.M);need(match,'Exact retained link libraries');words=[w.strip('"')for w in shlex.split(match[1],posix=False)];options=[]
  for word in words:
   if word.startswith('-'):options.append('/'+word[1:]);continue
   path=Path(word);candidate=path if path.is_absolute()else build/path
   if not candidate.is_file():candidate=next((Path(d)/word for d in os.environ.get('LIB','').split(';')if d and(Path(d)/word).is_file()),None)
   need(candidate is not None and candidate.is_file(),'Every actual existing link library resolved '+word);libraries.append(str(pin(candidate)))
  exe=out/'remill-lift-recursive-entry-21.exe';linkargs=[str(obj),*libraries,'/link','/machine:x64','/INCREMENTAL:NO','/subsystem:console',*options,'/OUT:'+str(exe)];rsp=out/'link.rsp';rsp.write_text(subprocess.list2cmdline(linkargs));clang=pin(R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe');run([str(clang),'@'+str(rsp)],'link',build);pin(exe);pin(obj)
  for path,h in list(pins.items()):need(sha(path)==h,'All inputs stable after isolated clone build')
  delta=out/'source-delta.json';delta.write_text(json.dumps(dict(before=before,after=after,inverse_equal=True,only_completed_cache_changed=True),indent=2)+'\n');pin(delta);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  pin(__file__);pin(Path(__file__).with_suffix('.ps1'));pin(sys.executable)
  for q in out.iterdir():
   if q.is_file():pin(q)
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Exact completed-entry LLVM trace cache repair; workspace-local compiled clone of current control lifter; no lift retry or target execution',recursive_entry_original_PC=0x10001740,actual_recursive_CALL_PCs=[0x10001a23,0x10001a35],source_inverse_to_current_control_lifter=True if passed else False,completed_definitions_reused_only=True if passed else False,first_entry_discovery_retained=True if passed else False,commands=commands,link_libraries=len(libraries),seconds=time.monotonic()-started,clone_executed=False,helper_retry_admitted=False,DLL_loaded=False,worker_executed=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),tool_sha256=pins.get(str(out/'remill-lift-recursive-entry-21.exe')))))
if __name__=='__main__':main()
