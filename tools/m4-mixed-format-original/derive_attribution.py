"""Extend the sealed formatter COFF/link verifier to all current FS and CP observers."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def one(s,a,b):
 assert s.count(a)==1,a[:70];return s.replace(a,b,1)
s=(ROOT/'tools/m4-formatting-original/attribute_observers.py').read_text().replace("BASE=ROOT/'reports/m4-formatting-original'","BASE=ROOT/'reports/m4-mixed-format-original'")
s=one(s,"('prefix-validation-r1','54199a2f52a1c7489ccc53a8722bf6dc1d06395e7c05c6043e84f82af5f1b3e4'),('trace-prefix-validation-r1','d410d2020a019e17e0ec88154520b8e89c165a5e52685c3b75c45fc274ddac25')","('prefix-validation-r1','a909c998cd40be724397c38adf63d89ec1d0246c282da3f8bfe28d4689af772b'),('trace-prefix-validation-r1','bfebfd1929e0a023e11857855286d354927f6f343bfc495db1b036397480b4b6')")
marker="   ref=pin(Path(build['preparation'])/'reference.cpp').read_text();"
block=r'''   # No source CPU/memory expectations enter this compiled-byte verification.
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
'''
s=one(s,marker,block+marker)
s=one(s,"counts['compiled_linked_functions']==12 and len(template)==6","counts['compiled_linked_functions']==12 and len(template)==6 and counts['compiled_linked_FS_functions']==102 and counts['compiled_linked_Lockit_functions']==12")
s=s.replace('Exact full compiled and final linked six formatter CPU/FX/ENV/cdecl wrappers in both genuine original workers, actual entry IAT targets and physical return-hook initializer targets. Original return hook runtime page is not separately captured; checked installer and source-restoration guards are bound. Independent review remains separate.','Exact full compiled/final-linked six formatter,51FS and6Lockit wrappers in both genuine mixed original workers. Actual provider E9/IAT code pages are retained; game FS/format runtime patch pages are not separately captured, their unique final initializer targets and checked installer/restoration guards are bound. Independent review remains separate.')
p=ROOT/'tools/m4-mixed-format-original/attribute_observers.py';assert not p.exists();p.write_text(s)
