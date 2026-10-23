"""Current own-BEFORE literal string argument and complete owned byteflow joins.
The positive malloc boundary admits its actual allocation scalar and genuine
API-initial backing; no CPU equivalence of the skipped malloc body is claimed.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def module(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 authority=set();saved_read_bytes=Path.read_bytes;saved_read_text=Path.read_text;saved_spec=importlib.util.module_from_spec
 def track(p):
  p=Path(p).resolve()
  if p.is_relative_to(R):assert p.name!='transport.json'and p.suffix.lower()not in('.mwb','.mwi','.zip');authority.add(p)
 def read_bytes(p,*a,**kw):track(p);return saved_read_bytes(p,*a,**kw)
 def read_text(p,*a,**kw):track(p);return saved_read_text(p,*a,**kw)
 def create_module(spec):
  if spec.origin and spec.origin.endswith('.py'):track(spec.origin)
  return saved_spec(spec)
 Path.read_bytes=read_bytes;Path.read_text=read_text;importlib.util.module_from_spec=create_module
 D=module('ordinary',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');G=module('literal_string_own_before',R/'tools/m4-next-source/game_model.py');O=module('own_original_state',R/'tools/m4-mfc-source/compare_original_game.py');J=module('architectural_seed',R/'tools/m4-joint-startup27-review/observe.py');m,_,_,_=J.models();PE=module('physical',R/'tools/analysis/pe.py');game=PE.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());crt=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes());program,callbacks=G.source_program();string_contract=json.loads(pin(R/'reports/m4-strings-review/interface-r2/instruction-contracts.json').read_bytes());string_PCs={v['pc']for v in string_contract['instructions']};assert len(string_PCs)==117
 gp=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');g=json.loads(gp.read_bytes());assert g['passed']and g['reader_closed'];prep=json.loads(pin(R/'reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161').read_bytes());PAGES=prep['observed_pages'];m.PAGES=list(PAGES)
 roots=json.loads(pin(R/'reports/m4-strings-source/recovery-r7/string-roots.json').read_bytes());add=json.loads(pin(R/'reports/m4-container-source/allocation-interface-r1/string-inputs.json','b355761251799f245daf8a74dbef07ae008863deb1e2f88c4723af13090ab9f6').read_bytes());bindings={r['entry']:r['string']for r in roots};bindings.update({r['root']:r for r in add});positive={k:v for k,v in bindings.items()if v['actual_strdup_called']};assert len(positive)==19
 lp=pin(R/'reports/m4-startup138-paired/CRT-lock13-domain-r2/report.json','6bf6c226e40dea50912fb126eaaa97715af4aadd436189114ec292f599a161eb');lg=json.loads(lp.read_bytes());domains=json.loads(pin(lg['domains_path'],lg['domains_sha256']).read_bytes());unused={s:set().union(*(set(r['unused_input_offsets'])for r in domains if r['sequence']==s))for s in range(6)}
 e=next(r for r in g['paired_exports']if r['branch']=='original');idx=pin(e['index_path'],e['index_sha256']);payload=pin(e['payload_path'],e['payload_sha256']);entries=D.entries(idx,re.compile(r'phase/[0-5]/(?:\d+\.bin|\d+/(?:api-ledger.bin|fs-events.bin|widget-fs-events.bin|strings/\d+/(?:meta|bytes).bin|api-initial/\d+/(?:size|bytes).bin))'));rows=[];read_operands=0;write_operands=0
 def disjoint(seq,address,size):
  assert 0<=address and 0<=size and address+size<=0x100000000;assert not{a-0x78037000 for a in range(max(address,0x78037000),min(address+size,0x78038000))}&unused[seq]
 def physical(model):
  for pc in model.PCs:
   r=program[pc];image=crt if pc>=0x78000000 else game;off,_=image.rva_range(pc-image.image_base,r['width']);assert image.data[off:off+r['width']]==bytes.fromhex(r['bytes_hex'])
 Path.read_bytes=saved_read_bytes;Path.read_text=saved_read_text;importlib.util.module_from_spec=saved_spec
 for p in sorted(authority):pin(p)
 source_authority_files={str(p):pins[str(p)]for p in sorted(authority)}
 controls=[];volatile_suffix_controls=[]
 with payload.open('rb')as f:
  def data(k,n=None):
   z=entries[k];assert n is None or z['bytes']==n;f.seek(z['offset']);b=f.read(z['bytes']);assert len(b)==z['bytes']and hashlib.sha256(b).hexdigest()==z['sha256'];return b
  for seq in range(6):
   for phase,item in enumerate(prep['selected_order']):
    entry=item['entry']
    if entry not in positive:continue
    binding=positive[entry];stem=f'phase/{seq}/{phase}/';raw=data(f'phase/{seq}/{phase}.bin',356992);memory={p:bytearray(raw[2276+4096*i:2276+4096*(i+1)])for i,p in enumerate(PAGES)};assert struct.unpack_from('<I',memory[0x5bb000],0x670)[0]==0x78010a6d;struct.pack_into('<I',memory[0x5bb000],0x670,0x1df886)
    fs=data(stem+'fs-events.bin');head=struct.unpack_from('<I',fs,16)[0]if fs else None
    if fs:assert len(fs)%1216==0 and struct.unpack_from('<4I',fs)[:2]==(1,entry)and struct.unpack_from('<I',fs,12)[0]==0;memory[0x7ffde000]=bytearray(struct.pack('<I',head))
    raw_strdup_target=0x78010a6d;raw_off,_=game.rva_range(0x5bb670-game.image_base,4);assert struct.unpack_from('<I',game.data,raw_off)[0]==0x1df886
    cpu=struct.unpack_from('<10I',raw,36);state=O.original_state(m,G,cpu,raw);model=G.Machine(state,raw[116:628],raw[36:76],memory,program=program,callbacks=callbacks);model.call_stack.append((entry,cpu[4],0x410a80,0,model.reg('ebp'),model.reg('ebx'),model.reg('esi'),model.reg('edi'),0))
    model.run(stop=lambda x:x.cursor==0x78010a6d,api=lambda x,t:(_ for _ in()).throw(ValueError(('Unexpected prefix API',hex(t)))))
    frame=model.reg('esp');args=struct.unpack('<2I',model.bytes(frame,8));assert args==(binding['return_pc'],binding['source'])and model.PCs[-1]==binding['CALL_pc'];source_input=model.bytes(binding['source'],binding['physical_read_end']-binding['source']);assert source_input==bytes.fromhex(binding['physical_bytes_hex']);disjoint(seq,binding['source'],len(source_input));disjoint(seq,frame,8)
    model.run(stop=lambda x:x.cursor==0x780012b3,api=lambda x,t:(_ for _ in()).throw(ValueError(('Unexpected string API',hex(t)))))
    malloc_frame=model.reg('esp');malloc_ret,request=struct.unpack('<2I',model.bytes(malloc_frame,8));assert malloc_ret==0x78010a83 and request==binding['size'];actual=struct.unpack('<6I',data(stem+f'strings/{entry}/meta.bin',24));assert actual[:2]==(entry,binding['source'])and actual[4]==request and 0<request<=actual[5]<=512
    ledger=list(struct.iter_unpack('<26I',data(stem+'api-ledger.bin')));matches=[(i,v)for i,v in enumerate(ledger)if v[24]==0 and v[10]==actual[3]];assert len(matches)==1;index,v=matches[0];assert v[22]==(request+15)&~15 and v[25]==0x78001385 and v[9]==v[19]==0;capacity=struct.unpack('<I',data(stem+f'api-initial/{index}/size.bin',4))[0];initial=data(stem+f'api-initial/{index}/bytes.bin',capacity);assert capacity==actual[5]and len(initial)==capacity;disjoint(seq,actual[3],capacity)
    # Source-only cdecl boundary from the exact independently derived frame:
    # malloc is separately accepted; only its genuine positive scalar result
    # and full API-before-write initial backing enter the literal string suffix.
    assert actual[3]not in model.memory;model.memory[actual[3]]=bytearray(initial);model.reg('eax',actual[3]);model.reg('esp',malloc_frame+4);model.cursor=malloc_ret;model.word(2472,malloc_ret);call=model.call_stack.pop();assert call[0]==0x780012b3 and call[1]==malloc_frame and call[2]==malloc_ret
    suffix_cut=copy.deepcopy(model,memo={id(model.program):model.program,id(model.callbacks):model.callbacks});suffix_start=len(model.accesses)
    model.run(stop=lambda x:x.cursor==binding['return_pc'],api=lambda x,t:(_ for _ in()).throw(ValueError(('Unexpected string suffix API',hex(t)))))
    assert model.reg('eax')==actual[3]and model.reg('esp')==frame+4;predicted=model.bytes(actual[3],capacity);assert predicted[:request]==bytes.fromhex(binding['bytes_hex'])and predicted==data(stem+f'strings/{entry}/bytes.bin',capacity)
    for variant,(ecx,edx,flags)in enumerate([(0xdeadbeef,0xa5a5a5a5,0),(0x13579bdf,0x2468ace0,1)]):
     mutant=copy.deepcopy(suffix_cut,memo={id(model.program):model.program,id(model.callbacks):model.callbacks});mutant.reg('ecx',ecx);mutant.reg('edx',edx)
     for flag in G.I.FLAGS:mutant.flag(flag,flags)
     mutant.run(stop=lambda x:x.cursor==binding['return_pc'],api=lambda x,t:(_ for _ in()).throw(ValueError(('Unexpected mutant suffix API',hex(t)))))
     assert mutant.bytes(actual[3],capacity)==predicted and mutant.reg('eax')==actual[3]and mutant.reg('esp')==frame+4 and mutant.accesses[suffix_start:]==model.accesses[suffix_start:]
     assert all(mutant.reg(reg)==model.reg(reg)for reg in('ebx','ebp','esi','edi'));volatile_suffix_controls.append(dict(sequence=seq,phase=phase,variant=variant,ECX=ecx,EDX=edx,all_FLAGS=flags,whole_owned_bytes_and_memory_operands_unchanged=True,full_CPU_equivalence_claimed=False))
    overwritten={};flags_written=None
    for pc in model.PCs[len(suffix_cut.PCs):]:
     instruction=program[pc];op=instruction['mnemonic'];args0=instruction['decoded_operands'];read=[];written=[]
     for pos,arg in enumerate(args0):
      if arg['kind']=='memory':read.extend(t['register']for t in arg['terms'])
      elif arg['kind']=='register':
       reg=G.I.alias(arg['register'])[0]
       if pos==0 and op in('mov','lea','pop'):written.append(reg)
       elif pos==0 and op in('add','sub','xor','and','or','inc','dec'):
        read.append(reg);written.append(reg)
       else:read.append(reg)
     for reg in read:
      reg=G.I.alias(reg)[0]
      if reg in('ecx','edx'):assert reg in overwritten,('Old malloc volatile consumed',hex(pc),reg)
     if op.startswith('j')and op!='jmp':assert flags_written is not None,('Old malloc flags consumed',hex(pc))
     for reg in written:overwritten.setdefault(reg,pc)
     if op in('test','cmp','add','sub','xor','and','or','inc','dec'):flags_written=flags_written or pc
    assert overwritten['ecx']==0x78010a83 and flags_written==0x78010a84 and overwritten['edx']==0x78002fc0
    assert all(v[k]==v[k+10]for k in(3,5,6,7))and v[14]==v[4]+16
    after=raw[178404:178404+43*4096];field=binding['object_addresses'][0]+4;assert actual[2]==field;page=field&~4095;assert page in PAGES and struct.unpack_from('<I',after,PAGES.index(page)*4096+(field&4095))[0]==actual[3]
    publication=None
    for _ in range(3):
     old_accesses=len(model.accesses);model.step()
     stores=[v for v in model.accesses[old_accesses:]if v[4]and v[1]==field]
     if stores:
      assert len(stores)==1 and stores[0][2:]==(actual[3],4,1);publication=dict(PC=stores[0][0],address=field,width=4,value=actual[3],source_field_from_bound_instance=True);break
    assert publication is not None and model.bytes(field,4)==struct.pack('<I',actual[3])
    physical(model);body_roles=[]
    for pc,address,value,width,write in model.accesses:
     disjoint(seq,address,width);read_operands+=not write;write_operands+=bool(write)
     if pc in string_PCs:
      if 0x20001000<=address and address+width<=0x20002000:role='own_literal_call_frame'
      elif actual[3]<=address and address+width<=actual[3]+capacity:role='same_actual_API_initial_owned_destination'
      elif binding['source']-binding['alignment_prefix']<=address and address+width<=binding['physical_read_end']:assert not write;role='exact_own_NUL_source_extent'
      else:raise AssertionError(('Unbound string register-pointer operand',seq,phase,hex(pc),hex(address),width,write))
      body_roles.append(dict(PC=pc,address=address,width=width,write=bool(write),role=role))
    def joined(raw_target,call_pc,source,extent,returned,initial_capacity,first_PC=None,first_value=None,prior_value=None):
     assert raw_target==0x78010a6d and call_pc==binding['CALL_pc']and source==args[1]==binding['source']and extent==len(source_input)and returned==v[10]==actual[3]and initial_capacity==capacity==actual[5]
     if fs:assert first_PC==struct.unpack_from('<I',fs,8)[0]and first_value==head and prior_value==head
    fs_cut=None
    if fs:
     accesses=[(i,v)for i,v in enumerate(model.accesses)if v[1]==0x7ffde000];assert accesses and not accesses[0][1][4]and accesses[0][1][2]==head;first_pc=accesses[0][1][0];assert struct.unpack_from('<I',fs,8)[0]==first_pc
     # All literal prefix steps precede any opaque API (the runner denies any
     # unresolved target). No guest FS store or head-installer precedes this
     # exact source first read. Thus its observed input is a causal entry scalar,
     # not a future source/API output or an AFTER machine seed.
     assert all(a!=0x7ffde000 or not w for p,a,v,n,w in model.accesses[:accesses[0][0]])
     for ordinal,(access_index,(pc,address,value,width,write))in enumerate(accesses):
      event=fs[ordinal*1216:(ordinal+1)*1216];version,root,eventpc,kind,bh,ah=struct.unpack_from('<6I',event);assert version==1 and root==entry and eventpc==pc and width==4 and write==(kind!=0)and value==(ah if write else bh)
     prior=None
     for pp in reversed(range(phase)):
      for leaf,size in [('fs-events.bin',1216),('widget-fs-events.bin',1224)]:
       events=data(f'phase/{seq}/{pp}/'+leaf)
       if events:
        assert len(events)%size==0;ev=struct.unpack_from('<6I',events,len(events)-size);assert ev[0]==1
        prior=dict(sequence=seq,phase=pp,root=ev[1],last_source_PC=ev[2],terminal_FS_head=ev[5],ordinary_leaf=leaf);break
      if prior:break
     assert prior is not None and prior['terminal_FS_head']==head
     fs_cut=dict(root_entry_direct_TIB_snapshot_available=False,opaque_initial_FS0=head,first_source_read_PC=first_pc,first_source_read_kind=0,no_preceding_literal_source_FS_store=True,no_preceding_opaque_API_or_unresolved_prefix_target=True,prior_observed_terminal_scalar=prior,prior_observation_same_head=True,current_source_FS_events_joined=len(accesses),claim='Finite causal first-source-read input cut; entry scalar inferred from literal prefix order and prior observed terminal equality, not whole unobserved TIB or API transient equivalence')
    good=[raw_strdup_target,binding['CALL_pc'],args[1],len(source_input),actual[3],capacity]
    good+=[first_pc,head,prior['terminal_FS_head']]if fs else[None,None,None];joined(*good)
    for field in range(9 if fs else 6):
     bad=good[:];bad[field]^=1
     try:joined(*bad)
     except AssertionError:controls.append(dict(sequence=seq,phase=phase,name=['wrong-own-raw-strdup-target','wrong-source-CALL-PC','wrong-source-argument','wrong-source-span','wrong-actual-return-pointer','wrong-API-initial-capacity','wrong-FS-first-PC','wrong-FS-first-value','wrong-prior-FS-terminal'][field],refused=True))
     else:raise AssertionError(('Accepted bad string join',field))
    bad_address=binding['physical_read_end']+1
    assert not(0x20001000<=bad_address<0x20002000)and not(actual[3]<=bad_address<actual[3]+capacity)
    try:assert binding['source']-binding['alignment_prefix']<=bad_address and bad_address+1<=binding['physical_read_end']
    except AssertionError:controls.append(dict(sequence=seq,phase=phase,name='unaligned-byte-outside117-source-bounds',address=bad_address,refused=True))
    else:raise AssertionError('Accepted outside117byte')
    projection=dict(slot=0x5bb670,actual_original_installed_entry=raw_strdup_target,physical_raw_import=0x1df886,logical_handler_return_entry=0x78010a6d,physical_named_IMPORT='_strdup',source_CALL_PC=binding['CALL_pc'],own_source_derived_frame=frame,exact_argument=args[1],pointer_field_normalization_only=True,caller_argument_effects=False,scope='Retained accepted literal model raw-IAT handler projection for same physical original source function; actual installed target authenticated before exactly4B normalization')
    rows.append(dict(sequence=seq,phase=phase,root=entry,source_CALL_PC=binding['CALL_pc'],source_strdup_entry_frame=frame,source_strdup_return_PC=args[0],source_argument=args[1],whole_source_read_extent=len(source_input),source_NUL_bytes_hex=binding['bytes_hex'],literal_strlen_request=request,malloc_source_frame=malloc_frame,actual_HeapAlloc_index=index,actual_HeapAlloc_CPU_before=list(v[:10]),actual_HeapAlloc_CPU_after=list(v[10:20]),schema_absent_API_PC_exact_zero=True,actual_return_pointer=actual[3],literal_source_publication=publication,actual_initial_capacity=capacity,API_initial_sha256=hashlib.sha256(initial).hexdigest(),source_owned_final_sha256=hashlib.sha256(predicted).hexdigest(),source_PCs=model.PCs,source_accesses=model.accesses,all117_body_indirect_operand_roles=body_roles,exact_strdup_IAT_projection=projection,suffix_volatile_first_overwrite_PCs={k:v for k,v in overwritten.items()if k in("ecx","edx")},suffix_flags_first_overwrite_PC=flags_written,suffix_prior_malloc_ECX_EDX_FLAGS_read_before_overwrite=False,current_FS0_input_cut=fs_cut,AFTER_state_or_bytes_used_as_source_input=False,full_malloc_CPU_equivalence_claimed=False))
 assert len(rows)==114 and sha(idx)==e['index_sha256']and sha(payload)==e['payload_sha256']
 for path,h in g['files'].items():
  if path.lower().endswith('.py')and Path(path).is_file():pin(path,h)
 rp=out/'relations.json';rp.write_text(json.dumps(rows,indent=2)+'\n');pin(rp);pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='All114 current literal19 strdup roots derive actual CALL arguments/strlen source read spans from own BEFORE, bind true HeapAlloc result and API-initial fullcapacity, execute literal strdup/strcpy suffix, predict entire returned backing and publication alias; only unused-data consumption proof, no fullmalloc/providerCPU claim',actual_string_argument_return_span_relations=len(rows),source_read_operands=read_operands,source_write_operands=write_operands,full_actual_API_initial_and_owned_return_capacities=True,source_authority_read_files=source_authority_files,recursive_actual_module_and_program_spec_reads_pinned=True,exact_named_strdup_IAT_pointer_projection=True,volatile_suffix_independence_controls=volatile_suffix_controls,negative_join_and_operand_controls=controls,nonvolatile_actual_HeapAlloc_stdcall_ABI_checked=True,source_machine_executed=True,source_scope='Bounded literal own-BEFORE string prefix and suffix with typed positive malloc scalar/initial backing seam',provider_full_CPU_executed=False,all_executed117_string_indirect_operands_bounded_to_exact_own_source_frame_or_source_extent_or_owned_destination=True,root_entry_direct_TIB_snapshot_claim=False,FS0_scope="Causal actual first-source-read scalar after own BEFORE; no preceding source store or opaque API, joins prior observed terminal equality and every encountered actualFS event",AFTER_state_or_bytes_used_as_source_input=False,complete_paired_policy_admitted=False,archive_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
