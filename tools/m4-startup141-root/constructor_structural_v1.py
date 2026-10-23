"""Strict bounded37 transport, source-witness, actual owner and hardware gate.

This gate does not substitute for literal source evaluation or original pairing.
Only this current native capture is opened, after both admitted writers close.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
R=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def rows(raw,fmt):
 width=struct.calcsize(fmt);need(len(raw)%width==0,'Whole typed record extent');return list(struct.iter_unpack(fmt,raw))
def host(raw):
 need(len(raw)==1632,'Entire measured caller hardware boundary');a=raw[:512];b=raw[1088:1600];need(a[:5]==b[:5]and a[24:28]==b[24:28]and raw[512:540]==raw[1600:1628]and a[160:416]==b[160:416]and all(a[32+16*i:42+16*i]==b[32+16*i:42+16*i]for i in range(8)),'Caller architectural CW/status/tag/MXCSR/raw80/XMM/ENV restoration')

def validate_sequence(data,seq,roots,widget_roots,source,cold,expectedcalls):
 prefix=f'sequence-{seq}/'
 final=prefix+f'Constructors/root-{roots[-1]}/after/';access=rows(data.data(final+'accesses.bin'),'<IIQII');calls=rows(data.data(final+'calls.bin'),'<12I');getters=rows(data.data(final+'getters.bin'),'<12I');FS=rows(data.data(final+'FS-events.bin'),'<12I')
 need([(v[0],v[1],v[2],v[5])for v in calls]==expectedcalls,'Exactly six actual MFC allocations/two genuine NULL825 source calls');need(all(v[4]==v[1]+5 and v[3]>=0x20001000 and v[3]+8<=0x20002000 for v in calls),'Full direct source CALL frames/returns')
 for v in access:need(v[0]in source and v[0]not in cold and v[3]in(1,2,4)and v[4]in(0,1),'Only current physical admitted literal source operands')
 need(len(getters)==2 and all(v[0]==roots[1]and v[1]==0x58b183 and v[4:8]==(0x604008,0x5bcc68,0x5bcc80,0x40a850)and v[10]>0 and v[11]==v[9]+1 for v in getters),'Two exact current published non-sentinel readonly-vptr getters')
 need(sum(v[5]==1 for v in FS)==sum(v[5]==2 for v in FS)>0 and FS[-1][6]==0,'All actual normal source FS installations/restorations balanced')
 for i,root in enumerate(roots):
  stem=prefix+f'Constructors/root-{root}/after/';status=data.words(stem+'status.bin',8);need(status[0]==1 and status[2]==root and status[3]==0x20001800 and status[4:7]==(0,0,i+1),'Complete serial constructor status/own real root frame');need(len(data.data(stem+'State.bin'))==3504 and len(data.data(stem+'CPU.bin'))==40 and len(data.data(stem+'FX.bin'))==512 and data.data(stem+'frames.bin')==b''and data.data(stem+'FS-frames.bin')==b'','Whole current root source machine and empty frame stacks');host(data.data(prefix+f'Constructors/root-{root}/caller-hardware.bin'))
 mirror=rows(data.data(prefix+'selected/constructor-source-mirror-accesses.bin'),'<12Q');writes=[v for v in access if v[4]];privatewrites=[v for v in mirror if v[5]];need([(v[0],v[1],v[3],v[2])for v in writes]==[(v[1],v[2],v[3],v[4])for v in privatewrites],'Every complete literal store joins private typed preimage/mirror witness in exact order')
 start=data.words(prefix+'caller-projection-before/registry.bin',32,'Q');selected_summary=data.words(prefix+'selected/registry-summary.bin',32,'Q');need(selected_summary[9]==start[9]+111,'Exactly25 current source registrations from carried producer BEFORE');projection=rows(data.data(prefix+'selected/locale-research-projections.bin'),'<8I');all_onexit=[v for v in projection if v[0]==9];need(len(all_onexit)==10 and {v[1]for v in all_onexit}==set(roots)|set(widget_roots),'Exact complete ten-root current union API projection domain');new_registrations=[v for v in all_onexit if v[1]in roots];need(new_registrations==[(9,root,0x5ac11e,0x5bb52c,0x1decb0,0x78004a36,0x20001800-24,0x5ac124)for root in roots],'Three exact committed source onexit services and affine real frames');selected=rows(data.data(prefix+'selected/locale-allocations.bin'),'<16Q');cleaned=rows(data.data(prefix+'cleaned/locale-allocations.bin'),'<16Q');byguest={v[1]:v for v in selected};new=[]
 for v in calls:
  if v[2]!=0x5abd26:continue
  a=byguest.get(v[6]);need(a is not None and a[2]==v[5]and a[3]==16 and a[4]>=16 and a[6]==4 and a[8]and a[9]and not a[10]and not a[11],'Real current MFC generation/request/rounded source extent');generation=a[5];initial=data.data(prefix+f'selected/locale-allocation-{generation}-initial.bin');expected=data.data(prefix+f'selected/locale-allocation-{generation}-expected.bin');actual=data.data(prefix+f'selected/locale-allocation-{generation}-owned-page.bin');need(len(initial)==16 and len(expected)==a[4]and actual==expected and expected[a[2]:16]==initial[a[2]:16],'Complete source native extent/mapped mirror and untouched requested tail');new.append(a)
 need(len(new)==6 and len({v[5]for v in new})==6,'Six distinct measured current allocation generations');cleanup={v[5]:v for v in cleaned}
 for a in new:v=cleanup.get(a[5]);need(v is not None and v[1:7]==a[1:7]and not v[8]and v[10]and not v[11],'Actual genuine source MFC825 cleanup of same entire owner generation')
 state=data.words(prefix+'cleaned/registry-summary.bin',32,'Q');need(state[1]and not state[2]and not state[3]and state[4]and state[10:12]==(0,0)and not state[15],'All current Session heap/CS owners genuinely released');need(1<=data.words(prefix+'growth-replay-count.bin',1)[0]<=512,'Inherited full141 genuine source growth is required and bounded')

 return dict(source_operands=len(access),private_mirror_records=len(mirror),FS_events=len(FS),allocations=6,NULL_calls=2,getters=2)
