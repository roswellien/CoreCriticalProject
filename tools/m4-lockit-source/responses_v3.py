"""Independent typed source API extension for a genuine native MSVCP CS owner.

Guest CS24 output is derived from the observed serial original ABI fields and
the source-established depth/thread; native CS40 is separately checked as an
actual Windows witness. No whole AFTER State/CPU/FX/page or candidate guard
enters this model, and a resource association does not claim source DllMain.
"""
from pathlib import Path
import struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
import provider_responses_v2 as PRIOR
I=PRIOR.I
CS=0x78145640
class ActualResponses(PRIOR.ActualResponses):
 def __init__(self,facts):
  super().__init__(facts);self.lockit_images=[];self.lockit_image_index=0;self.lockit_relations=[];self.lockit_thread=0;self.lockit_original_CS=b''
 def associate_lockit(self,m,resource,actual_images,authentic_CS):
  # The lifecycle raw field is an explicit research-seam marker from the PE,
  # not a source IAT CALL. Genuine source Enter/Leave imports are read below.
  w=self.facts[self.index]['words'];resource=tuple(resource);I.need(self.index==4 and w[:5]==(1,4,0,0x78146190,0x866ce)and w[5:8]==(0,0,0)and w[8]==1 and w[14:16]==(1,1)and w[16]and w[31]==1,'Actual measured native resource association at the explicit research lifecycle seam')
  I.need(w[9]==w[11]and not self.facts[self.index]['inputs']and not self.facts[self.index]['outputs'],'Association preserves caller LastError and transports no source bytes')
  I.need(len(resource)==8 and resource[0:2]==(1,1)and resource[3:6]==(CS,24,40)and resource[6]and resource[7]==0,'Typed independently associated guest24/native40 resource identity')
  I.need(len(authentic_CS)==24 and m.bytes(CS,24)==authentic_CS and int.from_bytes(m.bytes(0x78145658,4),'little')==2,'Exact genuine original loaded CS and state2 input')
  d=struct.unpack('<6I',authentic_CS);I.need(d[1:5]==(0xffffffff,0,0,0),'Genuine initialized unheld original CS baseline')
  I.need(CS not in self.sections,'Fresh fifth static section resource');self.generation+=1;I.need(resource[2]==self.generation,'Actual resource generation follows carried bootstrap owners')
  self.sections[CS]=dict(generation=self.generation,depth=0,native=w[16],enters=0,leaves=0,initialized=True,deletes=0)
  self.lockit_thread=resource[6];self.lockit_original_CS=bytes(authentic_CS);self.lockit_images=list(actual_images);I.need(len(self.lockit_images)==8 and all(len(b)==40 for b in self.lockit_images),'Eight complete actual native CS40 after API observations')
  for site,slot,name in((0x7810a30b,0x78146198,'EnterCriticalSection'),(0x7810a35e,0x78146184,'LeaveCriticalSection')):
   self.contracts[site]=dict(name=name,slot=slot,raw=int.from_bytes(m.bytes(slot,4),'little'),argc=1,tail=False,void=True)
  self.index+=1
 def __call__(self,m,target):
  site=m.PCs[-1]
  if site not in(0x7810a30b,0x7810a35e):return super().__call__(m,target)
  I.need(self.index<len(self.facts)and self.lockit_image_index<len(self.lockit_images),'Finite complete genuine Lockit API witnesses');fact=self.facts[self.index];w=tuple(fact['words']);c=self.contracts[site];frame=m.reg('esp');ret=int.from_bytes(m.bytes(frame,4),'little');arg=int.from_bytes(m.bytes(frame+4,4),'little')
  I.need(w[:8]==(1,self.index,site,c['slot'],c['raw'],frame,ret,1)and target==c['raw']and arg==CS and w[20]==CS and not w[19]and w[14:16]==(1,1),'Literal source-derived actual Lockit CALL/API/argument/stdcall frame')
  I.need(w[9]==w[11]and w[9]<=0xffffffff and w[10]<=0xffffffff and w[8]==w[12]==0,'Actual caller LastError restored and VOID guest EAX has no fabricated result')
  entry=self.sections[CS];I.need(entry['initialized']and entry['native']==w[16]and w[17]==40,'Exact live full-native owner remains associated')
  before=m.bytes(CS,24);I.need(fact['inputs']==[before]and len(fact['outputs'])==1,'Whole independently carried CS24 input and one typed semantic output')
  self.active=self.index;tag='locale-api-'+str(self.index);m.snapshot(tag+'-before');m.emit('api-before',index=self.index,fact=fact,contract=c)
  if c['name']=='EnterCriticalSection':entry['depth']+=1;entry['enters']+=1
  else:I.need(entry['depth']>0,'Same-thread balanced source Leave');entry['depth']-=1;entry['leaves']+=1
  depth=entry['depth'];I.need(w[18]==depth and 0<=depth<=2,'Actual observed serial original recursion domain')
  image=self.lockit_images[self.lockit_image_index];lockcount,recursion=struct.unpack_from('<iI',image,8);thread=struct.unpack_from('<Q',image,16)[0]
  expected_lock=0xffffffff if depth==0 else 0xfffffffe;expected_thread=self.lockit_thread if depth else 0
  I.need(lockcount&0xffffffff==expected_lock and recursion==depth and thread==expected_thread,'Actual CS40 Windows field witness agrees with source depth/current thread and original serial ABI')
  expected=bytearray(self.lockit_original_CS);struct.pack_into('<III',expected,4,expected_lock,depth,expected_thread);actual=fact['outputs'][0];I.need(actual==bytes(expected),'Complete semantic guest CS24 derived from original opaque identity and genuine native field effects')
  I.need(w[13]==24 and w[29]==1 and w[30]==1,'Explicit full CS input/output payload cardinality and extent')
  for offset in range(0,24,4):m.write(CS+offset,int.from_bytes(expected[offset:offset+4],'little'),4,domain='transport',pc=site)
  m.snapshot(tag+'-after');m.api_return(site,1,m.reg('eax'));self.lockit_relations.append(dict(API_index=self.index,source_PC=site,frame=frame,return_pc=ret,guest_CS=CS,native_owner=w[16],generation=entry['generation'],depth=depth,LockCount=expected_lock,OwningThread=expected_thread,derived_CS24_hex=expected.hex(),actual_native_CS40_hex=image.hex(),actual_API_words=list(w)))
  self.index+=1;self.active=None;self.lockit_image_index+=1
 def lockit_complete(self):
  e=self.sections[CS];I.need(self.lockit_image_index==8 and e['enters']==e['leaves']==4 and e['depth']==0,'All four rooted constructor/destructor API pairs exhaust actual source witnesses')

# Preserve the explicit contract interface used by the capture adapter.
B=PRIOR.B
NEW_CONTRACTS=PRIOR.NEW_CONTRACTS
