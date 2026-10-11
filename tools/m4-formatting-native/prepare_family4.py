"""Compose the finite fourth formatter with literal mixed containers; no output seeds."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def main(name):
    out=R/'reports/m4-formatting-native'/name;assert not out.exists();out.mkdir(parents=True);pins={}
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    def one(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
    def edit(file,a,b):
        p=out/file;p.write_text(one(p.read_text(),a,b))
    def append_array(file,array,rows):
        p=out/file;s=p.read_text();pattern=r'(\b'+array+r'\[\]\{)(.*?)(\n\};)';s,n=re.subn(pattern,lambda m:m[1]+m[2]+'\n'+'\n'.join('{'+','.join(map(str,row))+'},'for row in rows)+m[3],s,count=1,flags=re.S);assert n==1,(file,array);p.write_text(s)
    previous=R/'reports/m4-formatting-native/preparation-r15';parent=read(previous/'report.json','bbe18a53a6c8c400f3274e470a28ded84d7c7c45c4fc860cf5e598ed4d5730aa')
    assert parent['passed']
    for p in previous.iterdir():
        if p.suffix in('.cpp','.hpp','.inc'):(out/p.name).write_bytes(pin(p,parent['files'][str(p.resolve())]).read_bytes())
    receipt_paths={
      'mixed_source':R/'reports/m4-mixed-format-original/original-source-r7/report.json',
      'mixed_interface':R/'reports/m4-mixed-format-original/native-interface-r1/report.json',
      'mixed_lifts':R/'reports/m4-mixed-format-original/lifts-r1/report.json',
      'mixed_recovery':R/'reports/m4-mixed-format-original/recovery-r1/report.json',
      'format_normal':R/'reports/m4-formatting-source/normal-contracts-r1/report.json',
      'format_source':R/'reports/m4-formatting-source/native-source-r9/report.json',
      'format_witnesses':R/'reports/m4-formatting-source/native-witnesses-r4/report.json'}
    receipts={k:read(v)for k,v in receipt_paths.items()}
    for receipt in receipts.values():assert receipt['passed']
    for key in('mixed_interface','mixed_lifts','mixed_recovery','format_normal'):
        for p,h in receipts[key]['files'].items():pin(p,h)
    interface=read(R/'reports/m4-mixed-format-original/native-interface-r1/contracts.json');game=read(R/'reports/m4-mixed-format-original/recovery-r1/instruction-contracts.json')
    normal=read(receipts['format_normal']['contracts'],receipts['format_normal']['contracts_sha256'])
    bodies={b['entry']:b for b in receipts['mixed_lifts']['source_bodies'].values()};root=interface['root'];assert root==0x4e1ca0
    accepted_bodies={int(k):v for k,v in parent['formatting_bodies'].items()}
    shared=bodies.pop(0x49bfd0);old=accepted_bodies[0x49bfd0]
    assert shared['source_sha256']==old['source_sha256'] and shared['source_bytes']==old['source_bytes']==1
    assert len(bodies)==6 and not set(bodies)&set(accepted_bodies)
    # Exact LLVM source-PC flag callback recovery; retain every source file consumed.
    callback_path=pin(R/'tools/m4-crt-locale-batch-recovery/callbacks.py');spec=importlib.util.spec_from_file_location('mixed_family_callback_recovery',callback_path);D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
    row_map={r['pc']:r for r in game['instructions']};callbacks={};callback_bodies={}
    folder=receipt_paths['mixed_lifts'].parent
    for key,b in receipts['mixed_lifts']['source_bodies'].items():
        if b['entry']not in bodies:continue
        pre=pin(folder/(key+'-pre.ll'));baseline=pin(folder/(key+'-baseline.ll'));host=pin(folder/(key+'-host.ll'),b['host_sha256'])
        calls,mapping=D.recover(D.function(pre.read_text(),b['entry']),D.function(baseline.read_text(),b['entry']),b['entry'],row_map)
        for call in calls:assert call['pc']not in callbacks or callbacks[call['pc']]==call['State_offsets'];callbacks[call['pc']]=call['State_offsets']
        callback_bodies[b['entry']]=dict(callback_sites=calls,source_marker_map=mapping)
    (out/'mixed-callbacks.json').write_text(json.dumps(dict(State_offsets_by_original_PC=callbacks,bodies=callback_bodies,AFTER_seed=False),indent=2)+'\n')
    # The new suffix byte sequence comes only from physical filename input and .zrd.
    pe_path=pin(R/'tools/analysis/pe.py');spec=importlib.util.spec_from_file_location('mixed_family_physical_pe',pe_path);PE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PE)
    physical=PE.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    filename=interface['entry_to_object']['filename'];filename_bytes=physical.read(physical.rva_range(filename-physical.image_base,7)[0],7);assert filename_bytes==b'valves\0'
    output_bytes=filename_bytes[:-1]+b'.zrd';request=len(output_bytes)+1;assert request==11
    new_owned=[dict(PC=0x7801042a,offset=i,width=1,writing=True,literal_value=v)for i,v in enumerate(output_bytes)]
    new_owned.extend([dict(PC=0x78022bd5,offset=len(output_bytes),width=1,writing=False,literal_value=0),dict(PC=0x78022bd5,offset=len(output_bytes),width=1,writing=True,literal_value=0)])
    begin=sum(len(c['owned_accesses'])for c in normal['cases']);assert begin==33 and len(new_owned)==12
    obj=interface['entry_to_object']['object'];pub=interface['entry_to_object']['format_owned_pointer_field']
    append_array('formatting_contract.inc','formatting_roots',[(root,obj,pub,filename,request,begin,len(new_owned))])
    append_array('formatting_contract.inc','formatting_owned_order',[(r['PC'],r['offset'],r['width'],str(r['writing']).lower(),r['literal_value'])for r in new_owned])
    # Expose only newly decoded physical rows; every shared row must have identical bytes.
    old_rows={r['pc']:r for r in normal['instructions']}
    old_rows.update({r['pc']:r for r in read(R/'reports/m4-formatting-frontier/recovery-r1/instruction-contracts.json')['instructions']})
    rows=[]
    for row in game['instructions']:
        if row['pc']in old_rows:assert row['bytes_hex']==old_rows[row['pc']]['bytes_hex'] and row['width']==old_rows[row['pc']]['width']
        else:rows.append(row)
    rows.sort(key=lambda r:r['pc']);assert len(rows)==230
    regs={r:i for i,r in enumerate(('', 'eax','ecx','edx','ebx','esp','ebp','esi','edi','al','cl','dl','bl','ah','ch','dh','bh','ax','cx','dx','bx','sp','bp','si','di'))}
    def operand(row,index,op):
        bits=op.get('bits',0)or next((x['bits']for x in row['decoded_operands']if x.get('bits')),32)
        if op['kind']=='register':v=[1,bits//8,regs[op['register']],0,0,0,1,0,0,1]
        elif op['kind']=='immediate':v=[2,bits//8,0,0,0,0,1,0,str(op['value']&0xffffffffffffffff)+'ULL',1]
        else:
            base=index_reg=0;scale=1
            for term in op['terms']:
                if not base and term['scale']==1:base=regs[term['register']]
                else:index_reg,scale=regs[term['register']],term['scale']
            d=op['displacement'];d=d-2**32 if d>=2**31 else d
            v=[3,bits//8,0,int(op['segment']=='fs'),base,index_reg,scale,d,0,int(index in row['explicit_memory_reads'])+2*int(index in row['explicit_memory_writes'])]
        return '{'+','.join(map(str,v))+'}'
    lines=['}','namespace mw34::m4_crt_locale_batch {','namespace {','constexpr unsigned mixed_format_root=0x4e1ca0;','constexpr SourceInstruction mixed_format_instructions[]{']
    for row in rows:
        ops=row['decoded_operands'];values=[operand(row,i,o)for i,o in enumerate(ops)]+['{}']*(3-len(ops));assert len(values)==3
        lines.append('{'+f'{row["pc"]},{row["width"]},{json.dumps(row["mnemonic"])},{{{{'+','.join(values)+'}},'+f'{len(ops)},{int(bool(row.get("repeat")))}'+'},')
    lines+=['};','constexpr SourceSpan mixed_format_spans[]{'];spans=[]
    for row in rows:
        raw=bytes.fromhex(row['bytes_hex'])
        if spans and spans[-1][0]+len(spans[-1][1])==row['pc']:spans[-1][1].extend(raw)
        else:spans.append([row['pc'],bytearray(raw)])
    for address,data in spans:lines.append('{'+f'{address},{len(data)},5,"{hashlib.sha256(data).hexdigest()}"'+'},')
    allocations=interface['MFC_allocation_contracts'];owned=interface['owned_access_contracts'];assert len(allocations)==3 and len(owned)==10
    owner_objects=[0x60b74c,obj,obj]
    lines+=['};','constexpr MfcRootInput mixed_format_mfc_inputs[]{']
    for i,a in enumerate(allocations):lines.append('{'+','.join(map(str,(root,a['allocation_CALL_pc'],a['requested'],owner_objects[i],0)))+'},')
    lines+=['};','struct MixedFormatOwned{unsigned pc,owner,offset,bytes;int value_owner;unsigned literal;};constexpr MixedFormatOwned mixed_format_owned[]{']
    for row in owned:
        relation=row['source_value_relation'];assert relation.get('offset',0)==0
        lines.append('{'+','.join(map(str,(row['source_pc'],row['owner_index'],row['owned_offset'],row['width'],relation.get('owner_index',-1),relation.get('literal',0))))+'},')
    lines+=['};','}']
    # Existing lower-level FS and Lockit machinery receives source-only exact rows.
    append_array('fs_contract.inc','fs_frames',[(f['function'],f['handler'],f['read_pc'],f['install_pc'],f['saved_predecessor_read_pc'],f['restore_pc'],f['return_pc'])for f in interface['FS_frame_contracts']])
    append_array('fs_contract.inc','fs_inputs',[(root,a['allocation_CALL_pc'],a['requested'],owner_objects[i],a['publication_address'],a['publication_pc'],0,0,0)for i,a in enumerate(allocations)])
    append_array('fs_contract.inc','fs_owned_accesses',[(root,r['source_pc'],1,r['width'],root,r['allocation_CALL_pc'],r['owned_offset'])for r in owned])
    lock=interface['Lockit_scratch_contracts'];assert [r['scratch_from_entered_CALL_frame_offset']for r in lock]==[48,48]
    append_array('lockit_contract.inc','lockit_inputs',[(root,lock[0]['CALL_pc'],lock[1]['CALL_pc'],48,48)])
    # Wrap the already frozen family lookup/dispatch; retain its exact bodies.
    for file,functions in [('formatting_contract.inc',('instruction','source_spans','generated_undefined_sites','has_body','dispatch_body','registration_callback')),('tree_contract.inc',('mfc_root_input',))]:
        p=out/file;s=p.read_text()
        for fn in functions:s=re.sub(r'\b'+fn+r'\(','accepted128_'+fn+'(',s)
        p.write_text(s)
    lines+=['const SourceInstruction*instruction(unsigned pc)noexcept{auto i=std::lower_bound(std::begin(mixed_format_instructions),std::end(mixed_format_instructions),pc,[](const auto&r,unsigned p){return r.pc<p;});return i!=std::end(mixed_format_instructions)&&i->pc==pc?i:accepted128_instruction(pc);}',
      'std::span<const SourceSpan>source_spans()noexcept{static const auto all=[](){auto b=accepted128_source_spans();std::vector<SourceSpan>v(b.begin(),b.end());v.insert(v.end(),std::begin(mixed_format_spans),std::end(mixed_format_spans));return v;}();return all;}',
      'unsigned registration_callback(unsigned root)noexcept{return root==mixed_format_root?0x4e1ce0:accepted128_registration_callback(root);}',
      'const MfcRootInput*mfc_root_input(unsigned root,unsigned site)noexcept{if(root==mixed_format_root)for(const auto&i:mixed_format_mfc_inputs)if(i.call==site)return &i;return accepted128_mfc_root_input(root,site);}']
    lines+=['extern "C" void*'+b['symbol']+'_body(State*,unsigned,void*);'for b in bodies.values()]
    lines+=['bool has_body(unsigned pc)noexcept{switch(pc){']+[f'case {pc}:return true;'for pc in bodies]+['default:return accepted128_has_body(pc);}}','void*dispatch_body(unsigned pc,State*s,void*p){switch(pc){']+[f'case {pc}:return {b["symbol"]}_body(s,pc,p);'for pc,b in bodies.items()]+['default:return accepted128_dispatch_body(pc,s,p);}}']
    added=[pc for pc,offsets in callbacks.items()for _ in offsets]
    lines+=['std::span<const unsigned>generated_undefined_sites()noexcept{static const auto all=[](){auto b=accepted128_generated_undefined_sites();std::map<unsigned,unsigned>counts,added;std::vector<unsigned>v;constexpr unsigned n[]{'+','.join(map(str,added))+'};for(auto pc:b)++counts[pc];for(auto pc:n)++added[pc];for(auto[pc,num]:added)counts[pc]=std::max(counts[pc],num);for(auto[pc,num]:counts)for(unsigned k=0;k<num;++k)v.push_back(pc);return v;}();return all;}','}','namespace {']
    (out/'mixed_format_contract.inc').write_text('\n'.join(lines)+'\n')
    p=out/'registry_library.cpp';s=one(p.read_text(),'#include "formatting_contract.inc"','#include "formatting_contract.inc"\n#include "mixed_format_contract.inc"');existing=set(re.findall(r'extern "C" .+?(\w+)\(',s));bridges={v for b in bodies.values()for v in b['bridges']}
    for symbol in sorted(bridges-existing):
        if symbol.endswith('_undefined_8'):s+='\nextern "C" unsigned char '+symbol+'(){return mw34::m4_onexit::undefined();}\n'
        elif '_direct_'in symbol or symbol.startswith('sub_'):s+='\nextern "C" void*'+symbol+'(State*s,unsigned a,void*p){return mw34::m4_onexit::called(p,s,a);}\n'
        else:raise ValueError(symbol)
    p.write_text(s)
    (out/'mixed_format_operations.inc').write_bytes(pin(R/'tools/m4-formatting-native/mixed_format_operations.inc').read_bytes())
    edit('locale_batch.hpp','void formatting_enter();','void mixed_format_enter();void mixed_format_owner_before(unsigned,std::uint64_t,unsigned,bool);void mixed_format_called(unsigned,unsigned,unsigned);void mixed_format_returned(unsigned);void formatting_enter();')
    edit('locale_batch_operations.inc','formatting_owner_before(a,0,n,false);','formatting_owner_before(a,0,n,false);mixed_format_owner_before(a,0,n,false);')
    edit('locale_batch_operations.inc','formatting_owner_before(a,v,n,true);','formatting_owner_before(a,v,n,true);mixed_format_owner_before(a,v,n,true);')
    edit('locale_batch_operations.inc','formatting_called(target,w.pc,w.address);','mixed_format_called(target,w.pc,w.address);formatting_called(target,w.pc,w.address);')
    edit('locale_batch_operations.inc','formatting_returned(f.entry,state.gpr.rax.dword,f.frame);','mixed_format_returned(f.entry);formatting_returned(f.entry,state.gpr.rax.dword,f.frame);')
    edit('locale_batch_operations.inc','live_allocations()>88','live_allocations()>92')
    with(out/'locale_batch_operations.inc').open('a')as stream:stream.write('\n#include "mixed_format_operations.inc"\n')
    edit('formatting_operations.inc','formatting_completed_>=3','formatting_completed_>=4')
    edit('formatting_operations.inc','if(!formatting_active_)return;const auto*r=formatting_root(registry_root_);\n if(entry==malloc_entry)', 'if(!formatting_active_)return;const auto*r=formatting_root(registry_root_);\n if(entry==malloc_entry&&std::none_of(formatting_calls_.begin(),formatting_calls_.end(),[&](const auto&w){return w[1]==registry_root_&&w[3]==entry&&w[4]==frame&&!w[14];}))return;\n if(entry==malloc_entry)')
    edit('session_impl.inc','binding->formatting_enter();binding->tree_enter();binding->guard();','binding->formatting_enter();binding->mixed_format_enter();binding->tree_enter();binding->guard();')
    edit('session_impl.inc','if(bootstrapped&&!failed){','if(r.poisoned())poison();\n   if(bootstrapped&&!failed){')
    objects=dict(parent['entry_objects'])
    for b in bodies.values():
        for objfile in b['objects'].values():objects[str(pin(objfile['path'],objfile['sha256']))]=objfile['sha256']
    expected_family_objects=396
    assert len(objects)==2*expected_family_objects,(len(objects),expected_family_objects)
    current_bodies=accepted_bodies|bodies;assert len(current_bodies)==25
    (out/'family-contracts.json').write_text(json.dumps(dict(schema='mw34-formatting4-native-finite-v1',root=root,mixed_interface=interface,additional_format_owned_order=new_owned,decoded_new_rows=rows,source_spans=[dict(address=a,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())for a,b in spans],source_filename_hex=filename_bytes.hex(),source_suffix_hex=b'.zrd'.hex(),source_requested=request,shared_RETinstruction_deduplicated=0x49bfd0,expected_objects_per_level=396,live_owner_bound=92,AFTER_seed=False),indent=2)+'\n')
    pin(__file__)
    for p in out.iterdir():
        if p.is_file():pin(p)
    result=parent|dict(scope='Unexecuted finite literal formatting4 native composition over accepted125; mixed owners/FS/Lockit use actual native storage',native_library=str(out/'registry_library.cpp'),native_include=str(out),entry_objects=objects,new_roots=parent['new_roots']+[root],formatting_bodies={str(k):v for k,v in current_bodies.items()},formatting_bodies_count=25,literal_objects_per_level=396,ordinary_pages=46,live_owner_bound=92,inherited_live_owner_bound=85,inherited_selected_roots=125,new_selected_roots=4,current_selected_roots=129,current_callback_roots=101,mixed_format_root=root,mixed_contracts=str(out/'family-contracts.json'),mixed_contracts_sha256=sha(out/'family-contracts.json'),mixed_callbacks=str(out/'mixed-callbacks.json'),mixed_callbacks_sha256=sha(out/'mixed-callbacks.json'),parent_preparation=str(previous/'report.json'),parent_preparation_sha256=sha(previous/'report.json'),source_or_native_executed=False,initializer_credit=0,external_Runtime_poison_cleanup=True,files=pins)
    result.update({k+'_receipt':str(v)for k,v in receipt_paths.items()});result.update({k+'_receipt_sha256':sha(v)for k,v in receipt_paths.items()})
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),new_rows=len(rows),bodies=len(current_bodies),objects_per_level=expected_family_objects)))
if __name__=='__main__':main(sys.argv[1])
