"""Literal constructor observer extension of the unmodified old68 MFC ledger.

All boundaries compare the same persistent source machine. Captured checkpoint
bytes are comparison targets only. Constructor records never enter old ledgers.
"""
from pathlib import Path
import importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PREP=ROOT/'reports/m4-native141-source/observer-preparation-r5'
sys.path.insert(0,str(PREP))
import final_observer141_parent_v2 as P
import hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
from constructor_journal141_v2 import Association
from constructor_native_outputs141_v2 import install_named,compare as compare_native_constructor
FORMAT_ROOTS=P.FORMAT_ROOTS
F=P.F;S=P.S;B=F.B;COUNTS=P.COUNTS;ROWS=P.ROWS;need=F.need
ROOTS=(0x4103f0,0x410440,0x459b40)
WIDGETS=(0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0)
ORDER_PATH=ROOT/'reports/m4-startup141-runway/readiness-r1/selected-order141.json'
SITES={(r,pc):(0x5abd26,size)for r in ROOTS[:2]for pc,size in((0x58af12,12),(0x58af6a,4))}
SITES.update({(r,0x58af9a):(0x5abd1a,0)for r in ROOTS[:2]})
SITES.update({(ROOTS[2],pc):(0x5abd26,12)for pc in(0x58f2a2,0x45b80e)})
def word(m,a):return int.from_bytes(m.bytes(a,4),'little')
def checkpoint_index(a,stem):
 order=json.loads(ORDER_PATH.read_bytes());need(len(order)==141 and [order[n]['entry']for n in(13,14,39)]==list(ROOTS),'Exact141 physical selected constructor positions')
 borrowed=[v['entry']for v in order if v['entry']in ROOTS+WIDGETS]
 need(len(borrowed)==10 and len(set(borrowed))==10,'Exact three constructor and seven widget chronology')
 rows=[]
 for key in a.entries:
  match=re.fullmatch(re.escape(stem)+r'registry-checkpoint-(\d+)-name.bin',key)
  if match:rows.append((int(match[1]),a.data(key).decode(),key[:-9]))
 rows.sort();index={};onbefore=onafter=mfcbefore=mfcafter=0
 for n,label,prefix in rows:
  if label=='widget-onexit-before':
   need(onbefore==onafter and onbefore<10,'Serial ten literal onexit entries');root=borrowed[onbefore];onbefore+=1;label=('constructor'if root in ROOTS else'widget')+f'-onexit-{root}-before'
  elif label=='widget-onexit-after':
   need(onafter+1==onbefore and onafter<10,'Same ten onexit frames return');root=borrowed[onafter];onafter+=1;label=('constructor'if root in ROOTS else'widget')+f'-onexit-{root}-after'
  elif label=='constructor-mfc-before':
   need(mfcbefore==mfcafter and mfcbefore<8,'Serial eight literal constructor MFC entries');label=f'constructor-mfc-{mfcbefore}-before';mfcbefore+=1
  elif label=='constructor-mfc-after':
   need(mfcafter+1==mfcbefore and mfcafter<8,'Same eight constructor MFC frames return');label=f'constructor-mfc-{mfcafter}-after';mfcafter+=1
  need(label not in index,'Every checkpoint preserved exactly once '+label);index[label]=prefix
 need(onbefore==onafter==10 and mfcbefore==mfcafter==8,'All20 onexit and16 MFC boundaries retained')
 return index
