"""Finite formatter4/mixed cross-branch relations from two literal proofs.

Original entry/return-patch observations are retained as observations. Native
post-RET machine state is source-derived; real API volatile state is not equated
across different processes. Every whole backing is derived from its own input.
"""
import collections,struct
ROOTS=(0x4df610,0x4e0710,0x4e0810,0x4e1ca0)
REQUESTS=dict(zip(ROOTS,(8,10,12,11)))
FORMAT_FIELDS=dict(zip(ROOTS,(0x60b5e4,0x60b634,0x60b60c,0x60b66c)))
MIXED_SITES=(0x49cc8d,0x4e5325,0x4e535b)
MIXED_PUBS=((0x49cc9a,0x60b750),(0x4e5334,0x60b7d4),(0x4e5366,0x60b764))
MIXED_STORE_TYPES=(
 ((0x49cc95,0,'self'),(0x49cc97,4,'self')),
 ((0x4e532a,4,'null'),(0x4e532d,20,1),(0x4e5339,0,'null'),(0x4e5343,8,'null')),
 ((0x4e5360,4,'header'),(0x4e5363,20,0),(0x4e5372,0,'self'),(0x4e5381,8,'self')),
)
BYTE_FIELDS=((0x60b74c,0x49cc89,0x49cc8b),(0x60b758,0x4e22b7,0x4e22c4),(0x60b760,0x4e52e6,0x4e52f4),(0x60b761,0x4e52ea,0x4e5303))
def need(v,m):
 if not v:raise ValueError(m)
def equal(a,b,m):need(a==b,m+' '+str((a,b))[:650])
def original_owner(o):
 return dict(guest=o['pointer'],requested=o['request'],capacity=o['capacity'],initial=bytes.fromhex(o['initial_hex']),final=bytes.fromhex(o['source_final_hex']),source=o)
def native_owner(o):
 return dict(guest=o['guest'],requested=o['requested'],capacity=o['extent'],initial=bytes.fromhex(o['initial']),final=bytes.fromhex(o['source_final_hex']),generation=o['generation'],native=o['native'],source=o)
def backing(o,n,capture,stem,counts):
 need(len(o['initial'])==len(o['final'])==o['capacity']and len(n['initial'])==len(n['final'])==n['capacity'],'Both whole genuine capacity backings')
 equal(capture.data(stem+f'locale-allocation-{n["generation"]}-initial.bin'),n['initial'],'Native actual source owner initial capacity')
 want=n['final']+bytes(4096-n['capacity'])
 for suffix in ('selected','grown','cleaned'):
  prefix=stem.replace('/selected/','/'+suffix+'/')+f'locale-allocation-{n["generation"]}'
  equal(capture.data(prefix+'-expected.bin'),want,'Whole4096 literal expected owner carry')
  if suffix!='cleaned':equal(capture.data(prefix+'-owned-page.bin'),want,'Whole4096 actual owned mapping')
  counts['new_family_whole_native_owned_carries']+=1
 for x in (o,n):
  equal(x['final'][x['requested']:],x['initial'][x['requested']:],'Untouched requested-to-capacity backing tail in its own branch')
  counts['new_family_untouched_capacity_tail_bytes']+=x['capacity']-x['requested']
def local_byte(source,field,readpc,writepc):
 accesses=source['source_accesses'];writes=[(i,r)for i,r in enumerate(accesses)if(r[0],r[1],r[3],r[4])==(writepc,field,1,1)];need(len(writes)==1,'One exact declared static byte store');wi,w=writes[0]
 reads=[(i,r)for i,r in enumerate(accesses[:wi])if r[0]==readpc and r[3:]==[1,0]];need(len(reads)==1,'One physical same-register byte read');ri,r=reads[0];equal(r[2],w[2],'Exact read-to-store byte flow')
 prior=[(i,v)for i,v in enumerate(accesses[:ri])if v[4]and v[1]<=r[1]<v[1]+v[3]]
 if prior:
  si,v=prior[-1];equal((v[2]>>(8*(r[1]-v[1])))&255,r[2],'Exact last dominating source store byte')
  origin=dict(kind='last_dominating_literal_store',source_access_index=si,PC=v[0],address=v[1],width=v[3],value=v[2],byte_offset=r[1]-v[1])
 else:origin=dict(kind='own_genuine_carried_BEFORE_byte',address=r[1],value=r[2],no_prior_overlapping_source_store=True,proven_by_independent_literal_source_gate=True)
 return dict(field=field,read_PC=readpc,write_PC=writepc,read_address=r[1],value=w[2],read_index=ri,write_index=wi,origin=origin)
