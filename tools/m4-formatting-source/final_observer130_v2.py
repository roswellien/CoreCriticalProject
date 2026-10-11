"""Add source-derived mixed CALL/RET scalars to the complete130 observer."""
import final_observer130 as F
BaseObserver=F.Observer
S=F.S;COUNTS=F.COUNTS;ROWS=F.ROWS;FORMAT_ROOTS=F.FORMAT_ROOTS
class Observer(BaseObserver):
 def __init__(self,*a,**k):
  super().__init__(*a,**k);self.mixed_source_calls=[]
 def string_event(self,m,event,data):
  super().string_event(m,event,data)
  if self.root!=0x4e1ca0:return
  if event=='control'and data['op']=='call'and data['target']in(0x7810a290,0x7810a350):
   ctor=data['target']==0x7810a290;site=0x4e530f if ctor else 0x4e5389;frame=m.reg('esp');F.need(data['site']==site and m.reg('ecx')==frame+48,'Exact literal mixed LEA and committed CALL frame')
   self.mixed_source_calls.append(dict(root=self.root,PC=site,target=data['target'],frame=frame,return_pc=int.from_bytes(m.bytes(frame,4),'little'),scratch=m.reg('ecx'),EAX_before=m.reg('eax'),API_index=m.responses.index,source_access_entered_index=len(m.accesses),source_CS24_before_hex=m.bytes(0x78145640,24).hex(),source_State_before_hex=bytes(m.state).hex(),source_CPU_before=list(m.projected_cpu()),source_FX_before_hex=m.fx.hex(),returned=False))
  if event=='returned'and data['caller']and data['caller'][0]in(0x7810a290,0x7810a350):
   matches=[r for r in self.mixed_source_calls if not r['returned']and r['target']==data['caller'][0]and r['frame']==data['frame']];F.need(len(matches)==1,'Same literal mixed source invocation returns once');r=matches[0]
   F.need(m.reg('esp')==r['frame']+4,'Exact mixed provider RET source frame')
   r.update(returned=True,EAX_after=m.reg('eax'),API_after=m.responses.index,source_access_returned_index=len(m.accesses),source_CS24_after_hex=m.bytes(0x78145640,24).hex(),source_State_after_hex=bytes(m.state).hex(),source_CPU_after=list(m.projected_cpu()),source_FX_after_hex=m.fx.hex())
F.Observer=Observer
configure=F.configure;begin=F.begin;end=F.end;finish=F.finish