class Observer(P.Observer):
 def __init__(self,*a,**k):
  super().__init__(*a,**k);self.constructor_mfc=[];self.constructor_call_rows=[];self.constructor_projections=[];self.constructor_active_call=None;self.constructor_free=None;self.constructor_root_order=[];self.constructor_onexit=None;self.constructor_FS_observations=[];self.constructor_game_FS_serial=0;self.constructor_mirror_rows=[];self.constructor_call_results=[]
 def mfc_event(self,m,event,data):
  if self.free_active is not None and any(self.free_active is r for r in self.constructor_mfc):
   need(self.constructor_free is None or self.constructor_free is self.free_active,'One exact source cleanup record');self.constructor_free=self.free_active
  active=self.root in ROOTS and getattr(m,'constructor_active',False)
  if not active and self.constructor_free is None:return super().mfc_event(m,event,data)
  if self.constructor_free is not None:
   record=self.constructor_free;w=record['words'];owner=next(a for a in m.responses.allocations if a['generation']==w[18])
   if event=='read-after'and data['domain']=='source'and (data['pc'],data['address'])==(0x5f401786,0x5f498148):need(data['bytes']==4 and data['value']==0x7800138a,'Physical named free import retained during new owner cleanup');record['free_import']=True
   if event=='control'and data['op']=='call'and data['site']==0x5f401786:
    frame=m.reg('esp');need(record.get('free_import')and data['target']==0x78001390 and frame==w[26]-8 and word(m,frame)==0x5f40178c and word(m,frame+4)==owner['guest'],'New constructor owner cleanup exact original825 CRT free CALL');record['free_frame']=frame
   if event=='returned'and data['caller']and data['caller'][0]==0x78001390:need(data['frame']==record.get('free_frame')and not owner['live']and owner['guest']not in m.memory,'Genuine new constructor source free unmaps exact current generation');record['free_return']=True
   if event=='returned'and data['caller']and data['caller'][0]==0x5f401782:
    need(record.get('free_return')and data['frame']==w[26]and m.reg('esp')==w[26]+4 and not owner['live'],'Complete new owner original825 return');w[30]=1;self.constructor_free=None;self.free_active=None;COUNTS['constructor_whole_source_cleanup_frees']+=1
   return
  if event=='control'and data['op']=='call'and data['target']in(0x5abd26,0x5abd1a):
   root=self.root;site=data['site'];target=data['target'];frame=m.reg('esp');need((root,site)in SITES and SITES[root,site]==(target,word(m,frame+4))and word(m,frame)==site+5,'Exact physical eight constructor MFC CALL sites, arguments and committed return word')
   need(self.constructor_active_call is None,'One source MFC invocation active');slot=0x5bb4bc if target==0x5abd26 else 0x5bb4c8;raw=0x80000337 if target==0x5abd26 else 0x80000339
   need(word(m,slot)==raw,'Retained owning raw game ordinal');record=dict(root=root,site=site,thunk=target,frame=frame,ret=site+5,request=word(m,frame+4),generation_before=m.responses.generation,API_before=m.responses.index)
   self.constructor_active_call=record;self.constructor_call_rows.append((11,root,site,target,slot,raw,frame,site+5));self.check(m,f'constructor-mfc-{len(self.constructor_call_rows)-1}-before')
  if event=='control'and data['op']=='jmp'and data['site']in(0x5abd26,0x5abd1a):
   c=self.constructor_active_call;target=0x5f401ea0 if data['site']==0x5abd26 else 0x5f401782;frame=m.call_stack[-1]
   need(c is not None and c['thunk']==data['site']and data['target']==target and frame[0]==data['site']and frame[1]==c['frame']and frame[3]==c['site'],'Exact constructor thunk JMP uses unchanged genuine CALL frame')
   m.call_stack[-1]=(target,)+frame[1:];c['entry']=target;COUNTS['constructor_literal_tail_frame_namings']+=1
  if event=='returned'and data['caller']:
   c=self.constructor_active_call;entry=data['caller'][0]
   if c is not None and entry==0x780012b3 and c['request']:
    owner=m.responses.allocations[-1];need(owner['kind']==4 and owner['guest']==m.reg('eax')and owner['requested']==c['request']and owner['extent']==16 and owner['live'],'Literal malloc returns same actual source-born MFC owner')
    w=[0]*32;w[16]=owner['guest'];w[18]=owner['generation'];w[7]=owner['requested'];self.constructor_mfc.append(dict(words=w,root=c['root'],site=c['site'],native=owner['native']));c['generation']=owner['generation']
   if c is not None and entry==c.get('entry'):
    need(data['frame']==c['frame']and m.reg('esp')==c['frame']+4 and m.cursor==c['ret'],'Whole genuine constructor MFC return boundary')
    if c['request']:need(c.get('generation')and m.reg('eax')==self.constructor_mfc[-1]['words'][16],'Whole positive MFC result is acquired source owner')
    else:need(m.responses.generation==c['generation_before']and m.responses.index==c['API_before'],'True free(NULL) has zero allocation/API effects')
    self.constructor_call_results.append((c['root'],c['site'],c['thunk'],c['frame'],c['ret'],c['request'],m.reg('eax'),0,0,0,0,0));self.check(m,f'constructor-mfc-{len(self.constructor_call_rows)-1}-after');self.constructor_active_call=None
 def string_event(self,m,event,data):
  super().string_event(m,event,data)
  if self.root not in ROOTS or not getattr(m,'constructor_active',False):return
  if event=='control'and data['op']=='call'and data['site']==0x5ac11e:
   frame=m.reg('esp');need(data['target']==0x78004a36 and word(m,0x5bb52c)==0x1decb0 and word(m,frame)==0x5ac124 and self.constructor_onexit is None,'Exact constructor source onexit IAT and committed CALL')
   self.constructor_onexit=(self.root,frame);self.constructor_projections.append((9,self.root,0x5ac11e,0x5bb52c,0x1decb0,0x78004a36,frame,0x5ac124));self.check(m,f'constructor-onexit-{self.root}-before')
  if event=='returned'and data['caller']and data['caller'][0]==0x78004a36:
   need(self.constructor_onexit==(self.root,data['frame'])and m.reg('esp')==data['frame']+4 and m.cursor==0x5ac124,'Exact source constructor onexit RET');self.check(m,f'constructor-onexit-{self.root}-after');self.constructor_onexit=None
 def finish(self,m,responses,roots,G):
  need(self.constructor_root_order==list(ROOTS)and len(self.constructor_mfc)==6 and len(self.constructor_call_rows)==8 and len(self.constructor_projections)==3 and self.constructor_active_call is None and self.constructor_onexit is None,'Complete carried three constructors, six positive and two NULL MFC calls, three source onexit')
  super().finish(m,responses,roots,G)
  need(self.constructor_free is None and all(r['words'][30]==1 for r in self.constructor_mfc),'Every new constructor owner actually source-freed and complete825 returned');COUNTS['complete141_constructor_observer_sequences']+=1;COUNTS['constructor_source_allocations']+=6
  ROWS[-1].update(MFC_count_domain='Inherited68 witness ledger; constructor6 source births separately proved',inherited_MFC_allocations=68,constructor_MFC_allocations=6,union_MFC_allocations=74,inherited_source_frees=88,constructor_source_frees=6,union_source_frees=94,whole_owners=98,whole_selected_callbacks=111)
