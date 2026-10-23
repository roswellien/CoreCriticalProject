"""ROOT admission of one bounded helper lift; no target execution or credit."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
out=R/'reports/m4-loader-message-review/recursive-lifter-root-review-r1'
need(not out.exists(),'Fresh ROOT review');out.mkdir(parents=True)
pins={}
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Physical identity '+str(p));pins[str(p)]=v;return p
report=pin(R/'reports/m4-loader-message-review/recursive-lifter-build-r2/report.json','8d3458569ebe11786443b198bba58163de24ef8c818d10972753d44e8fdbed72')
v=json.loads(report.read_bytes());need(v['passed'] and not v['clone_executed'] and v['initializer_credit']==0,'Build-only parent')
directory=report.parent
delta=json.loads(pin(directory/'source-delta.json',v['files'][str(directory/'source-delta.json')]).read_bytes())
old=pin(R/'local/tools/remill-x87-control-repair/source/bin/lift/Lift.cpp',v['files'][str(R/'local/tools/remill-x87-control-repair/source/bin/lift/Lift.cpp')]).read_text()
new=pin(directory/'Lift.cpp',v['files'][str(directory/'Lift.cpp')]).read_text()
need(old.count(delta['before'])==1 and new.count(delta['after'])==1,'Unique finite cache repair')
need(old.replace(delta['before'],delta['after'])==new and new.replace(delta['after'],delta['before'])==old,'Whole source exact inverse')
trace=pin(R/'local/tools/remill-v6.0.1/remill-6.0.1/lib/BC/TraceLifter.cpp',v['files'][str(R/'local/tools/remill-v6.0.1/remill-6.0.1/lib/BC/TraceLifter.cpp')]).read_text()
need(trace.count('manager.SetLiftedTraceDefinition(trace_addr, func);')==1,'One completed-definition publication')
publication=trace.index('manager.SetLiftedTraceDefinition(trace_addr, func);')
need(trace.rfind('callback(trace_addr, func);',0,publication)>trace.rfind('for (auto &block : *func)',0,publication),'Publish only after body closure and callback')
need('func = GetLiftedTraceDefinition(trace_addr);\n    if (func) {\n      continue;\n    }' in trace,'Worklist reuses completed definition')
exe=pin(directory/'remill-lift-recursive-entry-21.exe','19b3f3d0905ae2f77eca0c2f35e97e3b9ca31dd22dbd699371d4c6480eb70869')
pin(__file__)
result=dict(passed=True,scope='Whole exact local source inverse and completed-cache publication ordering; admit one bounded helper lift only',helper_PC=0x10001740,maximum_retry_seconds=120,helper_retry_admitted=True,tool_path=str(exe),tool_sha256=sha(exe),first_discovery_retained=True,installed_tools_modified=False,DLL_loaded=False,native_executed=False,initializer_credit=0,files=pins)
p=out/'report.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(p),sha256=sha(p))))
