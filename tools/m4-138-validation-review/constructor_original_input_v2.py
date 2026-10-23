"""Finite original own BEFORE adapter; FS head event observed, base identity inferred."""
import struct,re
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000,0x5e4000,0x5e5000,0x5e7000,0x72b000,0x731000,0x5f498000,0x736000,0x5f4cc000,0x5bc000,0x5cf000,0x5fc000,0x7810a000,0x78145000,0x78146000)
def need(v,m):
 if not v:raise ValueError(m)
def build(a,seq,root,observations,initial,program,FS_policy):
 phase={0x4103f0:13,0x410440:14,0x459b40:36}[root];raw=a.data(f'phase/{seq}/{phase}.bin');need(len(raw)==356992,'Whole original record');memory={page:raw[2276+i*4096:2276+(i+1)*4096]for i,page in enumerate(PAGES)}
 for key in a.entries:
  if key.startswith(f'phase/{seq}/{phase}/extra-before/'):memory[int(key.rsplit('/',1)[1][:-4])]=a.data(key)
 memory[0x5f2000]=a.data(f'constructor-prerequisites/phase/{seq}/{phase}/BEFORE-constructor/5F2000.bin')
 own=next(v for v in observations if (v['sequence'],v['root'])==(seq,root));owners=[]
 for v in own['whole_live_owners']:
  w=v['metadata'];b=bytes.fromhex(v['whole_backing_hex']);need(w[9]==1 and len(b)==w[8]and w[6]<=len(b),'Genuine whole own BEFORE owner');memory[w[7]]=b;owners.append(dict(guest=w[7],requested=w[6],extent=w[8],mapped_bytes=w[8],initial_hex=b.hex(),mapped_tail_hex='',generation=w[1],kind=w[4],capacity=w[8],live=True))
 for g in ('whole_shared_graph','whole_member_graph'):
  for n in own[g]['nodes']:
   w=n['metadata'];b=bytes.fromhex(n['whole_backing_hex']);need(len(b)==w[3],'Whole own graph node');memory[w[2]]=b
 fs=next(v for v in FS_policy['cases']if (v['sequence'],v['root'])==(seq,root));need(not fs['root_FS_base_directly_observed']and fs['FS_head_not_from_future_TEB'],'Finite original FS policy explicit');memory[fs['FS_base_identity']]=bytes.fromhex(fs['first_FS_event_head_raw4_hex'])
 ledger=a.data(f'phase/{seq}/{phase}/api-ledger.bin');need(len(ledger)%104==0,'API26 exact');APIs=[]
 for index,w in enumerate(struct.iter_unpack('<26I',ledger)):
  kind=w[24];argc=3 if kind in(0,1,2)else 4 if kind==3 else 1;need(w[9]==w[19]==0,'Actual nine DWORD CPU projection zero PC');candidates=[row for pc,row in program.items()if row['mnemonic']=='call'and pc+len(bytes.fromhex(row['bytes_hex']))==w[25]];need(len(candidates)==1,'Unique physical API call return word');row=candidates[0];operand=row['decoded_operands'][0];need(operand['kind']=='memory','Physical indirect API CALL');cell=operand.get('displacement',operand.get('disp'));need(cell is not None,'Literal API IAT');target=int.from_bytes(memory[cell&~4095][cell%4096:cell%4096+4],'little');after=list(w[10:20]);after[9]=w[25];fact=dict(site=row['pc'],target=target,argc=argc,args=list(w[20:20+argc]),before_cpu=list(w[:10]),after_cpu=after,raw_CPU_PC_zero=True,modeled_return_PC_separate=w[25],initial_allocations=[],input_buffers=[],output_buffers=[])
  if kind==0:
   v=next(v for v in initial if v['sequence']==seq and v['phase']==phase and v['metadata'][3]==index);m=v['metadata'];b=bytes.fromhex(v['whole_initial_hex']);need(m[7]==w[10]and m[8]==len(b),'Typed API initial whole backing');fact['initial_allocations']=[dict(guest=m[7],requested=m[6],extent=m[8],mapped_bytes=m[8],initial_hex=b.hex(),mapped_tail_hex='',generation=m[1],kind=m[4],capacity=m[8],live=True)]
  APIs.append(fact)
 bases=dict(ds=0,es=0,ss=0,fs=fs['FS_base_identity'],gs=0,cs=0)
 return dict(branch='original',root=root,BEFORE_CPU_hex=raw[36:76].hex(),BEFORE_FX_hex=raw[116:628].hex(),BEFORE_ENV28_hex=raw[2164:2192].hex(),BEFORE_segment_bases=bases,BEFORE_memory={str(k):v.hex()for k,v in memory.items()},owners=owners,APIs=APIs,imports=[dict(PC=pc,address=address,raw=int.from_bytes(memory[address&~4095][address%4096:address%4096+4],'little'),target=target,owning_named_input=True)for pc,address,target in((0x5abd1a,0x5bb4c8,0x5f401782),(0x5abd26,0x5bb4bc,0x5f401ea0),(0x5ac11e,0x5bb52c,0x78004a36))],original_State_observed=False,source_AFTER_seed=False,FS_input_policy_acceptance_pending=True,segment_bases_directly_observed=False)