def compare(original,native,capture,stem,pages,contract):
 counts=collections.Counter();root=original['root'];need(root in ROOTS and native['root']==root and original['no_post_source_seed']is True,'Both exact literal source roots without AFTER seed');equal(original['phase'],native['phase'],'Current physical phase')
 o=original_owner(original['owner']);n=native_owner(native['owner']);need(o['requested']==n['requested']==REQUESTS[root]and o['capacity']==n['capacity']==16,'Actual finite formatter role/request/capacity');backing(o,n,capture,stem,counts)
 for branch,owner in ((original,o),(native,n)):
  writes=[r for r in branch['source_accesses']if r[4]and owner['guest']<=r[1]<owner['guest']+owner['capacity']]
  predicted=bytearray(owner['initial']);written=set()
  for pc,address,value,width,writing in writes:
   offset=address-owner['guest'];need(offset+width<=owner['requested'],'Every formatter store stays within actual requested domain');predicted[offset:offset+width]=value.to_bytes(width,'little');written.update(range(offset,offset+width))
  equal(bytes(predicted),owner['final'],'Complete capacity backing is own literal writes plus untouched genuine input')
  owner['written']=written
 equal(o['written'],n['written'],'Exact formatter initialized byte domain');need(set(range(o['requested']))<=o['written'],'The complete finite output including NUL is initialized');equal(o['final'][:o['requested']],n['final'][:n['requested']],'Whole literal output and NUL');counts['paired_new_format_owners']+=1
 boundary_rows=original['original_boundary_joins'];calls=native['calls'];need(len(boundary_rows)==6 and len(calls)==3,'All three original entry/return observations and literal native CALL/RET occurrences');cdecl=[]
 for index,(call,entry,returned)in enumerate(zip(calls,boundary_rows[::2],boundary_rows[1::2])):
  PC,target,argc,returnPC=((0x4dea15,0x780264a9,2,0x4dea1b),(0x4deab1,0x780012b3,1,0x4deab7),(0x4dead1,0x78022b9a,4,0x4dead7))[index]
  need(call['root']==root and call['PC']==PC and call['target']==target and call['returned']and len(call['args'])==argc,'Exact literal cdecl target/site/argc/RET');need(entry['kind']==2*index and returned['kind']==2*index+1 and entry['CPU'][9]==target and returned['CPU'][9]==returnPC,'Genuine original bounded entry and first game return instruction')
  need(entry['CPU'][4]==call['frame']and returned['CPU'][4]==call['returned_ESP']==call['frame']+4,'Complete cdecl source frame and RET consumption')
  args=struct.unpack_from('<'+str(argc)+'I',bytes.fromhex(entry['frame32_hex']),4);native_args=call['args']
  if index==2:need(args[0]==o['guest']and native_args[0]==n['guest'],'sprintf destination is its exact current formatter owner');equal(tuple(args[1:]),tuple(native_args[1:]),'Exact finite format and source string varargs')
  else:equal(tuple(args),tuple(native_args),'Exact source filename/search or malloc requested arguments')
  if index==1:need(returned['CPU'][0]==o['guest']and call['result']==n['guest'],'Literal malloc return is the same exact formatter owner occurrence')
  else:equal(returned['CPU'][0],call['result'],'Literal strrchr/sprintf EAX result')
  equal(entry['FX512_hex'],returned['FX512_hex'],'Original whole floating state conserved by cdecl provider');equal(entry['ENV28_hex'],returned['ENV28_hex'],'Original whole x87 environment conserved by cdecl provider')
  cdecl.append(dict(original_entry=entry,original_first_return_instruction=returned,native_literal_call=call,original_postRET_machine_observed=False,native_CALL_RET_machine_source_derived=True));counts['paired_new_format_cdecl_lifetimes']+=1;counts['paired_new_format_cdecl_boundary_relations']+=2
 equal([r['index']for r in original['dispatches']],[1,7,1,7],'Original literal narrow table sequence');equal([r['index']for r in native['dispatches']],[1,7,1,7],'Native literal narrow table sequence')
 original_owners=[o];native_owners=[n];mixed=[];mixed_FS=[];mixed_API=[];byte_rows=[]
 if root==0x4e1ca0:
  ao=original['mixed_owners'];bn=native['mixed_owners'];need(len(ao)==len(bn)==3,'Three distinct repeated mixed MFC occurrences')
  for role,(a,b,site,request,types)in enumerate(zip(ao,bn,MIXED_SITES,(12,24,24),MIXED_STORE_TYPES)):
   x=original_owner(a);y=native_owner(b);need(a['CALL_pc']==b['allocation_CALL_pc']==site and b['owner_role']==role and x['requested']==y['requested']==request and x['capacity']==y['capacity']==(16 if role==0 else 32),'Finite mixed source occurrence, same-role current owner and capacity');backing(x,y,capture,stem,counts);original_owners.append(x);native_owners.append(y)
   ax=[r for r in a['source_owned_accesses']if r[4]];by=[r for r in b['source_owned_accesses']if r[4]];need(len(ax)==len(by)==len(types),'Complete literal mixed owner store count')
   for left,right,(pc,offset,kind)in zip(ax,by,types):
    need(left[0]==right[0]==pc and left[1]==x['guest']+offset and right[1]==y['guest']+offset and left[3:]==right[3:]==[4,1],'Each literal mixed DWORD exact role/PC/offset/width/order')
    if kind=='self':need(left[2]==x['guest']and right[2]==y['guest'],'Exact same occurrence self link')
    elif kind=='header':need(role==2 and left[2]==original_owners[2]['guest']and right[2]==native_owners[2]['guest'],'Exact role1 header parent link')
    else:equal(left[2],0 if kind=='null'else kind,'Exact original literal scalar/null');equal(right[2],left[2],'Exact native literal scalar/null')
    counts['paired_new_mixed_source_owned_writes']+=1
   for branch,owner,source_writes in ((original,x,ax),(native,y,by)):
    want=bytearray(owner['initial'])
    for pc,address,value,width,writing in source_writes:want[address-owner['guest']:address-owner['guest']+width]=value.to_bytes(width,'little')
    equal(bytes(want),owner['final'],'Whole mixed capacity byteflow from own initial and exact literal stores')
   mixed.append(dict(role=role,CALL_pc=site,original=a,native=b));counts['paired_new_mixed_MFC_owners']+=1
  source_private=native['mixed_private_relations'];need(len(source_private['FS_frames'])==2 and len(source_private['Lockit_calls'])==2,'Both complete native mixed source FS/Lockit invocations')
  observed=original['FS_events'];need(len(observed)==6,'Six individually observed original game FS events')
  for frame in source_private['FS_frames']:
   for side,kind in (('install',1),('restore',2)):
    event=frame[side];matches=[v for v in observed if v['PC']==event['PC']and v['kind']==kind];need(len(matches)==1,'One exact current original game FS source hook');actual=matches[0];raw=struct.unpack('<3I',bytes.fromhex(actual['record_before_hex']));derived=struct.unpack('<3I',bytes.fromhex(event['record_hex']));need(actual['CPU_before'][4]==event['ESP']and raw[1:]==derived[1:],'Actual original/native same affine FS record handler/scope')
    # Host outer predecessors differ by process; inner predecessor is its
    # independently source-established outer record in both branches.
    if event['group_entry']==0x4e2190:equal(raw[0],derived[0],'Inner mixed predecessor is the exact same source outer record address')
    else:need(raw[0]==observed[0]['header'][4]and derived[0]==frame['read']['before_head'],'Outer FS predecessor carries its own genuine source input')
    mixed_FS.append(dict(original=actual,native_source=event,native_whole_frame=frame['observed'],endpoint_scope='whole12B install/restore record before literal instruction'));counts['paired_new_mixed_FS_install_restore12B_relations']+=1
  cp=original['original_CP_joins'];need(len(cp)==6,'Six authentic mixed CP boundaries')
  for index,relation in enumerate(native['Lockit_API_relations']):
   entered,returned=cp[index*3+1:index*3+3];frame=relation['frame'];need(entered['CPU'][4]==frame and returned['CPU'][4]==frame+8 and returned['CPU'][9]==relation['return_pc'],'Actual original API-entry/stdcall return frame against literal native source relation');need(entered['FX512_hex']==returned['FX512_hex']and entered['ENV28_hex']==returned['ENV28_hex'],'Original true API numerical-state conservation')
   a=struct.unpack('<6I',bytes.fromhex(entered['CS24_hex']));b=struct.unpack('<6I',bytes.fromhex(returned['CS24_hex']));d=relation['depth'];need(a[0]==b[0]and a[4:]==b[4:]and b[1:4]==((0xfffffffe,1,entered['header'][6])if d else(0xffffffff,0,0)),'Actual original whole CS24 opaque identity and measured ownership depth')
   mixed_API.append(dict(original_actual_entry=entered,original_actual_source_return=returned,native_literal_API=relation,original_postRET_observed=False));counts['paired_new_mixed_bounded_API_relations']+=1
  for field,rpc,wpc in BYTE_FIELDS:
   a=local_byte(original,field,rpc,wpc);b=local_byte(native,field,rpc,wpc);claimed=next(v for v in native['byte_provenance']if v['field']==field);need(claimed['read_PC']==rpc and claimed['write_PC']==wpc and claimed['value']==b['value']and claimed['read_address']==b['read_address'],'Current source-native exact saved-byte attribution')
   byte_rows.append(dict(original=a,native=b));counts['paired_new_mixed_saved_byte_source_derivations']+=2
  zero=native['literal_zero_byte'];need(zero==dict(field=0x60b768,write_PC=0x4e5309,value=0,definition_PC=0x4e52cc),'Literal XOR EBX supplies +256 byte, no indeterminate projection')
 fields={};byte_by_field={r['original']['field']:r for r in byte_rows}
 def static(branch,owners):return[r for r in branch['source_accesses']if r[4]and r[1]&~4095 in pages and r[1]&~4095!=0x20001000 and not any(o['guest']<=r[1]<o['guest']+o['capacity']for o in owners)]
 aw=static(original,original_owners);bw=static(native,native_owners);equal([(r[0],r[1],r[3])for r in aw],[(r[0],r[1],r[3])for r in bw],'Complete game page literal static store order')
 pointer_fields={FORMAT_FIELDS[root]:(o['guest'],n['guest'],0x4deabc)}
 if root==0x4e1ca0:
  for role,(pc,address)in enumerate(MIXED_PUBS):pointer_fields[address]=(original_owners[role+1]['guest'],native_owners[role+1]['guest'],pc)
 for left,right in zip(aw,bw):
  pc,address,value,width,writing=left
  if address in pointer_fields and pc==pointer_fields[address][2]:
   av,bv,_=pointer_fields[address];need(width==4 and value==av and right[2]==bv,'Exact typed literal current owner publication');counts['paired_new_format_publications'if address==FORMAT_FIELDS[root]else'paired_new_mixed_publications']+=1
  elif address in byte_by_field:
   item=byte_by_field[address];need(width==1 and value==item['original']['value']and right[2]==item['native']['value'],'Exact own-branch literal saved byte store')
  else:equal(value,right[2],'Every remaining literal game scalar/borrowed-static value is exact')
  for offset in range(width):fields[address+offset]=((value>>(8*offset))&255,(right[2]>>(8*offset))&255,pc)
 need(FORMAT_FIELDS[root]in pointer_fields and counts['paired_new_format_publications']==1,'One exact formatter publication')
 row=dict(root=root,sequence=native['sequence'],level=native['level'],phase=native['phase'],formatter_original=original['owner'],formatter_native=native['owner'],cdecl=cdecl,mixed_owners=mixed,mixed_FS=mixed_FS,mixed_API=mixed_API,byte_provenance=byte_rows,static_fields={str(a):list(v)for a,v in fields.items()},counts=dict(counts))
 return fields,dict(counts),row
def carry(fields,phase,side,page,original,native,declared,counts):
 for address,(activation,a,b,PC)in fields.items():
  if address&~4095!=page or phase<activation or phase==activation and side=='before':continue
  off=address&4095;need(original[off]==a and native[off]==b,'Every exact source-established new family byte carries without wildcard');declared.add(off);counts['new_family_static_byte_endpoint_carries']+=1