def configure(G,numeric,archive,seq,level,pin):
 pin(__file__);pin(PREP/'report.json');pin(PREP/'final_observer141_parent.py');pin(PREP/'final_observer141_parent_v2.py');pin(ORDER_PATH)
 F.Observer=OBSERVER_CLASS;observer=F.configure(G,numeric,archive,seq,level,pin)
 if not getattr(B.R,'constructor141_owner_roles',False):
  B.R.ActualResponses=G.response_class(B.R.ActualResponses);B.R.constructor141_owner_roles=True
 if not getattr(B.R,'constructor141_mfc_classification',False):
  parent=B.R.ActualResponses
  class ConstructorMfcResponses(parent):
   def __call__(self,m,target):
    c=getattr(m,'constructor_active',False);count=len(self.allocations);super().__call__(m,target)
    if c and len(self.allocations)>count:
     need(len(self.allocations)==count+1 and any(f[0]==0x5f401ea0 for f in m.call_stack),'Only genuine constructor source MFC malloc birth classified kind4');self.allocations[-1]['kind']=4
  B.R.ActualResponses=ConstructorMfcResponses;B.R.constructor141_mfc_classification=True
 return observer
def constructor_phase(m,responses,root,a,seq,level,phase):
 o=S.CURRENT;need(root in ROOTS and o.seq==seq and o.level==level and m.cursor==root and not getattr(m,'constructor_active',False),'Same configured carried constructor machine')
 o.root=root;o.runtime_cpu=B.cpu(m.state);count=len(o.constructor_mfc);install_named(m,o);call_start=len(o.constructor_call_results);association=Association(m,o,root);m.hook=association.observer_hook
 start_FS=len(m.constructor_FS_events);start_getters=len(m.constructor_getters);start_publications=len(m.constructor_publications);start_flags=len(m.constructor_flag_consumers)
 try:before=m.run_carried_constructor(root,responses)
 except BaseException:
  m.hook=association.hook;m.accesses=association.full
  raise
 proof=association.finish()
 need(len(o.constructor_mfc)-count==2,'Two exact source-owned allocations per carried constructor');o.constructor_root_order.append(root)
 o.constructor_FS_observations.extend(proof['game_FS_observations']);o.constructor_mirror_rows.extend(proof['constructor_mirror_rows']);proof['constructor_call_results']=[list(r)for r in o.constructor_call_results[call_start:]]
 h=lambda b:hashlib.sha256(bytes(b)).hexdigest()
 proof.update(root=root,sequence=seq,level=level,phase=phase,computed_before_State_sha256=h(before['State']),computed_before_CPU=list(before['CPU']),computed_before_FX_sha256=h(before['FX']),computed_after_State_sha256=h(m.state),computed_after_CPU=list(m.projected_cpu()),computed_after_FX_sha256=h(m.fx),API_before=before['response_index'],API_after=responses.index,source_FS_events=m.constructor_FS_events[start_FS:],source_getters=m.constructor_getters[start_getters:],source_owned_writes=m.constructor_publications[start_publications:],source_defined_flag_consumers=m.constructor_flag_consumers[start_flags:])
 compare_native_constructor(a,seq,root,before,m,proof,o)
 return proof
