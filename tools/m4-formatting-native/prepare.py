"""Add finite literal formatting sources to accepted125 native provider."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
    out=R/'reports/m4-formatting-native'/name;assert not out.exists();out.mkdir(parents=True);pins={}
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    def one(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
    base=R/'reports/m4-tree-native/preparation-r5';parent=read(base/'report.json','9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2')
    for p in base.iterdir():
        if p.suffix in('.cpp','.hpp','.inc'):(out/p.name).write_bytes(pin(p,parent['files'][str(p.resolve())]).read_bytes())
    paths=[R/'reports/m4-formatting-frontier/lifts-r1/report.json',R/'reports/m4-formatting-source/lifts-r1/report.json',R/'reports/m4-formatting-source/callbacks-r1/report.json',R/'reports/m4-formatting-source/normal-contracts-r1/report.json']
    receipts=[read(p)for p in paths]
    for receipt in receipts:
        assert receipt['passed']
        for p,h in receipt['files'].items():pin(p,h)
    game_lift,provider_lift,callback_report,normal_report=receipts
    normal=read(normal_report['contracts'],normal_report['contracts_sha256']);callbacks=read(callback_report['callbacks'],callback_report['callbacks_sha256'])
    game_rec=read(R/'reports/m4-formatting-frontier/recovery-r1/report.json','8a2c511e47eddce2cab0929b9ede59e81276957ace6e2926b38c5323325dca15');game=read(R/'reports/m4-formatting-frontier/recovery-r1/instruction-contracts.json',game_rec['files'][str((R/'reports/m4-formatting-frontier/recovery-r1/instruction-contracts.json').resolve())])
    bodies={b['entry']:b for report in(game_lift,provider_lift)for b in report['source_bodies'].values()};assert len(bodies)==19
    rows=sorted(game['instructions']+normal['instructions'],key=lambda r:r['pc']);assert len(rows)==437
    registers={r:i for i,r in enumerate(('', 'eax','ecx','edx','ebx','esp','ebp','esi','edi','al','cl','dl','bl','ah','ch','dh','bh','ax','cx','dx','bx','sp','bp','si','di'))}
    def operand(row,index,op):
        bits=op.get('bits',0)or next((x['bits']for x in row['decoded_operands']if x.get('bits')),32)
        if op['kind']=='register':v=[1,bits//8,registers[op['register']],0,0,0,1,0,0,1]
        elif op['kind']=='immediate':v=[2,bits//8,0,0,0,0,1,0,str(op['value']&0xffffffffffffffff)+'ULL',1]
        else:
            base=index_reg=0;scale=1
            for term in op['terms']:
                if not base and term['scale']==1:base=registers[term['register']]
                else:index_reg,scale=registers[term['register']],term['scale']
            displacement=op['displacement'];displacement=displacement-2**32 if displacement>=2**31 else displacement
            v=[3,bits//8,0,int(op['segment']=='fs'),base,index_reg,scale,displacement,0,int(index in row['explicit_memory_reads'])+2*int(index in row['explicit_memory_writes'])]
        return '{'+','.join(map(str,v))+'}'
    lines=['}', 'namespace mw34::m4_crt_locale_batch {','namespace {','constexpr SourceInstruction formatting_instructions[]{']
    for row in rows:
        ops=row['decoded_operands'];assert len(ops)<=3;values=[operand(row,i,o)for i,o in enumerate(ops)]+['{}']*(3-len(ops))
        lines.append('{'+f'{row["pc"]},{row["width"]},{json.dumps(row["mnemonic"])},{{{{'+','.join(values)+'}},'+f'{len(ops)},{int(bool(row.get("repeat")))}'+'},')
    lines+=['};','struct FormattingRoot{unsigned root,object,publication,filename,request,owned_begin,owned_count;};constexpr FormattingRoot formatting_roots[]{']
    begin=0
    for case in normal['cases']:
        root=case['root_contract'];lines.append('{'+','.join(map(str,(root['entry'],root['object'],root['owned_pointer_field'],root['filename'],case['request'],begin,len(case['owned_accesses']))))+'},');begin+=len(case['owned_accesses'])
    lines+=['};','struct FormattingOwned{unsigned pc,offset,bytes;bool writing;std::uint64_t value;};constexpr FormattingOwned formatting_owned_order[]{']
    for case in normal['cases']:
        for row in case['owned_accesses']:lines.append('{'+f'{row["PC"]},{row["offset"]},{row["width"]},{str(row["writing"]).lower()},{row["literal_value"]}'+'},')
    spec=__import__('importlib.util',fromlist=['']).spec_from_file_location('format_native_pe',pin(R/'tools/analysis/pe.py'));mod=__import__('importlib.util',fromlist=['']).module_from_spec(spec);spec.loader.exec_module(mod);pe=mod.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    lines+=['};','struct FormattingImport{unsigned pc,slot,raw,target,argc;int frame_offset;};constexpr FormattingImport formatting_imports[]{']
    for row in normal['cdecl_source']:
        raw=int.from_bytes(pe.read(pe.rva_range(row['slot']-pe.image_base,4)[0],4),'little');lines.append('{'+','.join(map(str,(row['PC'],row['slot'],raw,row['target'],row['argc'],row['entry_offset'])))+'},')
    lines+=['};','constexpr SourceSpan formatting_spans[]{'];spans=[]
    for row in rows:
        raw=bytes.fromhex(row['bytes_hex'])
        if spans and spans[-1][0]+len(spans[-1][1])==row['pc']:spans[-1][1].extend(raw)
        else:spans.append([row['pc'],bytearray(raw)])
    for address,data in spans:lines.append('{'+f'{address},{len(data)},5,"{hashlib.sha256(data).hexdigest()}"'+'},')
    lines+=['};','}']
    for fn in('instruction','source_spans','source_pages','generated_undefined_sites','has_body','dispatch_body','registration_callback'):
        p=out/'tree_contract.inc';p.write_text(re.sub(r'\b'+fn+r'\(','accepted125_'+fn+'(',p.read_text()))
    lines+=['const SourceInstruction*instruction(unsigned pc)noexcept{auto i=std::lower_bound(std::begin(formatting_instructions),std::end(formatting_instructions),pc,[](const auto&r,unsigned p){return r.pc<p;});return i!=std::end(formatting_instructions)&&i->pc==pc?i:accepted125_instruction(pc);}',
        'std::span<const SourceSpan>source_spans()noexcept{static const auto all=[](){auto b=accepted125_source_spans();std::vector<SourceSpan>v(b.begin(),b.end());v.insert(v.end(),std::begin(formatting_spans),std::end(formatting_spans));return v;}();return all;}',
        'std::span<const SourcePage>source_pages()noexcept{static const auto all=[](){auto b=accepted125_source_pages();std::vector<SourcePage>v(b.begin(),b.end());for(unsigned p:std::array<unsigned,2>{0x78022000,0x78026000})if(std::none_of(v.begin(),v.end(),[&](const auto&r){return r.address==p;}))v.push_back({p,5});return v;}();return all;}',
        'unsigned registration_callback(unsigned root)noexcept{switch(root){']+[f'case {r["entry"]}:return {r["registration"]["callback"]};'for r in game['roots']]+['default:return accepted125_registration_callback(root);}}']
    lines+=['extern "C" void*'+b['symbol']+'_body(State*,unsigned,void*);'for b in bodies.values()]
    lines+=['bool has_body(unsigned pc)noexcept{switch(pc){']+[f'case {pc}:return true;'for pc in bodies]+['default:return accepted125_has_body(pc);}}','void*dispatch_body(unsigned pc,State*s,void*p){switch(pc){']+[f'case {pc}:return {b["symbol"]}_body(s,pc,p);'for pc,b in bodies.items()]+['default:return accepted125_dispatch_body(pc,s,p);}}']
    added=[int(pc)for pc,offsets in callbacks['State_offsets_by_original_PC'].items()for _ in offsets]
    lines+=['std::span<const unsigned>generated_undefined_sites()noexcept{static const auto all=[](){auto b=accepted125_generated_undefined_sites();std::map<unsigned,unsigned>counts,added;std::vector<unsigned>v;constexpr unsigned n[]{'+','.join(map(str,added))+'};for(auto pc:b)++counts[pc];for(auto pc:n)++added[pc];for(auto[pc,num]:added)counts[pc]=std::max(counts[pc],num);for(auto[pc,num]:counts)for(unsigned k=0;k<num;++k)v.push_back(pc);return v;}();return all;}','}','namespace {']
    (out/'formatting_contract.inc').write_text('\n'.join(lines)+'\n');(out/'formatting_operations.inc').write_bytes(pin(R/'tools/m4-formatting-native/formatting_operations.inc').read_bytes())
    p=out/'locale_batch.hpp';p.write_text(one(p.read_text(),'bool tree_started_{},tree_completed_{};','bool formatting_active_{};unsigned formatting_base_{},formatting_owner_{},formatting_generation_{},formatting_owned_cursor_{},formatting_dispatch_cursor_{},formatting_publications_{},formatting_completed_{};std::vector<std::array<std::uint64_t,16>>formatting_calls_;std::vector<std::array<std::uint64_t,12>>formatting_owned_,formatting_publication_records_;std::vector<std::array<std::uint64_t,8>>formatting_dispatches_;void formatting_enter();std::uint64_t formatting_read(unsigned,std::uint64_t,unsigned);void formatting_owner_before(unsigned,std::uint64_t,unsigned,bool);void formatting_owner_after(unsigned,std::uint64_t,unsigned,bool);void formatting_called(unsigned,unsigned,unsigned);void formatting_returned(unsigned,unsigned,unsigned);\n bool tree_started_{},tree_completed_{};'))
    p=out/'registry_contract.inc';s=p.read_text();s,n=re.subn(r'constexpr unsigned registry_game_pages\[\]\{([^}]+)\};',lambda m:'constexpr unsigned registry_game_pages[]{'+m[1]+',0x5cd000,0x5e3000,0x5e9000};',s);assert n==1;p.write_text(s)
    p=out/'locale_batch_operations.inc';s=p.read_text();s=one(s,'else if(m=="stosb"','else if(m=="scasb"){allowed=!writing&&n==1&&a==state.gpr.rdi.dword;}\n else if(m=="stosb"');s=one(s,'return lockit_read(a,mfc_read(a,v,n),n);','return formatting_read(a,lockit_read(a,mfc_read(a,v,n),n),n);')
    s=one(s,'vtable_read_before(a,n);','formatting_owner_before(a,0,n,false);vtable_read_before(a,n);');s=one(s,'vtable_read_after(a,v,n);','formatting_owner_after(a,v,n,false);vtable_read_after(a,v,n);');s=one(s,'vtable_write_before(a,v,n);','formatting_owner_before(a,v,n,true);vtable_write_before(a,v,n);');s=one(s,'vtable_write_after(a,v,n);','formatting_owner_after(a,v,n,true);vtable_write_after(a,v,n);');s=one(s,'lockit_called(target,w.pc,w.address);','formatting_called(target,w.pc,w.address);lockit_called(target,w.pc,w.address);');s=one(s,'lockit_returned(f.entry,state.gpr.rax.dword,f.frame);','formatting_returned(f.entry,state.gpr.rax.dword,f.frame);lockit_returned(f.entry,state.gpr.rax.dword,f.frame);');s=one(s,'sink("locale-summary.bin",','const std::array<unsigned,10>formatting_status{1,unsigned(formatting_active_),formatting_completed_,formatting_base_,formatting_owner_,formatting_generation_,formatting_owned_cursor_,formatting_dispatch_cursor_,formatting_publications_,registry_root_};sink("formatting-status.bin",std::as_bytes(std::span(formatting_status)),context);sink("formatting-calls.bin",std::as_bytes(std::span(formatting_calls_)),context);sink("formatting-owned.bin",std::as_bytes(std::span(formatting_owned_)),context);sink("formatting-publications.bin",std::as_bytes(std::span(formatting_publication_records_)),context);sink("formatting-dispatches.bin",std::as_bytes(std::span(formatting_dispatches_)),context);\n sink("locale-summary.bin",');p.write_text(s+'\n#include "formatting_operations.inc"\n')
    p=out/'session_impl.inc';s=p.read_text();s=one(s,'binding->tree_enter();binding->guard();','binding->formatting_enter();binding->tree_enter();binding->guard();');p.write_text(s)
    p=out/'registry_library.cpp';s=one(p.read_text(),'#include "tree_contract.inc"','#include "tree_contract.inc"\n#include "formatting_contract.inc"');existing=set(re.findall(r'extern "C" .+?(\w+)\(',s));bridges={v for b in bodies.values()for v in b['bridges']}
    for symbol in sorted(bridges-existing):
        if symbol.endswith('_undefined_8'):s+='\nextern "C" unsigned char '+symbol+'(){return mw34::m4_onexit::undefined();}\n'
        elif '_direct_'in symbol or symbol.startswith('sub_'):s+='\nextern "C" void*'+symbol+'(State*s,unsigned a,void*p){return mw34::m4_onexit::called(p,s,a);}\n'
        else:raise ValueError(symbol)
    p.write_text(s);objects=dict(parent['entry_objects'])
    for b in bodies.values():
        for o in b['objects'].values():objects[str(pin(o['path'],o['sha256']))]=o['sha256']
    pin(__file__)
    for p in out.iterdir():
        if p.is_file():pin(p)
    result=parent|dict(scope='Unexecuted literal formatting3 native preparation; exact normal cdecl/table/owner byteflow contracts',native_library=str(out/'registry_library.cpp'),native_include=str(out),entry_objects=objects,new_roots=[r['entry']for r in game['roots']],source_lifts=str(paths[0]),provider_lifts=str(paths[1]),source_lifts_sha256=sha(paths[0]),provider_lifts_sha256=sha(paths[1]),normal_contracts=str(paths[3]),normal_contracts_sha256=sha(paths[3]),source_pages=sorted(set(parent['source_pages'])|{0x78022000,0x78026000}),game_pages=sorted(set(parent['game_pages'])|{0x5cd000,0x5e3000,0x5e9000}),formatting_bodies={str(k):v for k,v in bodies.items()},source_or_native_executed=False,initializer_credit=0,files=pins)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
