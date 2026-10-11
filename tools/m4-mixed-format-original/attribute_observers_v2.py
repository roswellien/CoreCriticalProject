"""Exact compiled/link attribution for both genuine formatting original workers."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-mixed-format-original'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh exact formatting observer attribution');out.mkdir(parents=True);pins={};counts=collections.Counter();rows=[];passed=False;reader=None
 def pin(p,h=None):
  p=Path(p).resolve();v=pins.get(str(p))or sha(p);need(h is None or h==v,'Physical observer identity '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
 def module(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  P=module(ROOT/'tools/analysis/pe.py','format_attrib_PE');C=module(ROOT/'tools/m4-fs-source/observer_attribution.py','format_attrib_COFF');L=module(ROOT/'tools/m4-lockit-review/full_original_review.py','format_attrib_reused_pattern');D=module(ROOT/'tools/m4-crt-allocation-root/run_v2.py','format_attrib_direct')
  game=P.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  def physical(pe,a,n):return pe.read(pe.rva_range(a-pe.image_base,n)[0],n)
  funcs=[('strrchr',0,0x780264a9,0x4dea1b,bytes.fromhex('83c4083bc3'),0x5bb5a8),('malloc',1,0x780012b3,0x4deab7,bytes.fromhex('83c4043bc3'),0x5bb664),('sprintf',2,0x78022b9a,0x4dead7,bytes.fromhex('83c4108b442420'),0x5bb658)]
  def expected_format(pc,kind,replay,index,after):
   b,rel=L.expected_lockit(pc,kind,replay,'_format_continues'if after else None,None if after else'_format_targets');b=bytearray(b);rel=[(o,n.replace('_lockit_','_format_'),t)for o,n,t in rel];flags=[o for o,n,t in rel if n=='_format_cpu'and struct.unpack_from('<I',b,o)[0]==32];need(len(flags)==2,'Reviewed full flag save/restore pair');pos=flags[0]+4;b[pos:pos]=b'\xfc';rel=[(o+(o>=pos),n,t)for o,n,t in rel]
   tail=rel[-1];need(tail[1]==('_format_continues'if after else'_format_targets'),'Only typed full source continuation/provider tail slot');struct.pack_into('<I',b,tail[0],index*4);return bytes(b),rel
  template={};gate_paths=[('prefix-validation-r1','a909c998cd40be724397c38adf63d89ec1d0246c282da3f8bfe28d4689af772b'),('trace-prefix-validation-r1','bfebfd1929e0a023e11857855286d354927f6f343bfc495db1b036397480b4b6')]
  for gate_name,gate_sha in gate_paths:
   gate=read(BASE/gate_name/'report.json',gate_sha);execution=read(gate['execution_path'],gate['execution_sha256']);build=read(execution['build_path'],execution['build_sha256']);prep=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);need(all(x['passed']for x in(gate,execution,build,prep)),'Actual original positive gates')
   for p,h in prep['files'].items():pin(p,h)
   for p,h in read(Path(execution['build_path']).parent/'pins.json')['files'].items():pin(p,h)
   release=Path(execution['build_path']).parent/'build-x86/mw34_joint_startup124_original.dir/Release';symbols,sections=C.parse_coff(pin(release/'format_observer_x86.obj').read_bytes());defs={s['name']:s for s in symbols.values()if s['section']>0 and s['storage']==2};need(len([n for n in defs if n.startswith('_format_')])==6,'All six compiled formatting wrappers');links=list(release.rglob('link.command.1.tlog'));need(len(links)==1 and 'FORMAT_OBSERVER_X86.OBJ'in pin(links[0]).read_text(encoding='utf-16').upper(),'Actual observer included in final link')
   workerbytes=pin(build['worker'],build['worker_sha256']).read_bytes();worker=P.PEImage(workerbytes);need(worker.machine==0x14c and worker.image_base==0x18000000,'Genuine actual fixed-base i386 observer worker');shared={}
   reader=D.DirectSet(execution['original_capture'],pin);data=reader.data('phase/0/0.bin');pages=prep['observed_pages'];iat_offset=2276+pages.index(0x5bb000)*4096
   def executable(a):return any(s['executable']and worker.image_base+s['virtual_address']<=a<worker.image_base+s['virtual_address']+s['raw_size']for s in worker.sections)
   for name,index,entry,ret,replay,iat in funcs:
    need(physical(game,ret,len(replay))==replay,'Exact physical caller-return replay span')
    key=struct.pack('<2I',ret,len(replay));matches=[];start=0
    while True:
     p=workerbytes.find(key,start)
     if p<0:break
     if workerbytes[p+12:p+12+len(replay)]==replay:matches.append(p)
     start=p+1
    need(len(matches)==1,'Unique final compiled FormatHook source/target initializer');return_target=struct.unpack_from('<I',workerbytes,matches[0]+8)[0];entry_target=struct.unpack_from('<I',data,iat_offset+(iat&4095))[0]
    for after,target in[(0,entry_target),(1,return_target)]:
     symbol='_format_'+('return_'if after else'entry_')+name;b,rel=expected_format(ret if after else entry,index*2+after,replay if after else b'',index,after);definition=defs[symbol];sec=sections[definition['section']];actual=sec['bytes'][definition['value']:definition['value']+len(b)];actual_rel=[(o-definition['value'],n,t)for o,n,t in sec['relocations']if definition['value']<=o<definition['value']+len(b)];need(actual==b and actual_rel==rel,'Entire actual compiled wrapper bytes and exact typed relocations')
     if symbol in template:need(template[symbol]==(b,rel),'Normal and debugger worker wrapper code/relocations identical')
     else:template[symbol]=(b,rel)
     need(executable(target),'Actual linked source target belongs to current worker executable code');linked=physical(worker,target,len(b));normalized=bytearray(linked)
     for offset,sym,typ in rel:
      addend=struct.unpack_from('<I',b,offset)[0];value=struct.unpack_from('<I',linked,offset)[0];address=(value-addend)&0xffffffff if typ==6 else(target+offset+4+value-addend)&0xffffffff;need(typ in(6,0x14),'Only typed i386 DIR32/REL32 fields');need(sym not in shared or shared[sym]==address,'Stable actual shared compiled symbol '+sym);shared[sym]=address;normalized[offset:offset+4]=b[offset:offset+4]
     need(bytes(normalized)==b,'Every actual linked executable wrapper byte modulo exact relocation fields');counts['compiled_linked_functions']+=1;counts['compiled_linked_bytes']+=len(b);counts['compiled_linked_relocations']+=len(rel);rows.append(dict(gate=gate_name,symbol=symbol,kind=index*2+after,source_PC=ret if after else entry,actual_worker_target=target,target_source='Actual source owning IAT in whole game BEFORE page'if not after else'Unique physical final FormatHook initializer consumed by checked source patch installer',bytes=len(b),relocations=len(rel),replay_hex=replay.hex()if after else'',tail_field_index=index,source_return_before_caller_cleanup=bool(after)))
   need(physical(worker,shared['_format_continues'],12)==struct.pack('<3I',0x4dea20,0x4deabc,0x4deade),'All actual physical caller continuation DWORDs');need(tuple(struct.unpack('<3I',reader.data('formatting/import-targets.bin')))==(0x780264a9,0x780012b3,0x78022b9a),'Actual initialized named source provider targets');need(any(s['writable']and worker.image_base+s['virtual_address']<=shared['_format_targets']<worker.image_base+s['virtual_address']+s['virtual_size']for s in worker.sections),'Actual source target array is owned worker mutable BSS, runtime values separately observed')
   # No source CPU/memory expectations enter this compiled-byte verification.
   def check_compiled_linked(sym,expected,rel,defs_,sections_,target,family):
    d=defs_[sym];sec=sections_[d['section']];need(sec['bytes'][d['value']:d['value']+len(expected)]==expected,'Every compiled '+family+' instruction byte')
    actual_rel=[(o-d['value'],n,t)for o,n,t in sec['relocations']if d['value']<=o<d['value']+len(expected)];need(actual_rel==rel,'Every compiled '+family+' relocation field')
    need(executable(target),'Actual final initializer/observed target belongs to worker executable code');linked=physical(worker,target,len(expected));normalized=bytearray(linked)
    for offset,symbol,typ in rel:
     addend=struct.unpack_from('<I',expected,offset)[0];value=struct.unpack_from('<I',linked,offset)[0];need(typ in(6,0x14),'Typed i386 relocation only');address=(value-addend)&0xffffffff if typ==6 else(target+offset+4+value-addend)&0xffffffff;need(symbol not in shared or shared[symbol]==address,'Actual linked shared symbol identity');shared[symbol]=address;normalized[offset:offset+4]=expected[offset:offset+4]
    need(bytes(normalized)==expected,'Whole final linked '+family+' code modulo exact typed fields');counts['compiled_linked_'+family+'_functions']+=1;counts['compiled_linked_'+family+'_bytes']+=len(expected);counts['compiled_linked_'+family+'_relocations']+=len(rel)
   fsbindings=read(Path(build['preparation'])/'fs-hook-bindings.json');need(len(fsbindings)==51 and 'FS_OBSERVER_X86.OBJ'in pin(links[0]).read_text(encoding='utf-16').upper(),'Current final51 FS wrappers physically linked')
   fs_symbols,fs_sections=C.parse_coff(pin(release/'fs_observer_x86.obj').read_bytes());fsdefs={x['name']:x for x in fs_symbols.values()if x['section']>0 and x['storage']==2};crt=P.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
   for item in fsbindings:
    pc,kind=item['PC'],item['kind'];raw=bytes.fromhex(item['raw_bytes']);need(physical(crt if pc>=0x78000000 else game,pc,len(raw))==raw,'Every exact physical source FS opcode')
    expected,rel,marks=C.expected_function(pc,kind,raw);needle=struct.pack('<3I',pc,len(raw),kind);matches=[];cursor=0
    while True:
     at=workerbytes.find(needle,cursor)
     if at<0:break
     if workerbytes[at+16:at+16+len(raw)]==raw:matches.append(at)
     cursor=at+1
    need(len(matches)==1,'Unique final FS source initializer target');target=struct.unpack_from('<I',workerbytes,matches[0]+12)[0];check_compiled_linked('_'+item['declared_observer'],expected,rel,fsdefs,fs_sections,target,'FS');continuation='_fs_continue_'+format(pc,'x');need(words:=struct.unpack('<I',physical(worker,shared[continuation],4))[0]==pc+len(raw),'Actual final physical source FS continuation');rows.append(dict(gate=gate_name,family='FS',source_PC=pc,kind=kind,actual_worker_target=target,whole_compiled_linked_bytes=len(expected),relocations=len(rel),final_target_scope='Unique actual final FsHook initializer; corresponding complete runtime patch code page not separately captured',runtime_patch_page_observed=False))
   cp=P.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL').read_bytes());bindings=read(ROOT/'reports/m4-lockit-original/original-preparation-r4/lockit-hook-bindings.json');snap=reader.data('phase/0/0/lockit-snapshots.bin');need(len(snap)==6*12988,'Actual balanced CP observations for final target attribution');patched=snap[700:4796];iat=snap[8892:12988];boot={p:reader.data(f'lockit/post-DllMain/{p}-page.bin')for p in(0x7810a000,0x78145000,0x78146000)}
   need(boot[0x7810a000]==physical(cp,0x7810a000,4096),'Authentic complete postDllMain preferred-base source code page')
   symbols_,sections_=C.parse_coff(pin(release/'lockit_observer_x86.obj').read_bytes());cpdefs={x['name']:x for x in symbols_.values()if x['section']>0 and x['storage']==2};functions=[]
   for h in bindings:
    raw=bytes.fromhex(h['raw']);need(physical(cp,h['pc'],h['size'])==raw,'All exact provider source patch spans');i=h['pc']-0x7810a000;span=patched[i:i+h['size']];need(span[0]==0xe9 and span[5:]==bytes([0x90])*(h['size']-5),'Exact actual provider E9/padding');target=(h['pc']+5+int.from_bytes(span[1:5],'little',signed=True))&0xffffffff;functions.append((h['name'].replace('probe_','lockit_'),h['pc'],h['kind'],bytes.fromhex(h['replay']),'_lockit_continue_'+format(h['pc'],'x')if h['continuation']else None,None,target))
   for name,kind,slot in(('lockit_api_Enter',1,0x78146198),('lockit_api_Leave',4,0x78146184)):functions.append((name,0,kind,b'',None,'_lockit_actual_'+('Enter'if kind==1 else'Leave'),struct.unpack_from('<I',iat,slot&4095)[0]))
   for name,pc,kind,replay,cont,target,linked in functions:
    expected,rel=L.expected_lockit(pc,kind,replay,cont,target);check_compiled_linked('_'+name,expected,rel,cpdefs,sections_,linked,'Lockit')
    if cont:need(struct.unpack('<I',physical(worker,shared[cont],4))[0]==pc+len(replay),'Actual provider continuation DWORD')
    rows.append(dict(gate=gate_name,family='Lockit',source_PC=pc,kind=kind,actual_worker_target=linked,whole_compiled_linked_bytes=len(expected),relocations=len(rel),final_target_scope='Actual E9 target on complete observed provider page or actual named provider IAT API wrapper',runtime_patch_page_observed=True))
   expected=bytearray(boot[0x7810a000])
   for h in bindings:i=h['pc']-0x7810a000;expected[i:i+h['size']]=patched[i:i+h['size']]
   need(bytes(expected)==patched,'Complete provider code differs only by four exact declared observer spans');expected=bytearray(boot[0x78146000])
   for slot in(0x78146198,0x78146184):expected[slot&4095:(slot&4095)+4]=iat[slot&4095:(slot&4095)+4]
   need(bytes(expected)==iat,'Complete actual loaded provider IAT differs only by two named observer slots');counts['complete_provider_code_IAT_patch_page_relations']+=2
   for page,a in boot.items():need(reader.data(f'lockit/restored/{page}-page.bin')==a,'Actual entire original provider page restored after source root');counts['whole_final_restored_provider_pages']+=1
   ref=pin(Path(build['preparation'])/'reference.cpp').read_text();need('Exact formatting caller return span'in ref and 'Original selected source changed after checkpoint'in ref and 'Formatting source restored'in ref,'Actual executed worker guards source-before installer and complete source-after conservation');reader.close();reader=None;counts['actual_original_workers']+=1
  need(counts['compiled_linked_functions']==12 and len(template)==6 and counts['compiled_linked_FS_functions']==102 and counts['compiled_linked_Lockit_functions']==12,'Complete both worker attribution');passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if reader:reader.close()
  p=out/'compiled-observer-attribution.json';p.write_text(json.dumps(rows,indent=2)+'\n');pin(p);pin(__file__);report=dict(passed=passed,scope='Exact full compiled/final-linked six formatter,51FS and6Lockit wrappers in both genuine mixed original workers. Actual provider E9/IAT code pages are retained; game FS/format runtime patch pages are not separately captured, their unique final initializer targets and checked installer/restoration guards are bound. Independent review remains separate.',counts=dict(counts),actual_entry_IAT_targets_observed=True,return_hook_targets_from_actual_final_initializer=True,return_hook_runtime_page_observed=False,debugger_and_normal_compiled_wrapper_equality=True,allocator_generation_scope='Logical allocation occurrence index+1; no OS heap generation claim',whole_CPU40_FX512_ENV28_preservation=True,reader_closed=True,no_native_acceptance_credit=True,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