def prove_constructor_projections(m,raw):
 o=S.CURRENT;need(len(raw)%32==0,'Whole8DWORD projection extent');rows=list(struct.iter_unpack('<8I',raw));ctors=[r for r in rows if r[0]==9 and r[1]in ROOTS]
 need(ctors==o.constructor_projections and len(ctors)==3,'All-and-only three literal constructor tag9 rows')
 need([r for r in rows if r[0]==11]==o.constructor_call_rows,'All-and-only eight complete literal constructor MFC projection rows')
 order=json.loads(ORDER_PATH.read_bytes());expected=[v['entry']for v in order if v['entry']in ROOTS+WIDGETS]
 need([r[1]for r in rows if r[0]==9]==expected,'Whole ten borrowed rows in actual physical141 temporal order')
 return b''.join(struct.pack('<8I',*r)for r in rows if not(r[0]==9 and r[1]in ROOTS))
begin=F.begin;end=F.end;finish=F.finish

OBSERVER_CLASS=Observer
def install_widget_observer(PW):
 global OBSERVER_CLASS
 OBSERVER_CLASS=PW.observer_class(Observer)
 return OBSERVER_CLASS

from constructor_fs_union141_v1 import partition as _partition_normal_FS
def partition_normal_FS(archive,stem):
 return _partition_normal_FS(archive,stem,S.CURRENT,ROOTS)

_owners_parent=Observer.owners
def _owners141(self,m,responses,stage,expected_callbacks):
 _owners_parent(self,m,responses,stage,expected_callbacks)
 actual=list(struct.iter_unpack('<12Q',self.a.data(f'sequence-{self.seq}/{stage}/constructor-source-mirror-accesses.bin')))
 need(actual==[tuple(r)for r in self.constructor_mirror_rows],'Whole constructor mirror journal from current source operands/owners/generations')
 need(self.a.words(f'sequence-{self.seq}/{stage}/constructor-FS-source-scope.bin',2)==(0,0),'All literal constructor component/provider ownership scopes closed')
Observer.owners=_owners141


def pin_current_inputs(pin):
 """Authenticate all pre-audit child source before a capture reader opens."""
 receipt=ROOT/'reports/m4-native141-source/observer-preparation-r5/report.json'
 current=json.loads(pin(receipt,'ac0ff78b6038f3f47d2edfaaef5b923cd0a6dac6b8797e68f232f87297f06a7d').read_bytes())
 need(current['passed'] and current['source_only'] and not current['canonical_reader_opened'],'Exact current source-only observer preparation')
 for path,digest in current['files'].items():pin(path,digest)
 for path in (__file__,Association.__module__,install_named.__module__,_partition_normal_FS.__module__):
  source=sys.modules[path].__file__ if path in sys.modules else path
  pin(source)
 return dict(pinned_before_capture_open=True,physical_preparation=str(receipt),physical_files=len(current['files']),AFTER_seed=False)
