"""Synthetic idle legacy delegation and exact active-widget borrowing controls."""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-joint-startup138-source/widget-scope-controls-r1';assert not out.exists();out.mkdir()
 helper=R/'tools/m4-joint-startup138/persistent_widgets_v2.py';spec=importlib.util.spec_from_file_location('synthetic_widget_scope',helper);PW=importlib.util.module_from_spec(spec);spec.loader.exec_module(PW)
 checks=[]
 def check(value,name):assert value,name;checks.append(name)
 class GDI:
  def __init__(self):self.calls=[]
  def control(self,*args):self.calls.append(args[1:])
 class Observer:
  def __init__(self):self.calls=[]
  def check(self,m,name):self.calls.append(name)
 class Machine:
  def __init__(self):
   self.state=bytearray(3504);self.fx=bytes(512);self.accesses=[];self._source_undefined_flags={};self.cursor=0x78004a36;self.r={'esp':PW.FRAME-24,'eax':PW.CALLBACKS[0]}
  def reg(self,key):return self.r[key]
  def bytes(self,address,n):assert(address,n)==(PW.FRAME-24,8);return struct.pack('<2I',0x5ac124,PW.CALLBACKS[0])
  def projected_cpu(self):return tuple(range(10))
 m=Machine();gdi=GDI();observer=Observer();a=PW.JournalAssociation(m,observer,gdi,None,0,'synthetic',None)
 legacy={'op':'call','target':0x78004a36,'site':0x5ac11e}
 a.before_control('control',legacy);a.after_control('returned',{'caller':(0x78004a36,), 'frame':PW.FRAME-24})
 check(a.root==0 and a.mode=='provider'and not a.records and not m.accesses and not observer.calls and not gdi.calls,'Idle legacy same-target CALL/RET leaves all widget association journals untouched')
 a.root=PW.WIDGETS[0];a.mode='component';a.root_runtime_cpu=bytes(40);a.component_accesses=[(0x5ac11e,0x5bb52c,0x1decb0,4,0),(0x5ac11e,PW.FRAME-24,0x5ac124,4,1)];a.shared=list(a.component_accesses)
 invalid=dict(legacy,site=0x5ac120)
 try:a.before_control('control',invalid)
 except ValueError as error:check('Only exact literal widget CALL'in str(error),'Active widget still refuses wrong literal borrowed CALL site')
 else:raise AssertionError('Active strict guard bypassed')
 check(a.mode=='component'and not a.records,'Rejected active CALL commits no provider association')
 a.before_control('control',legacy)
 check(a.mode=='provider'and len(a.records)==1 and m.accesses==a.shared and observer.calls==[f'widget-onexit-{a.root}-before'],'Exact active widget CALL keeps strict operands/frame/callback and provider observer entry')
 m.r['esp']=PW.FRAME-20;m.cursor=0x5ac124;m.accesses.append((0x78004a36,0x1234,1,4,0))
 a.after_control('returned',{'caller':(0x78004a36,), 'frame':PW.FRAME-24})
 check(a.mode=='component'and a.records[0]['returned'] and observer.calls[-1]==f'widget-onexit-{a.root}-after','Exact active provider RET preserves frame/callback/journal and provider observer return checks')
 class ParentMachine:
  def __init__(self):self.calls=[]
  def emit(self,event,**data):self.calls.append((event,data));return 'parent-result'
 class Spy:
  def __init__(self,root):self.root=root;self.calls=[]
  def before_control(self,*args):self.calls.append('before')
  def after_control(self,*args):self.calls.append('after')
 wrapper=PW.machine_class(ParentMachine)();idle=Spy(0);wrapper.widget_association=idle
 check(wrapper.emit('control',**legacy)=='parent-result'and not idle.calls and len(wrapper.calls)==1,'Idle machine emit delegates exactly once through original parent')
 active=Spy(PW.WIDGETS[0]);wrapper.widget_association=active
 check(wrapper.emit('control',**legacy)=='parent-result'and active.calls==['before','after']and len(wrapper.calls)==2,'Active machine emit wraps one original parent emission')
 class ParentObserver:
  def __init__(self):self.calls=[]
  def check(self,m,name):self.calls.append(('check',name));return 'checked'
  def string_event(self,m,event,data):self.calls.append(('event',event));return 'observed'
 O=PW.observer_class(ParentObserver)();m.widget_association=idle;idle.mode='provider'
 check(O.check(m,'legacy')=='checked'and O.string_event(m,'legacy',{})=='observed','Idle provider observer retains both parent callbacks')
 idle.mode='component'
 check(O.check(m,'idle-component')=='checked','Inactive association cannot suppress provider observation even with stale component mode')
 m.widget_association=active;active.mode='component';prior=len(O.calls);O.check(m,'component');O.string_event(m,'component',{})
 check(len(O.calls)==prior,'Active component observer suppression stays confined to actual widget root')
 active.mode='provider'
 check(O.check(m,'borrowed-provider')=='checked','Active borrowed provider observer still delegates parent check')
 files={str(p):sha(p)for p in(helper,Path(__file__).resolve())}
 report=dict(passed=True,scope='Synthetic scope/delegation checks only; no source/capture/native execution',checks=checks,active_widget_guards_retained=True,legacy_parent_delegation=True,canonical_reader_opened=False,native_worker_launched=False,source_model_executed=False,initializer_credit=0,files=files)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),checks=len(checks))))
if __name__=='__main__':main()
