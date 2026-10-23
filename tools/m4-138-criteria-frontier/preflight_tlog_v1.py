"""Exact source inverse and synthetic worker/compiler-ID tlog lineage controls."""
from pathlib import Path
import json,hashlib,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prep=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r7';pr=json.loads((prep/'report.json').read_bytes());out=prep.parent/'tlog-preflight-r1';assert not out.exists();pins={str(prep/'report.json'):sha(prep/'report.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
for p,h in pr['files'].items():assert sha(Path(p))==h;pins[p]=h
d=pr['checker_source_delta'];s=(R/'tools/m4-138-criteria-frontier/check_schema138_v6.py').read_text();assert s.count(d['after'])==1 and s.replace(d['after'],d['before'])==(R/'tools/m4-138-criteria-frontier/check_schema138_v5.py').read_text()
code='\n'.join(x[2:]if x.startswith('  ')else x for x in d['after'].splitlines());tests=[]
def trial(label,mutation=None,bad=False):
 tree=(R/'synthetic-build').resolve();of=(R/'synthetic-preparation').resolve();target='mw34_joint_startup124_original';project=tree/(target+'.vcxproj');linked=tree/'Release'/(target+'.exe');worker=tree.parent/'synthetic-copy.exe';td=tree/(target+'.dir')/'Release';tlog=td/'tracked.tlog/CL.read.1.tlog';compilerid=tree/'CompilerId/Debug/CompilerId.tlog/CL.read.1.tlog'
 paths=[project,linked,tlog,compilerid]
 if mutation=='duplicate worker tlog':paths.append(td/'second.tlog/CL.read.1.tlog')
 if mutation=='compiler-ID only':paths.remove(tlog)
 files={str(p):'h'for p in paths};condition="'$(Configuration)|$(Platform)'=='Release|Win32'"
 source=(of/'reference.cpp')if mutation!='wrong source'else(of/'other.cpp')
 xml=('<Project xmlns="http://schemas.microsoft.com/developer/msbuild/2003"><PropertyGroup><IntDir Condition="'+condition+'">'+str(Path(target+'.dir')/'Release')+'</IntDir><TargetName Condition="'+condition+'">'+target+'</TargetName></PropertyGroup><ItemGroup><ClCompile Include="'+str(source)+'"/></ItemGroup></Project>').encode()
 def blob(p,h=None):
  p=Path(p)
  if p==of/'CMakeLists.txt':return ('add_executable('+target+' reference.cpp foo.asm)').encode()
  if p==project:return xml
  return b'actual-linked-payload'if p==linked or mutation!='different copied worker'else b'other'
 text='^'+str(of/('wrong.cpp'if mutation=='wrong compile header'else'reference.cpp'))+'\n'
 class FakeFile:
  def read_text(self,**k):return text
 env=dict(Path=Path,ob=dict(commands=[dict(arguments=['--build',str(tree),'--config','Release'],exit_code=0)],worker=str(worker),worker_sha256='h'),orr=dict(files=files),of=of,blob=blob,pin=lambda *a:FakeFile(),measurements={})
 try:exec(compile(code,'synthetic exact compiler attribution','exec'),env);assert env['tlogs']==[tlog]
 except (AssertionError,KeyError):assert bad
 else:assert not bad,'Adverse admitted '+label
 tests.append(dict(label=label,passed=True,adverse=bad))
trial('current266 domain distinguished from compiler-ID3')
for m in ('duplicate worker tlog','compiler-ID only','wrong source','different copied worker','wrong compile header'):trial(m,m,True)
out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Synthetic exact build/project/source/output tlog controls only; no actual checker or compiler run',tests=tests,whole_checker_inverse=True,files=pins),indent=2)+'\n');print(sha(q))
