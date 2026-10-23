"""Ordinary sealed current native141 own BEFORE adapter; endpoint files are separate."""
from pathlib import Path
import struct,re
FIXED=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000)
def need(v,m):
 if not v:raise ValueError(m)
def rows(b,f):
 need(len(b)%struct.calcsize(f)==0,"Exact typed input extent");return list(struct.iter_unpack(f,b))
def build(a,level,seq,root,current_source,owner_cut,metadata_model,physical_contracts,heap_field_model):
 stem=f"sequence-{seq}/";table=a.words("selected-table.bin",141);phase=table.index(root);need(phase=={0x4103f0:13,0x410440:14,0x459b40:39}[root],"Exact current physical selected constructor141 chronology");base=stem+"selected/";names={};number={}
 for key in a.entries:
  match=re.fullmatch(re.escape(base)+r"registry-checkpoint-(\d+)-name.bin",key)
  if match:
   name=a.data(key).decode();prefix=key[:-9];number[prefix]=int(match[1]);names.setdefault(name,[]).append(prefix)
 def unique(name):need(len(names.get(name,[]))==1,"Exact named checkpoint "+name);return names[name][0]
 starts=sorted(names["constructor-mfc-before"],key=lambda x:number[x]);ends=sorted(names["constructor-mfc-after"],key=lambda x:number[x]);need(len(starts)==len(ends)==8,"Exact eight physical constructor MFC call checkpoint pairs");which=(0x4103f0,0x410440,0x459b40).index(root);first=(0,3,6)[which];last=(2,5,7)[which];prior=next(k for k,v in number.items()if v==number[starts[first]]-1);end=min((v for v in names["widget-onexit-after"]if number[v]>number[ends[last]]),key=lambda x:number[x])
 beforekey=stem+f"Constructors/root-{root}/before/";afterkey=stem+f"Constructors/root-{root}/after/";native=a.data(stem+f"phase-{phase}.bin");state=a.data(beforekey+"State.bin");cpu=a.data(beforekey+"CPU.bin");fx=a.data(beforekey+"FX.bin");need((len(native),len(state),len(cpu),len(fx))==(159716,3504,40,512),"Entire own current constructor machine")
 need(cpu==native[36:76]and fx==native[116:628],"Same genuine phase/component BEFORE architecture")
 need(current_source['level']==level and current_source['sequence']==seq and current_source['root']==root and current_source['phase']==phase,"Exact current carried native source row")
 need(current_source['AFTER_seed']is False and current_source['source_seed']is False and current_source['whole_native_component_journals_compared']is True and current_source['whole_native_State_CPU_FX_compared']is True,"Current fullcarried source component gate, no isolated current-result substitution")
 import hashlib
 need(hashlib.sha256(state).hexdigest()==current_source['computed_before_State_sha256']and list(struct.unpack('<10I',cpu))==current_source['computed_before_CPU']and hashlib.sha256(fx).hexdigest()==current_source['computed_before_FX_sha256'],"Every genuine fullownBEFORE equals independently carried literal source projection")
 memory={int(key[len(prior)+6:-4]):a.data(key)for key in a.entries if key.startswith(prior+"-page-")}
 # Native source6 intentionally omitted these checkpoint owner pages from its
 # ordinary export. The ROOT-admitted supplement exposes only the genuine first
 # MFC BEFORE cut; owner bytes carry back to root entry via the complete prefix.
 need(owner_cut['level']==level and owner_cut['sequence']==seq and owner_cut['root']==root and owner_cut['checkpoint_prefix']==starts[first] and owner_cut['checkpoint_name']=='constructor-mfc-before',"Exact genuine first borrowed MFC BEFORE owner cut")
 call=current_source['constructor_call_results'][0];journal=current_source['whole_literal_source_accesses'];need(call[0]==root and call[2]==0x5abd26 and call[4]==call[1]+5,"Exact first literal MFC allocator CALL")
 call_indices=[i for i,v in enumerate(journal)if v==[call[1],call[3],call[4],4,1]];need(len(call_indices)==1,"One whole source saved-return operand identifies first MFC cut")
 prefix=journal[:call_indices[0]+1];need(not any(v[4] and v[1]<0x32000000 and v[1]+v[3]>0x31000000 for v in prefix),"Complete current source root prefix changes no dynamic owner byte")
 need(owner_cut['pages'] and len({v['address']for v in owner_cut['pages']})==len(owner_cut['pages']),"Distinct complete dynamic owner cuts, never empty stack-only substitute")
 owner_input_addresses=[]
 for row in owner_cut['pages']:
  address=row['address'];raw=bytes.fromhex(row['hex']);need(type(address)is int and 0x31000000<=address<0x32000000 and row['logical_key']==starts[first]+'-page-'+str(address)+'.bin' and row['bytes']==len(raw) and len(raw)>0 and __import__('hashlib').sha256(raw).hexdigest()==row['sha256'],"Whole own actual checkpoint dynamic backing identity")
  need(address not in memory,"Supplement may not replace an existing own input region");memory[address]=raw;owner_input_addresses.append(address)

 for i,page in enumerate(FIXED):memory[page]=native[2276+i*4096:2276+(i+1)*4096]
 for key in a.entries:
  if key.startswith(stem+f"phase-{phase}-before-page-"):memory[int(key.rsplit("-",1)[1][:-4])]=a.data(key)
 memory[0x5f2000]=a.data(stem+f"phase-{phase}-before-constructor-global5F2000.bin")
 heap_field_cut=heap_field_model.prove(current_source,a.data(base+'heap-source-accesses.bin'),a.data(base+'locale-source-accesses.bin'),a.data(base+'heap-create-witness.bin'))
 need(0x78035000 not in memory and heap_field_cut['whole_page_claim']is False and heap_field_cut['bytes']==8,'Only missing finite two DWORD heap input; no whole-page substitute');memory[0x78035000]=bytes.fromhex(heap_field_cut['memory_hex'])
 fsbase=struct.unpack_from("<I",state,2168)[0];old=a.data(beforekey+"accesses.bin");new=a.data(afterkey+"accesses.bin");need(new.startswith(old),"Stable own root causal prefix");access=rows(new[len(old):],"<IIQII");fs_index=next(i for i,v in enumerate(access)if v[1]==fsbase);first=access[fs_index];need(first[3:]==(4,0)and all(not(v[1]<=fsbase<v[1]+v[3]and v[4])for v in access[:fs_index]),"First actual normal FS read precedes all FS writes")
 memory[fsbase]=struct.pack("<I",first[2]);field=dict(address=fsbase,bytes=4,source_PC=first[0],source_access_index=fs_index,value=first[2],whole_TIB_claim=False,no_prior_FS_write=True)
 normal_facts=[list(a.words(base+'locale-api-'+str(i)+'-witness.bin',32,'Q'))for i in range(current_source['API_after'])]
 mfc_births=[list(v)for v in rows(a.data(base+'mfc-allocation-witnesses.bin'),'<32Q')];string_births=[list(v)for v in rows(a.data(base+'strings-witnesses.bin'),'<32Q')];resource=list(a.words(base+'lockit-resource.bin',8,'Q'));growth=[]
 for key in a.entries:
  if key.startswith(base+'registry-growth-')and key.endswith('-witness.bin'):growth.append(list(a.words(key,32,'Q')))
 before_metadata=metadata_model.derive(normal_facts,mfc_births,string_births,resource,growth,current_source['API_before'],physical_contracts);after_metadata=metadata_model.derive(normal_facts,mfc_births,string_births,resource,growth,current_source['API_after'],physical_contracts)
 def table(meta):
  result={}
  for guest,o in meta['owners'].items():
   v=[0]*16;v[:9]=[1,guest,o['requested'],o['extent'],o['mapped_bytes'],o['generation'],o['kind'],o['acquired'],o['native']];result[guest]=v
  return result
 byguest=table(before_metadata);birth_table=table(after_metadata);owners=[]
 def owner(v,raw):
  need(v[2]<=v[3]<=len(raw)and v[4]==len(raw),"Own requested/extent/mapped geometry");return dict(guest=v[1],requested=v[2],extent=v[3],mapped_bytes=v[4],initial_hex=raw[:v[3]].hex(),mapped_tail_hex=raw[v[3]:].hex(),generation=v[5],kind=v[6],capacity=0,native=v[8],live=True)
 for guest,v in byguest.items():
  if guest in memory:owners.append(owner(v,memory[guest]))
 need(all(v in byguest and byguest[v][4]==len(memory[v])for v in owner_input_addresses),"Every supplemental backing joins exact actual allocation mapped extent")
 need(len(owners)=={0x4103f0:8,0x410440:10,0x459b40:19}[root] and sum(v['kind']==1 for v in owners)==1,"Exact current total root-entry owner roles including registry; future births excluded")
 APIs=[]
 for name,prefixes in names.items():
  match=re.fullmatch(r"locale-api-(\d+)-before",name)
  if not match:continue
  prefix=unique(name)
  if not(number[prior]<number[prefix]<number[end]):continue
  index=int(match[1]);p=base+f"locale-api-{index}";w=a.words(p+"-witness.bin",32,"Q");returned_name=f"locale-api-{index}-returned";observed_return=returned_name in names;retpoint=unique(returned_name if observed_return else f"locale-api-{index}-after");need(number[prefix]<number[retpoint]<number[end]and w[:2]==(1,index)and w[14:16]==(1,1)and w[7]in(1,3) and not w[19]and not w[31],"Completed genuine finite normal API")
  fact=dict(site=w[2],target=w[4],argc=w[7],args=list(w[20:20+w[7]]),before_cpu=list(a.words(prefix+"-cpu.bin",10)),after_cpu=list(a.words(retpoint+"-cpu.bin",10)),input_buffers=[],output_buffers=[],initial_allocations=[],native_API_words=list(w),native_API_index=index)
  before_fx=a.data(prefix+"-fx.bin");after_fx=a.data(retpoint+"-fx.bin");need(len(before_fx)==len(after_fx)==512 and before_fx==after_fx,"Whole actual own API entry/return FX512 conservation, no FP output copied");fact["actual_API_before_FX512_hex"]=before_fx.hex();fact["actual_API_after_FX512_hex"]=after_fx.hex()
  if not observed_return:
   need(w[3]in(0x7802e044,0x7802e048)and w[7]==1,"Only exact native CS API shim lacks captured returned checkpoint");fact["actual_API_after_CPU_before_shim"]=list(fact["after_cpu"]);fact["source_shim_return_derived"]=["ESP","EIP"];need(fact["after_cpu"][0]==fact["before_cpu"][0],"VOID CS source shim preserves EAX");fact["after_cpu"][4]=w[5]+4*(w[7]+1);fact["after_cpu"][9]=w[6];fact["postRET_observed"]=False
  else:fact["postRET_observed"]=True
  if w[3]==0x7802e094:
   v=birth_table[w[12]];initial=a.data(p+"-output-0.bin");need(len(initial)==w[13]==w[22]==v[3]and v[6]==4,"Actual constructor API initial allocation bytes/extent");full=initial+bytes(v[4]-v[3]);newowner=owner(v,full);fact["initial_allocations"]=[newowner]
  elif w[3]==0x7802e1dc:
   raw=a.data(p+"-input-0.bin");fact["input_buffers"]=[dict(address=w[22],bytes=len(raw),hex=raw.hex())];output=a.data(p+"-output-0.bin");need(len(output)==w[17]==w[12],"Actual HeapSize full capacity bytes");fact["output_buffers"]=[dict(address=w[22],bytes=len(output),hex=output.hex())]
  elif w[3]in(0x7802e044,0x7802e048):
   raw=a.data(p+"-input-0.bin");need(len(raw)==24 and p+"-output-0.bin"not in a.entries,"Actual native CS association conserves guest24; no copied native40 output");fact["input_buffers"]=[dict(address=w[20],bytes=24,hex=raw.hex())]
  else:raise ValueError("Unknown constructor source API slot "+hex(w[3]))
  APIs.append(fact)
 APIs.sort(key=lambda v:v["native_API_index"]);need(len(APIs)==5,"Exact two allocator and one genuine callback capacity API")
 return dict(branch=level,root=root,BEFORE_State_hex=state.hex(),BEFORE_CPU_hex=cpu.hex(),BEFORE_FX_hex=fx.hex(),BEFORE_ENV28_hex=native[2164:2192].hex(),BEFORE_memory={str(k):v.hex()for k,v in memory.items()},owners=owners,APIs=APIs,imports=[dict(PC=pc,address=address,raw=int.from_bytes(memory[address&~4095][address%4096:address%4096+4],"little"),target=target,owning_named_input=True)for pc,address,target in((0x5abd1a,0x5bb4c8,0x5f401782),(0x5abd26,0x5bb4bc,0x5f401ea0),(0x5ac11e,0x5bb52c,0x78004a36))],FS_observed_field=field,heap_initial_field_cut=heap_field_cut,source_AFTER_seed=False,own_prior_checkpoint=prior,prior_checkpoint_nonphase_regions_carry_physical_review_pending=True,owner_input_cut=owner_cut['checkpoint_prefix'],owner_input_prefix_call_index=call_indices[0],owner_input_prefix_no_dynamic_write=True,owner_input_snapshot_is_constructor_MFC_BEFORE=True,static_pages_from_actual_root_BEFORE=True,causal_owner_metadata=before_metadata,metadata_API_cut=current_source['API_before'],future_allocation_summary_used=False)
