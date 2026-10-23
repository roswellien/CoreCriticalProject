"""Pure exact finite widget byteflow from authenticated source BEFORE bytes.

No reads initialize memory. Registry stores are returned as obligations for
the caller's independently owned CRT registration/capacity proof.
"""
import hashlib,struct
def need(v,s):
 if not v:raise ValueError(s)
def verify(row,getter,phase,*,crt_source_words):
 before=row['whole_carried_before'];after=row['whole_carried_after'];memory={};counts={'source_reads':0,'source_writes':0,'whole_endpoint_bytes':0};external=[]
 def add(a,raw):
  need(isinstance(raw,bytes)and raw,'Whole immutable source BEFORE input');need(all(a+len(raw)<=b or b+len(v)<=a for b,v in memory.items()),'Unique nonoverlapping source-owned input extent');memory[a]=bytearray(raw)
 def get(a,n):
  owners=[(b,v)for b,v in memory.items()if b<=a and a+n<=b+len(v)];need(len(owners)==1,'Exact existing BEFORE source owner '+hex(a));b,v=owners[0];return bytes(v[a-b:a-b+n])
 def put(a,raw):
  owners=[(b,v)for b,v in memory.items()if b<=a and a+len(raw)<=b+len(v)];need(len(owners)==1,'Exact existing source write owner '+hex(a));b,v=owners[0];v[a-b:a-b+len(raw)]=raw
 p=before['prefix'];q=after['prefix'];need(before['source_equality_only']is True and after['source_equality_only']is True,'Already source-computed whole boundaries')
 need(before['whole_State_bytes']==after['whole_State_bytes']==3504 and before['whole_CPU_bytes']==after['whole_CPU_bytes']==40 and before['whole_FX_bytes']==after['whole_FX_bytes']==512 and before['whole_stack_bytes']==after['whole_stack_bytes']==4096,'Entire boundary geometry')
 for a,n,h in before['Game_regions']:
  raw=getter(p+'game-region-'+str(a)+'.bin');need(len(raw)==n and hashlib.sha256(raw).hexdigest()==h,'Exact producer-authenticated computed BEFORE Game bytes');add(a,raw)
 for a,h in before['provider_pages']:
  raw=getter(p+'provider-source-page-'+str(a)+'.bin');need(len(raw)==4096 and hashlib.sha256(raw).hexdigest()==h,'Exact computed BEFORE provider page');add(a,raw)
 stack=getter(p+'stack.bin');need(len(stack)==4096,'Whole computed source stack');add(0x20001000,stack)
 tib=getter(p+'TIB.bin');need(len(tib)==20,'Every carried TIB DWORD');a,*values=struct.unpack('<5I',tib)
 for o,v in zip((0,4,8,0x18),values):add(a+o,struct.pack('<I',v))
 need(isinstance(crt_source_words,bytes)and len(crt_source_words)==8,'Exact independently derived two CRT birth globals');add(0x78035000,crt_source_words)
 for pc,a,v,n,write in row['source_accesses']:
  need(type(n)is int and n in(1,2,4,8)and type(v)is int and 0<=v<1<<(8*n)and write in(0,1),'Literal source operand type/width');raw=v.to_bytes(n,'little')
  owned=any(b<=a and a+n<=b+len(data)for b,data in memory.items())
  if not owned:
   need(write==1 and n==4 and pc==0x78004a67 and v==row['borrowed_provider']['callback'],'Only independently delegated exact literal registry callback store');external.append(dict(PC=pc,address=a,value=v,width=n));continue
  if write:put(a,raw);counts['source_writes']+=1
  else:need(get(a,n)==raw,'Whole independently reconstructed source read '+hex(pc)+' '+hex(a));counts['source_reads']+=1
 need(len(external)==1,'Exactly one separately owned callback slot publication')
 for a,n,h in after['Game_regions']:
  expected=getter(q+'game-region-'+str(a)+'.bin');need(len(expected)==n and hashlib.sha256(expected).hexdigest()==h and get(a,n)==expected,'Entire independent Game byteflow endpoint');counts['whole_endpoint_bytes']+=n
 for a,h in after['provider_pages']:
  expected=getter(q+'provider-source-page-'+str(a)+'.bin');need(len(expected)==4096 and hashlib.sha256(expected).hexdigest()==h and get(a,4096)==expected,'Whole independent provider-page byteflow endpoint');counts['whole_endpoint_bytes']+=4096
 need(get(0x20001000,4096)==getter(q+'stack.bin'),'Entire independently reconstructed stack endpoint');counts['whole_endpoint_bytes']+=4096
 end=getter(q+'TIB.bin');need(len(end)==20 and struct.unpack_from('<I',end)[0]==struct.unpack_from('<I',tib)[0],'Same carried source TIB owner')
 need(end==struct.pack('<5I',struct.unpack_from('<I',tib)[0],*[int.from_bytes(get(struct.unpack_from('<I',tib)[0]+o,4),'little')for o in(0,4,8,0x18)]),'Entire independently reconstructed TIB endpoint')
 return dict(counts=counts,delegated_registry_callback_store=external[0],whole_memory_byteflow_closed=True,CPU_State_semantics_independently_reexecuted=False)
