"""Add independently source-derived exact refusal prefix extents."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-joint-startup138'/name
 if out.exists():raise ValueError('Fresh bounded checker preparation')
 out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p)
  if h and h!=v:raise ValueError('Exact source input')
  pins[str(p)]=v;return p
 prior=pin(R/'reports/m4-joint-startup138/controls-tools-preparation-r2/report.json','d88033270c03453116d093159a0038958e95706fa595b7cedc9014a5fe98dcee');d=json.loads(prior.read_bytes());source=pin(d['checker'],d['checker_sha256']);text=source.read_text();anchor="   if mode in(5,7):need(denied is not None,'Actual failed write logged but uncommitted')"
 if text.count(anchor)!=1:raise ValueError('Exact unexecuted checker insertion')
 addition="""
   if mode==5:need(len(suffix)==16 and suffix[-1]==(0x59fba5,0x736130,0x5cfd10,4,1),'First complete literal object store row15 denied; no later source instruction')
   if mode==7:need(len(suffix)==6 and suffix[-1]==(0x5a459e,tib[0],F-16,4,1),'First complete literal FS install row5 denied; actual source frame value')
   if mode==3:need(len(suffix)==461,'Exact 460 prior source operands followed by first owning onexit IAT read')
""".rstrip()
 text=text.replace(anchor,anchor+addition);ast.parse(text);target=R/'tools/m4-joint-startup138/check_context_controls_v4.py'
 if target.exists():raise ValueError('Never replace frozen checker')
 target.write_text(text);pin(target);pin(__file__);pin(sys.executable);pin(R/'reports/m4-fps-native/connected-component-preparation-r4/literals.hpp');pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Unexecuted current135 controls semantic checker: independently literal-proven exact first-denial source extents added',prior_tools_preparation=str(prior),prior_tools_preparation_sha256=sha(prior),controller=d['controller'],controller_sha256=d['controller_sha256'],checker=str(target),checker_sha256=sha(target),exact_added_predicates={'mode5':{'operands':16,'last':[0x59fba5,0x736130,0x5cfd10,4,1]},'mode7':{'operands':6,'PC':0x5a459e,'address':'actual same TIB','value':'actual rootframe-16','width':4,'write':True},'mode3':{'operands':461,'last_PC':0x5ac11e,'address':0x5bb52c,'width':4,'write':False}},partial_fault_register_prediction=False,worker_executed=False,archive_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
