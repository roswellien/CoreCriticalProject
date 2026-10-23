"""Ordinary sealed native37 own BEFORE adapter; endpoint files are separate."""
from pathlib import Path
import struct,re
FIXED=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000)
def need(v,m):
 if not v:raise ValueError(m)
def rows(b,f):
 need(len(b)%struct.calcsize(f)==0,"Exact typed input extent");return list(struct.iter_unpack(f,b))
def build(a,level,seq,root):
 stem=f"sequence-{seq}/";table=a.words("selected-table.bin",37);phase=table.index(root);base=stem+"selected/";names={};number={}
 for key in a.entries:
  match=re.fullmatch(re.escape(base)+r"registry-checkpoint-(\d+)-name.bin",key)
  if match:
   name=a.data(key).decode();prefix=key[:-9];number[prefix]=int(match[1]);names.setdefault(name,[]).append(prefix)
 def unique(name):need(len(names.get(name,[]))==1,"Exact named checkpoint "+name);return names[name][0]
 prior=unique(f"registry-root-{phase-1}-after");end=unique(f"registry-root-{phase}-after")
 beforekey=stem+f"Constructors/root-{root}/before/";afterkey=stem+f"Constructors/root-{root}/after/";native=a.data(stem+f"phase-{phase}.bin");state=a.data(beforekey+"State.bin");cpu=a.data(beforekey+"CPU.bin");fx=a.data(beforekey+"FX.bin");need((len(native),len(state),len(cpu),len(fx))==(159716,3504,40,512),"Entire own current constructor machine")
 need(cpu==native[36:76]and fx==native[116:628],"Same genuine phase/component BEFORE architecture")
 memory={int(key[len(prior)+6:-4]):a.data(key)for key in a.entries if key.startswith(prior+"-page-")}
 for i,page in enumerate(FIXED):memory[page]=native[2276+i*4096:2276+(i+1)*4096]
 for key in a.entries:
  if key.startswith(stem+f"phase-{phase}-before-page-"):memory[int(key.rsplit("-",1)[1][:-4])]=a.data(key)
 memory[0x5f2000]=a.data(stem+f"phase-{phase}-before-constructor-global5F2000.bin")
 fsbase=struct.unpack_from("<I",state,2168)[0];old=a.data(beforekey+"accesses.bin");new=a.data(afterkey+"accesses.bin");need(new.startswith(old),"Stable own root causal prefix");access=rows(new[len(old):],"<IIQII");fs_index=next(i for i,v in enumerate(access)if v[1]==fsbase);first=access[fs_index];need(first[3:]==(4,0)and all(not(v[1]<=fsbase<v[1]+v[3]and v[4])for v in access[:fs_index]),"First actual normal FS read precedes all FS writes")
 memory[fsbase]=struct.pack("<I",first[2]);field=dict(address=fsbase,bytes=4,source_PC=first[0],source_access_index=fs_index,value=first[2],whole_TIB_claim=False,no_prior_FS_write=True)
 allocation_rows=rows(a.data(base+"locale-allocations.bin"),"<16Q");byguest={v[1]:v for v in allocation_rows};owners=[]
 def owner(v,raw):
  need(v[2]<=v[3]<=len(raw)and v[4]==len(raw),"Own requested/extent/mapped geometry");return dict(guest=v[1],requested=v[2],extent=v[3],mapped_bytes=v[4],initial_hex=raw[:v[3]].hex(),mapped_tail_hex=raw[v[3]:].hex(),generation=v[5],kind=v[6],capacity=0,native=v[8],live=True)
 for guest,v in byguest.items():
  if guest in memory:owners.append(owner(v,memory[guest]))
 APIs=[]
 for name,prefixes in names.items():
  match=re.fullmatch(r"locale-api-(\d+)-before",name)
  if not match:continue
  prefix=unique(name)
  if not(number[prior]<number[prefix]<number[end]):continue
  index=int(match[1]);p=base+f"locale-api-{index}";w=a.words(p+"-witness.bin",32,"Q");retpoint=unique(f"locale-api-{index}-returned");need(number[prefix]<number[retpoint]<number[end]and w[:2]==(1,index)and w[14:16]==(1,1)and w[7]==3 and not w[19]and not w[31],"Completed genuine finite normal API")
  fact=dict(site=w[2],target=w[4],argc=w[7],args=list(w[20:23]),before_cpu=list(a.words(prefix+"-cpu.bin",10)),after_cpu=list(a.words(retpoint+"-cpu.bin",10)),input_buffers=[],output_buffers=[],initial_allocations=[],native_API_words=list(w),native_API_index=index)
  if w[3]==0x7802e094:
   v=byguest[w[12]];initial=a.data(p+"-output-0.bin");need(len(initial)==w[13]==w[22]==v[3]and v[6]==4,"Actual constructor API initial allocation bytes/extent");full=initial+bytes(v[4]-v[3]);newowner=owner(v,full);fact["initial_allocations"]=[newowner]
  elif w[3]==0x7802e1dc:
   raw=a.data(p+"-input-0.bin");fact["input_buffers"]=[dict(address=w[22],bytes=len(raw),hex=raw.hex())];output=a.data(p+"-output-0.bin");need(len(output)==w[17]==w[12],"Actual HeapSize full capacity bytes");fact["output_buffers"]=[dict(address=w[22],bytes=len(output),hex=output.hex())]
  else:raise ValueError("Unknown constructor source API slot "+hex(w[3]))
  APIs.append(fact)
 APIs.sort(key=lambda v:v["native_API_index"]);need(len(APIs)==(3 if root!=0x459b40 else 3),"Exact two allocator and one genuine callback capacity API")
 return dict(branch=level,root=root,BEFORE_State_hex=state.hex(),BEFORE_CPU_hex=cpu.hex(),BEFORE_FX_hex=fx.hex(),BEFORE_memory={str(k):v.hex()for k,v in memory.items()},owners=owners,APIs=APIs,imports=[],FS_observed_field=field,source_AFTER_seed=False,own_prior_checkpoint=prior,prior_checkpoint_nonphase_regions_carry_physical_review_pending=True)
