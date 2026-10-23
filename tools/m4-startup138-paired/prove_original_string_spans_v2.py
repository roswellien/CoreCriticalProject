"""Current own-BEFORE literal string argument and complete owned byteflow joins.
The positive malloc boundary admits its actual allocation scalar and genuine
API-initial backing; no CPU equivalence of the skipped malloc body is claimed.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
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
 D=module('ordinary',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');G=module('literal_string_own_before',R/'tools/m4-next-source/game_model.py');O=module('own_original_state',R/'tools/m4-mfc-source/compare_original_game.py');J=module('architectural_seed',R/'tools/m4-joint-startup27-review/observe.py');m,_,_,_=J.models();PE=module('physical',R/'tools/analysis/pe.py');game=PE.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());crt=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes());program,callbacks=G.source_program()
 gp=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');g=json.loads(gp.read_bytes());assert g['passed']and g['reader_closed'];prep=json.loads(pin(R/'reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161').read_bytes());PAGES=prep['observed_pages'];m.PAGES=list(PAGES)
 roots=json.loads(pin(R/'reports/m4-strings-source/recovery-r7/string-roots.json').read_bytes());add=json.loads(pin(R/'reports/m4-container-source/allocation-interface-r1/string-inputs.json','b355761251799f245daf8a74dbef07ae008863deb1e2f88c4723af13090ab9f6').read_bytes());bindings={r['entry']:r['string']for r in roots};bindings.update({r['root']:r for r in add});positive={k:v for k,v in bindings.items()if v['actual_strdup_called']};assert len(positive)==19
 lp=pin(R/'reports/m4-startup138-paired/CRT-lock13-domain-r2/report.json','6bf6c226e40dea50912fb126eaaa97715af4aadd436189114ec292f599a161eb');lg=json.loads(lp.read_bytes());domains=json.loads(pin(lg['domains_path'],lg['domains_sha256']).read_bytes());unused={s:set().union(*(set(r['unused_input_offsets'])for r in domains if r['sequence']==s))for s in range(6)}
 e=next(r for r in g['paired_exports']if r['branch']=='original');idx=pin(e['index_path'],e['index_sha256']);payload=pin(e['payload_path'],e['payload_sha256']);entries=D.entries(idx,re.compile(r'phase/[0-5]/(?:\d+\.bin|\d+/(?:api-ledger.bin|fs-events.bin|strings/\d+/(?:meta|bytes).bin|api-initial/\d+/(?:size|bytes).bin))'));rows=[];read_operands=0;write_operands=0
 def disjoint(seq,address,size):
  assert 0<=address and 0<=size and address+size<=0x100000000;assert not{a-0x78037000 for a in range(max(address,0x78037000),min(address+size,0x78038000))}&unused[seq]
 def physical(model):
  for pc in model.PCs:
   r=program[pc];image=crt if pc>=0x78000000 else game;off,_=image.rva_range(pc-image.image_base,r['width']);assert image.data[off:off+r['width']]==bytes.fromhex(r['bytes_hex'])
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
    model.run(stop=lambda x:x.cursor==binding['return_pc'],api=lambda x,t:(_ for _ in()).throw(ValueError(('Unexpected string suffix API',hex(t)))))
    assert model.reg('eax')==actual[3]and model.reg('esp')==frame+4;predicted=model.bytes(actual[3],capacity);assert predicted[:request]==bytes.fromhex(binding['bytes_hex'])and predicted==data(stem+f'strings/{entry}/bytes.bin',capacity)
    after=raw[178404:178404+43*4096];field=actual[2];page=field&~4095;assert page in PAGES and struct.unpack_from('<I',after,PAGES.index(page)*4096+(field&4095))[0]==actual[3]
    physical(model)
    for pc,address,value,width,write in model.accesses:disjoint(seq,address,width);read_operands+=not write;write_operands+=bool(write)
    rows.append(dict(sequence=seq,phase=phase,root=entry,source_CALL_PC=binding['CALL_pc'],source_strdup_entry_frame=frame,source_strdup_return_PC=args[0],source_argument=args[1],whole_source_read_extent=len(source_input),source_NUL_bytes_hex=binding['bytes_hex'],literal_strlen_request=request,malloc_source_frame=malloc_frame,actual_HeapAlloc_index=index,actual_HeapAlloc_CPU_before=list(v[:10]),actual_HeapAlloc_CPU_after=list(v[10:20]),schema_absent_API_PC_exact_zero=True,actual_return_pointer=actual[3],actual_initial_capacity=capacity,API_initial_sha256=hashlib.sha256(initial).hexdigest(),source_owned_final_sha256=hashlib.sha256(predicted).hexdigest(),source_PCs=model.PCs,source_accesses=model.accesses,AFTER_state_or_bytes_used_as_source_input=False,full_malloc_CPU_equivalence_claimed=False))
 assert len(rows)==114 and sha(idx)==e['index_sha256']and sha(payload)==e['payload_sha256']
 for path,h in g['files'].items():
  if path.lower().endswith('.py')and Path(path).is_file():pin(path,h)
 rp=out/'relations.json';rp.write_text(json.dumps(rows,indent=2)+'\n');pin(rp);pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='All114 current literal19 strdup roots derive actual CALL arguments/strlen source read spans from own BEFORE, bind true HeapAlloc result and API-initial fullcapacity, execute literal strdup/strcpy suffix, predict entire returned backing and publication alias; only unused-data consumption proof, no fullmalloc/providerCPU claim',actual_string_argument_return_span_relations=len(rows),source_read_operands=read_operands,source_write_operands=write_operands,full_actual_API_initial_and_owned_return_capacities=True,source_machine_executed=True,source_scope='Bounded literal own-BEFORE string prefix and suffix with typed positive malloc scalar/initial backing seam',provider_full_CPU_executed=False,AFTER_state_or_bytes_used_as_source_input=False,complete_paired_policy_admitted=False,archive_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
