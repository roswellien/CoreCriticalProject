"""Generate an unexecuted additive literal widget model and bounded contracts."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-widget-source'
PINS={}
def need(v,t):
 if not v:raise ValueError(t)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.zip','.mwb'),'No capture payload');v=sha(p);need(h is None or h==v,'Exact source/model dependency');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
MODEL=r'''"""Literal widget source from current BEFORE and measured typed API effects.

Prepared only: no original or native execution proof. Virtual targets retain
same-instance most recent vptr writes; array targets retain actual helper
frames, source caller arguments and iteration. No opaque GDI pointer seed.
"""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('accepted130_widget_parent',R/'reports/m4-formatting-source/persistent-family-model-r1/persistent_model.py')
G=importlib.util.module_from_spec(s);s.loader.exec_module(G)
I=G.I;begin_root=G.begin_root;complete_root=G.complete_root
def frozen(path,h):
 raw=(R/path).read_bytes();I.need(hashlib.sha256(raw).hexdigest()==h,'Exact widget source contract');return json.loads(raw)
def contracts():return frozen('reports/m4-widget-source/lift-preparation-r1/instruction-contracts.json','CONTRACT_HASH')
def source_program():
 program,callbacks=G.source_program()
 for row in contracts()['instructions']:
  pc=row['pc'];I.need(pc not in program or program[pc]==row,'Exact retained and additive widget instruction');program[pc]=row
 data=frozen('reports/m4-widget-source/game-callbacks-r1/callbacks.json','CALLBACK_HASH')
 for pc,offsets in data['State_offsets_by_original_PC'].items():
  pc=int(pc);offsets=tuple(offsets);I.need(pc not in callbacks or callbacks[pc]==offsets,'Identical literal undefined callback attribution');callbacks[pc]=offsets
 return program,callbacks
class Machine(G.Machine):
 def __init__(self,*args,widget_imports=None,**kwargs):
  super().__init__(*args,**kwargs);self.widget_active=False;self.widget_root=None
  self.widget_imports=widget_imports or {};self.widget_vptrs={};self.widget_virtual_calls=[]
  self.widget_array_frames=[];self.widget_arrays=[];self.widget_import_reads=[];self.widget_strings=[]
  data=contracts();self.widget_indirects={r['CALL_pc']:r for r in data['source_indirect_contracts']}
  self.widget_vptr_stores={r['source_vptr_store_PC']:r['source_vptr']for r in data['source_indirect_contracts']}
  self.widget_array_contracts=data['source_array_contracts']
 def begin_widget(self,root):
  I.need(not self.widget_active and self.cursor==root,'One actual current selected widget CALL')
  I.need(root in {r['entry']for r in contracts()['selected_roots']},'Exact selected widget root')
  I.need(self.word(I.BASE['ds'])==self.word(I.BASE['es'])==self.word(I.BASE['ss'])==0 and not self.flag('DF'),'Actual flat widget source segments and forward REP input')
  self.widget_active=True;self.widget_root=root
 def end_widget(self):
  I.need(self.widget_active and not self.widget_array_frames,'Complete widget source RET with balanced array frames')
  self.widget_active=False;self.widget_root=None
 def write(self,address,value,size=4,domain='source',pc=None):
  original_pc=self.word(2472)if pc is None else pc
  result=super().write(address,value,size,domain,pc)
  if self.widget_active:
   # Any overlapping store invalidates an earlier token, including API or
   # untyped writes. Only literal current-instance 32-bit stores replace it.
   for base in list(self.widget_vptrs):
    if address<base+4 and base<address+size:del self.widget_vptrs[base]
   if domain=='source' and size==4 and original_pc in self.widget_vptr_stores:
    I.need(value==self.widget_vptr_stores[original_pc],'Literal instance vptr store value')
    self.widget_vptrs[address]=dict(PC=original_pc,value=value,source_access_index=len(self.accesses)-1,root=self.widget_root)
  return result
 def read(self,address,size=4,domain='source',pc=None):
  original_pc=self.word(2472)if pc is None else pc
  value=super().read(address,size,domain,pc)
  if not self.widget_active or domain!='source':return value
  binding=self.widget_indirects.get(original_pc)
  if binding is not None:
   I.need(size==4 and address==binding['slot'] and value==binding['target'],'Exact current readonly source vtable slot')
   instance=self.reg('ecx');token=self.widget_vptrs.get(instance)
   I.need(token and token['root']==self.widget_root and token['PC']==binding['source_vptr_store_PC']and token['value']==binding['source_vptr'],'Same current instance most recent literal source vptr store')
   I.need(self.bytes(instance,4)==binding['source_vptr'].to_bytes(4,'little'),'Current carried instance vptr unchanged')
   self.widget_virtual_calls.append(dict(root=self.widget_root,PC=original_pc,instance=instance,source_store=dict(token),slot=address,target=value,ESP=self.reg('esp'),source_access_index=len(self.accesses)-1))
  imports={0x5a013c:0x5bb070,0x5a063f:0x5bb074,0x5a074b:0x5bb068}
  if original_pc in imports:
   I.need(size==4 and address==imports[original_pc],'Exact owning widget API import operand')
   response=self.widget_imports.get((original_pc,address));I.need(response is not None,'Unmeasured genuine widget API import remains denied')
   I.need(type(response['raw_value'])is int and value==response['raw_value']and type(response['target'])is int and response['target']>0,'Exact own branch raw import and named service target; caller authenticates API identity')
   self.widget_import_reads.append(dict(root=self.widget_root,PC=original_pc,slot=address,raw_value=value,target=response['target'],source_access_index=len(self.accesses)-1))
   return response['target']
  return value
 def step(self):
  pc=self.cursor
  if not self.widget_active:return super().step()
  if pc==0x517680:I.need(self.bytes(0x6384e8,4)==bytes(4),'Actual current zero font registry input; raw BSS is insufficient')
  if pc==0x5a2f40:I.need(self.bytes(self.reg('esp')+8,4)==bytes(4),'Current literal null format argument')
  I.need(pc not in(0x5ac24b,0x5a075b),'Reverse unwind and CreateFont failure/error branches are retained unadmitted frontiers')
  if pc==0x5ac2a0:
   f=self.call_stack[-1];I.need(f[0]==pc and f[1]==self.reg('esp'),'Actual entered vector helper CALL frame')
   matches=[r for r in self.widget_array_contracts if r['CALL_pc']==f[3]and self.widget_root in r['roots']];I.need(len(matches)==1,'Exact current caller-bound vector contract')
   c=matches[0];base=int.from_bytes(self.bytes(f[1]+4,4),'little');args=[int.from_bytes(self.bytes(f[1]+4*(i+2),4),'little')for i in range(4)]
   I.need(args==[c['stride'],c['count'],c['constructor'],c['destructor']],'Whole actual vector argument frame')
   root=next(r for r in contracts()['selected_roots']if r['entry']==self.widget_root)
   I.need(base==root['object']+c['base_root_offset'],'Literal current root object and array base')
   event=dict(root=self.widget_root,caller=f[3],frame=f[1],base=base,contract=c,iterations=[]);self.widget_array_frames.append(event);self.widget_arrays.append(event)
  if pc==0x5ac2db:
   I.need(self.widget_array_frames,'Current active vector invocation');a=self.widget_array_frames[-1];c=a['contract'];i=self.reg('esi')
   I.need(self.reg('ebp')==a['frame']-4 and i==len(a['iterations'])and i<c['count'],'Actual helper frame and ordered bounded source iteration')
   I.need(self.reg('ecx')==a['base']+i*c['stride']and int.from_bytes(self.bytes(self.reg('ebp')+0x14,4),'little')==c['constructor'],'Same caller callback and exact current element')
   a['iterations'].append(dict(PC=pc,iteration=i,instance=self.reg('ecx'),target=c['constructor'],ESP=self.reg('esp'),source_access_index=len(self.accesses)))
  if pc==0x5ac30c:
   I.need(self.widget_array_frames,'Current successful array RET');a=self.widget_array_frames[-1]
   I.need(self.reg('esp')==a['frame']and len(a['iterations'])==a['contract']['count'],'Full constructor count and genuine RET14 frame');self.widget_array_frames.pop()
  if pc==0x5a2f55:
   I.need(not self.flag('DF')and self.word(I.BASE['es'])==0 and self.reg('ecx')==128 and self.reg('eax')==0,'Exact source forward zero REP STOSD extent')
   self.widget_strings.append(dict(PC=pc,address=self.reg('edi'),bytes=512,source_access_index=len(self.accesses)))
  return super().step()
'''
def main(name):
 out=B/name;need(not out.exists(),'Fresh widget literal model');out.mkdir(parents=True)
 p=read(B/'lift-preparation-r1/report.json','b1778f7359075bae0c6c2afa0f5745b864b481f2e762dce64b385bb16c9a01dd');need(p['passed'],'Exact widget literal preparation')
 contracts=pin(B/'lift-preparation-r1/instruction-contracts.json');callback=read(B/'game-callbacks-r1/report.json','d9d5f1832af4aa5e1c8cd7ae864beacae1f32efd312a656fecddf661a04d65a4');pin(B/'game-callbacks-r1/callbacks.json',callback['callbacks_sha256'])
 parent=read(R/'reports/m4-formatting-source/persistent-family-model-r1/report.json','53c2a9f6dc3ede4ed5b089ff7c92490bbcdd4113679fc35ba830a4e359f50887');pin(parent['model'],parent['model_sha256'])
 text=MODEL.replace('CONTRACT_HASH',sha(contracts)).replace('CALLBACK_HASH',callback['callbacks_sha256'])
 model=R/'tools/m4-widget-source/game_model.py';need(not model.exists(),'Fresh widget source model');model.write_text(text);pin(model)
 sp=importlib.util.spec_from_file_location('widget_model_preflight',model);G=importlib.util.module_from_spec(sp);sp.loader.exec_module(G);program,callbacks=G.source_program()
 pin(__file__)
 report=dict(passed=True,scope='Imported literal source program and preparatory same-instance/caller-frame guards only; no source execution, authentic API response or runtime acceptance',model=str(model),model_sha256=sha(model),counts=dict(program_instructions=len(program),callback_sites=len(callbacks),widget_source_instructions=1081,widget_array_CALL_sites=4,widget_vptr_slot_bindings=17),original_executed=False,native_executed=False,source_model_executed=False,initializer_credit=0,files=PINS)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),counts=report['counts'])))
if __name__=='__main__':main(sys.argv[1])
