"""Current worker tlog ownership via actual build/project/source/output lineage."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r6';assert sha(old/'report.json')=='e337ba3bd78f717dd25dc7888bb164042f9c01526d9e82db331f34787eea0549'
pr=json.loads((old/'report.json').read_bytes());out=old.parent/'schema-checker-preparation-r7';assert not out.exists();out.mkdir();pins={str(old/'report.json'):sha(old/'report.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
for n in ['accepted131-materialized.py','native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py','native-linked.py','inputs.json']:
 p=old/n;assert sha(p)==pr['files'][str(p)];pins[str(p)]=sha(p);q=out/n;q.write_bytes(p.read_bytes());pins[str(q)]=sha(q)
parent=R/'tools/m4-138-criteria-frontier/check_schema138_v5.py';assert sha(parent)=='06343be28bc404d11cbaf923a098c894f91435d56f55198a8297ec17914d26df';pins[str(parent)]=sha(parent);s=parent.read_text()
before="  tlogs=[Path(p)for p in orr['files']if p.endswith('CL.read.1.tlog')];assert len(tlogs)==1"
after='''  # The closure also retains CMake compiler-ID records. Select the worker
  # domain through its actual compiler command, project IntDir/source and
  # identical linked/copy executable, not a success-only basename filter.
  import xml.etree.ElementTree as ET
  actual_build=[x for x in ob['commands']if '--build'in x['arguments']];assert len(actual_build)==1 and actual_build[0]['exit_code']==0
  args=actual_build[0]['arguments'];tree=Path(args[args.index('--build')+1]).resolve();assert args[args.index('--config')+1]=='Release'
  target='mw34_joint_startup124_original'
  assert ('add_executable('+target+' reference.cpp ')in blob(of/'CMakeLists.txt').decode()
  project=tree/(target+'.vcxproj');xml=ET.fromstring(blob(project,orr['files'][str(project)]));ns={'m':'http://schemas.microsoft.com/developer/msbuild/2003'}
  condition="'$(Configuration)|$(Platform)'=='Release|Win32'"
  intdirs=[x.text for x in xml.findall('.//m:IntDir',ns)if x.attrib.get('Condition')==condition];assert len(intdirs)==1
  names=[x.text for x in xml.findall('.//m:TargetName',ns)if x.attrib.get('Condition')==condition];assert names==[target]
  included=[Path(x.attrib['Include']).resolve()for x in xml.findall('.//m:ClCompile',ns)if 'Include'in x.attrib];assert (of/'reference.cpp').resolve()in included
  linked=tree/'Release'/(target+'.exe');assert blob(linked,orr['files'][str(linked)])==blob(ob['worker'],ob['worker_sha256'])
  worker_intdir=(tree/intdirs[0]).resolve()
  tlogs=[Path(p)for p in orr['files']if Path(p).name=='CL.read.1.tlog' and Path(p).parent.parent.resolve()==worker_intdir];assert len(tlogs)==1
  headers=[x[1:]for x in pin(tlogs[0],orr['files'][str(tlogs[0])]).read_text(encoding='utf-16').splitlines()if x.startswith('^')]
  assert headers and any(Path(x).resolve()==(of/'reference.cpp').resolve()for h in headers for x in h.split('|'))
  measurements['original_compiler_tlog_domain']=dict(project=str(project),IntDir=str(worker_intdir),worker=str(linked),tlog=str(tlogs[0]),copied_worker_sha256=ob['worker_sha256'],retained_other_tlogs=sum(Path(p).name=='CL.read.1.tlog'for p in orr['files'])-1)
'''
assert s.count(before)==1;s=s.replace(before,after);assert s.replace(after,before)==parent.read_text()
q=R/'tools/m4-138-criteria-frontier/check_schema138_v6.py';assert not q.exists();q.write_text(s);pins[str(q)]=sha(q)
result=dict(passed=True,scope='Code-only exact current build/project/tlog/compiler source and linked output ownership; inherited consumed266 predicate unchanged',whole_extracted_baseline_predicates_preserved=True,checker_source_delta=dict(before=before,after=after,parent_sha256=sha(parent)),files=pins)
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(sha(out/'report.json'));print(sha(q))
