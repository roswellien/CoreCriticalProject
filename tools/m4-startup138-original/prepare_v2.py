"""Fresh chronological original138 preparation; no worker or archive reader.

The accepted131 machine/bootstrap/observer ABI is retained. Seven physical
widget/FPS roots occupy the actual sorted CRT slots and share that same carried
game/CRT/MFC state. Inputs come from the real source pack and genuine loaders.
"""
from pathlib import Path
import copy,hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
OLD=R/'reports/m4-startup131-original/preparation-r4'
FAMILY=R/'reports/m4-fps-original/preparation-r1'
JOINT=R/'reports/m4-joint-startup138/preparation-r4'
ROOTS=(0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0)
PHASES=(15,16,17,47,134,135,136)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
def one(s,a,b):need(s.count(a)==1,'Exact additive original138 hunk '+a[:110]);return s.replace(a,b,1)
def array(s,field,values):
    pat=r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;'
    need(len(re.findall(pat,s))==1,'Exact source array '+field)
    return re.sub(pat,f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};',s)
def parse_pack(raw):
    count=struct.unpack_from('<I',raw,8)[0];need(raw[:8]==b'MW4J124P' and len(raw)==12+count*4104,'Exact whole sparse pack geometry')
    rows={}
    for i in range(count):
        p,perm=struct.unpack_from('<2I',raw,12+i*4104);need(p%4096==0 and p not in rows and perm in(0,1,2),'Distinct actual source page/permission');rows[p]=(perm,bytearray(raw[20+i*4104:4116+i*4104]))
    return rows
def main(name):
    out=R/'reports/m4-startup138-original'/name;need(not out.exists(),'Fresh additive original138 preparation');files={};deltas=[]
    def pin(p,h=None):
        p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No capture/archive reader');v=sha(p);need(h is None or h==v,'Exact original138 source input '+str(p));files[str(p)]=v;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    def text(p):return pin(p).read_text(encoding='utf-8-sig')
    old=read(OLD/'report.json','1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb')
    family=read(FAMILY/'report.json');joint=read(JOINT/'report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a')
    need(old['passed']and family['passed']and joint['passed'],'Exact reviewed parent and family recipes')
    for receipt,folder in((old,OLD),(family,FAMILY),(joint,JOINT)):
        # Do not walk their entire ancestor union or touch captures. Every
        # current consumed leaf below is physically rehashed independently.
        for p in folder.iterdir():
            if p.is_file() and p.suffix.lower()in('.cpp','.hpp','.asm','.json','.bin','.txt') and str(p.resolve())in receipt['files']:pin(p,receipt['files'][str(p.resolve())])
    selected=joint['selected_order'];need(len(selected)==138,'Actual current native selected138 schedule')
    pairs=[(v['slot'],v['entry'])for v in selected]
    need([v for v in pairs if v[1]not in ROOTS]==[(v['slot'],v['entry'])for v in old['selected_order']],'Every accepted131 relative table pair retained')
    need(tuple(selected[p]['entry']for p in PHASES)==ROOTS and selected[13]['entry']==0x5ae3e4,'Exact seven actual phases and earlier MFC chronology')
    pages=read(JOINT/'source-page-union.json',joint['files'][str((JOINT/'source-page-union.json').resolve())]);native_whole=list(pages['union']);need(len(native_whole)==len(set(native_whole))==69,'Complete actual current69 source pages');whole=old['observed_pages']+old['extra_whole_source_pages']+[p for p in native_whole if p not in old['observed_pages']+old['extra_whole_source_pages']];need(set(whole)==set(native_whole)and len(whole)==69,'Exact inherited43+3 order plus23 new whole observed source pages')
    fixed=old['observed_pages'];need(len(fixed)==43 and set(fixed)<=set(whole),'Fixed originalRecord43-page ABI remains exact')
    extra=[p for p in whole if p not in fixed];need(len(extra)==26,'Separate26 whole source endpoints without ABI expansion')
    sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
    pin(R/'tools/analysis/pe.py');game=PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    records=parse_pack(pin(OLD/'pages.bin',old['pack_sha256']).read_bytes());fpack=parse_pack(pin(FAMILY/'pages.bin',family['pack_sha256']).read_bytes())
    spans=copy.deepcopy(old['source_spans']);known={v['pc']:v for v in spans};new=[];overlay=[]
    for p,(perm,b)in fpack.items():
        if p not in records:records[p]=(perm,bytearray(b));continue
        need(records[p][0]==perm,'Same physical source page permission')
        if perm==2:need(records[p][1]==b,'Complete identical retained physical RW BEFORE page')
    for row in family['source_spans']:
        if row['pc']in known:need(row==known[row['pc']],'Exact same retained physical source row');continue
        need(row['origin']==0,'All additive widget source rows belong to game PE')
        off,_=game.rva_range(row['pc']-game.image_base,row['size']);need(off==row['image_offset'],'Whole physical widget instruction offset');code=game.data[off:off+row['size']]
        for n,value in enumerate(code):
            a=row['pc']+n;p=a&~4095;o=a&4095
            if p not in records:records[p]=(1,bytearray(b'\xcc'*4096))
            perm,b=records[p];need(perm==1 and len(b)==4096 and b[o]in(0xcc,value),'Only exact physical source overlays inherited sparse RX padding')
            if b[o]!=value:overlay.append(dict(address=a,before=b[o],after=value,source_PC=row['pc']))
            b[o]=value
        spans.append(row);known[row['pc']]=row;new.append(row)
    need(len(new)==1060 and len(spans)==5040,'Whole known original131 plus physical seven-family source closure')
    for slot,entry in pairs:
        off,_=game.rva_range(slot-game.image_base,4);need(struct.unpack_from('<I',game.data,off)[0]==entry and struct.unpack_from('<I',records[slot&~4095][1],slot&4095)[0]==entry,'Every real physical CRT initializer table cell')
    for p,(_,b)in records.items():need(len(b)==4096,'No source row may grow a page across a boundary')
    pack=b'MW4J124P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,perm)+b for p,(perm,b)in records.items());need(len(pack)==12+4104*len(records),'Final whole pack geometry')
    out.mkdir(parents=True)
    for p in OLD.iterdir():
        if p.is_file()and p.suffix.lower()in('.cpp','.hpp','.asm','.txt'):(out/p.name).write_bytes(pin(p,old['files'][str(p.resolve())]).read_bytes())
    for fn in('widget_observer_x86.asm','fps_observer_x86.asm'):(out/fn).write_bytes(pin(FAMILY/fn,family['files'][str((FAMILY/fn).resolve())]).read_bytes())
    (out/'pages.bin').write_bytes(pack)
    spec=text(OLD/'spec.hpp');spec=one(spec,old['pack_sha256'],sha(out/'pages.bin'));spec=re.sub(r'pack_size=\d+','pack_size='+str(len(pack)),spec)
    for field,values in(('entries',[v['entry']for v in selected]),('table_slots',[v['slot']for v in selected]),('page_bases',list(records)),('page_permissions',[v[0]for v in records.values()])):
        spec=array(spec,field,values)
    m=re.search(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',spec);need(m is not None,'One physical source binding array')
    spec=one(spec,m[0],f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings'+'{{'+','.join('{'+','.join(hex(v[k])for k in('pc','size','image_offset','origin'))+'}'for v in spans)+'}};')
    spec+='\ninline constexpr std::array<unsigned,7> widget_selected_roots{'+','.join(hex(r)for r in ROOTS)+'};\ninline constexpr std::array<unsigned,26> widget_extra_pages{'+','.join(hex(p)for p in extra)+'};\ninline constexpr std::array<unsigned,69> widget_whole_pages{'+','.join(hex(p)for p in whole)+'};\n'
    (out/'spec.hpp').write_text(spec)
    protocol=one(text(OLD/'protocol.hpp'),'sequences=6, roots=131','sequences=6, roots=138');(out/'protocol.hpp').write_text(protocol)
    ref=text(OLD/'reference.cpp');fref=text(FAMILY/'reference.cpp')
    def change(a,b):
        nonlocal ref
        ref=one(ref,a,b);deltas.append(dict(before=a,after=b))
    change('#include "prerequisite_observer.hpp"','#include "prerequisite_observer.hpp"\n#include "widget_observer.hpp"\n#include "fps_observer.hpp"')
    for fn,size in(('widget_observer.hpp',287444),('fps_observer.hpp',550180)):
        s=text(FAMILY/fn);s=one(s,',pages[64*4096]',',pages[69*4096]');old_size=266964 if fn.startswith('widget')else 529700;s=one(s,'=='+str(old_size),'=='+str(size));(out/fn).write_text(s)
    # Keep old131 FS1216/12B evidence untouched. A root-gated second ledger
    # retains the widget vector helper's complete16B records/1224B geometry.
    a=fref.index('struct FsEvent');b=fref.index('extern "C" extern "C"',a)
    fs_extra=fref[a:b].rstrip();need(fs_extra.endswith('\n}'),'Exact inherited extern block end');fs_extra=fs_extra[:-2]
    fs_extra='unsigned widget_fs_event_count{};\n'+fs_extra
    fs_extra=fs_extra.replace('FsEvent','WidgetFsEvent').replace('fs_events','widget_fs_events').replace('fs_event_count','widget_fs_event_count').replace('fs_observe_before','widget_fs_observe_before').replace('fs_observe_after','widget_fs_observe_after')
    fs_extra=one(fs_extra,'if(!fs_phase_root)return;','if(std::find(widget_selected_roots.begin(),widget_selected_roots.end(),fs_phase_root)==widget_selected_roots.end())return;') if fs_extra.count('if(!fs_phase_root)return;')==1 else fs_extra.replace('if(!fs_phase_root)return;','if(std::find(widget_selected_roots.begin(),widget_selected_roots.end(),fs_phase_root)==widget_selected_roots.end())return;')
    change('void fs_observe_before(){','void widget_fs_observe_before();void widget_fs_observe_after();\n'+fs_extra+'\nvoid fs_observe_before(){\n if(std::find(widget_selected_roots.begin(),widget_selected_roots.end(),fs_phase_root)!=widget_selected_roots.end()){widget_fs_observe_before();return;}')
    change('void fs_observe_after(){','void fs_observe_after(){\n if(std::find(widget_selected_roots.begin(),widget_selected_roots.end(),fs_phase_root)!=widget_selected_roots.end()){widget_fs_observe_after();return;}')
    # The seven new roots have their own complete source/GDI/FPS proof domain.
    # The inherited fixed-receiver and NULL-free metadata observers are only
    # applicable to the original131 contracts. Their assembly still executes
    # the exact source replay; metadata handlers stutter for these seven roots.
    for handler in('nullfree_observe','vtable_observe'):
        change('void '+handler+'(){\n if(!fs_phase_root)return;','void '+handler+'(){\n if(std::find(widget_selected_roots.begin(),widget_selected_roots.end(),fs_phase_root)!=widget_selected_roots.end())return;\n if(!fs_phase_root)return;')
    fs=read(OLD/'fs-hook-bindings.json');ffs=read(FAMILY/'fs-hook-bindings.json');old_pc={v['PC']for v in fs};add=[v for v in ffs if v['PC']not in old_pc]
    asm=text(OLD/'fs_observer_x86.asm');fasm=text(FAMILY/'fs_observer_x86.asm')
    declarations=[];definitions=[]
    for v in add:
        pc=v['PC'];name=v['declared_observer'];match=re.search(r'PUBLIC '+name+r'\n'+name+r' PROC\n.*?'+name+r' ENDP\n',fasm,re.S);need(match is not None,'Whole exact existing widget FS wrapper')
        definitions.append(match[0]);declarations.append(f'EXTERN fs_continue_{pc:x}:DWORD')
    asm=one(asm,'.code\n','\n'.join(declarations)+'\n.code\n');asm=one(asm,'END\n',''.join(definitions)+'END\n');(out/'fs_observer_x86.asm').write_text(asm)
    change('struct FsHook','\n'.join(f'extern "C" void {v["declared_observer"]}();\nextern "C" const unsigned fs_continue_{v["PC"]:x}=0x{v["continuation"]:x};'for v in add)+'\nstruct FsHook')
    m=re.search(r'const std::array<FsHook,\d+>\s*fs_hooks\{\{(.*?)\}\};',ref,re.S);need(m is not None,'Actual old FS hook array')
    entries=''.join(',{0x'+format(v['PC'],'x')+','+str(len(bytes.fromhex(v['raw_bytes'])))+','+str(v['kind'])+',&'+v['declared_observer']+',{'+','.join('0x'+format(x,'x')for x in bytes.fromhex(v['raw_bytes']))+'}}'for v in add)
    change(m[0],f'const std::array<FsHook,{len(fs)+len(add)}>fs_hooks'+'{{'+m[1]+entries+'}};')
    def lines(start,end):
        a=fref.index(start);b=fref.index(end,a);return fref[a:b]
    # The actual canonical GDI library is loaded once, with exact forwarder
    # identity exported. No source initializer or API is preinvoked.
    named=lines('    const std::array<const char*,3> widget_names','    auto*crtbegin=')
    change('    auto*crtbegin=','    const auto gdi=LoadLibraryW(L"gdi32.dll");require(gdi,"Actual canonical GDI provider load");\n'+named+'    auto*crtbegin=')
    install=lines('    for(unsigned i=0;i<3;++i){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(widget_IATs[i])','    owner=GetCurrentThreadId();')
    change('    owner=GetCurrentThreadId();',install+'    owner=GetCurrentThreadId();')
    identity=lines('    std::vector<unsigned> widget_identity;','    out.append("crt-image.bin"')
    need(identity,'Complete actual forwarder/formatter identity export block')
    change('    std::cerr<<"Original131 writermetadataready\\n";',identity+'    std::cerr<<"Original138 writermetadataready\\n";')
    change('        mixed_allocation_count=0;','        widget_resource_count=0;std::memset(widget_resources,0,sizeof(widget_resources));\n        mixed_allocation_count=0;')
    change('            auto r=std::make_unique<Record>();','            widget_fs_event_count=0;widget_count=0;widget_error=0;fps_count=0;fps_error=0;std::memset(widget_snapshots,0,sizeof(widget_snapshots));std::memset(fps_snapshots,0,sizeof(fps_snapshots));\n            auto r=std::make_unique<Record>();')
    exports=lines('            const auto fstem=','            for(unsigned p:widget_extra_pages)')
    change('            require(registry_API_count<=256,"Bounded actualAPI ledger");',exports+'            out.append(phase_stem+"/widget-fs-count.bin",&widget_fs_event_count,4);require(widget_fs_event_count<=2048,"Whole widget FS ledger bound before export");out.append(phase_stem+"/widget-fs-events.bin",widget_fs_events,widget_fs_event_count*sizeof(WidgetFsEvent));require(!widget_error&&!fps_error,"Actual current widget/FPS observer transparency");\n            require(registry_API_count<=256,"Bounded actualAPI ledger");')
    registry_before=lines('            const auto registry_cap_before=','            for(unsigned i=0;i<64;++i)')
    change('            for(auto page:format_extra_pages)',registry_before+'            for(auto page:format_extra_pages)') if ref.count('            for(auto page:format_extra_pages)')==1 else None
    # Both original extra-page loops remain distinct equality endpoints. The
    # BEFORE registry observation precedes the first loop and actual execute().
    if not registry_before in ref:
        change('            for(auto page:format_extra_pages)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/extra-before/"',registry_before+'            for(auto page:format_extra_pages)out.append("phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/extra-before/"')
    change('    const std::array<unsigned,3> format_extra_pages{0x5cd000,0x5e3000,0x5e9000};','    const auto& format_extra_pages=widget_extra_pages;')
    # Preserve all complete loaded provider pages independently of the source
    # union, so future source comparison has actual owning inputs at each root.
    change('            const bool format_phase=','            for(unsigned i=0;i<64;++i)out.append(phase_stem+"/CRT-before/"+std::to_string(0x78000000+i*4096)+".bin",reinterpret_cast<void*>(0x78000000+i*4096),4096);\n            const bool format_phase=')
    change('            const auto fstem=', '            for(unsigned i=0;i<64;++i)out.append(phase_stem+"/CRT-after/"+std::to_string(0x78000000+i*4096)+".bin",reinterpret_cast<void*>(0x78000000+i*4096),4096);\n            const auto fstem=')
    api_final=lines('            for(unsigned ai=0;ai<registry_API_count;++ai)if(registry_API_ledger[ai].kind==0&&registry_API_ledger[ai].after.eax){const auto pointer=','            require(registry_API_count<=256,"Bounded actualAPI ledger");')
    change('            require(registry_API_count<=256,"Bounded actualAPI ledger");','            require(registry_API_count<=256,"Bounded actualAPI ledger");\n            if(std::find(widget_selected_roots.begin(),widget_selected_roots.end(),entries[phase])!=widget_selected_roots.end()){\n'+api_final+'            }\n            require(registry_API_count<=256,"Bounded actualAPI ledger");')
    change('        require(*crtnext-*crtbegin==101*4','        require(*crtnext-*crtbegin==108*4')
    change('reinterpret_cast<void*>(*crtbegin),101*4','reinterpret_cast<void*>(*crtbegin),108*4')
    cleanup=lines('        for(unsigned i=0;i<widget_resource_count;++i)if(widget_resources[i].live)','        require(!std::memcmp(mfc540_loaded_page')
    cleanup_anchor='        require(!std::memcmp(mfc540_loaded_page.data(),reinterpret_cast<void*>(0x5f4cc000),4096),"Same-worker initialized MFC page source cleanup carry");'
    change(cleanup_anchor,cleanup+cleanup_anchor)
    # Whole code checks accept only the exact authored observer bytes, not an
    # address range mask. Final restoration is before protected pack equality.
    proof=lines('for(const auto&hook:widget_hooks)if(hook.pc<=span.pc','if(!hooked)require(')
    change('if(!hooked)require(',proof+'if(!hooked)require(')
    restore=lines('    for(unsigned i=0;i<3;++i){DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(widget_IATs[i]),4,PAGE_READWRITE,&prior),"GDI IAT restoration protection")','    for(unsigned i=0;i<pages.size();++i)')
    change('    for(unsigned i=0;i<pages.size();++i)if(page_permissions[i]!=2){',restore+'    for(unsigned i=0;i<pages.size();++i)if(page_permissions[i]!=2){')
    raw_iats=lines('            if(0x5bb53c<=pc&&pc<0x5bb540)','            require(actual[byte]==(pc>=capture_pc')
    change('            bool fs_byte=false;',raw_iats+'            bool fs_byte=false;')
    ref=ref.replace('/786 actual original initializer phases','/828 actual original initializer phases');ref=re.sub(r'std::array<void\*,134> pages',f'std::array<void*,{len(records)}> pages',ref)
    ref=ref.replace('MW4J131D','MW4J138D').replace('MW4J131O','MW4J138O').replace('Original131','Original138').replace('full131','full138').replace('Exact101callback','Exact108callback')
    (out/'reference.cpp').write_text(ref)
    broker=text(OLD/'original_broker.hpp');m=re.search(r'inline constexpr std::array<std::uint32_t,\d+> bases\{[^;]+;',broker);need(m is not None,'Exact broker pre-CRT region inventory');bases=[int(v,16)for v in re.search(r'\{([^}]+)\}',m[0])[1].split(',')]
    for p in records:
        if p<0x5f400000 and p&~65535 not in bases:bases.append(p&~65535)
    broker=one(broker,m[0],f'inline constexpr std::array<std::uint32_t,{len(bases)}> bases'+'{'+','.join(hex(v)for v in bases)+'};');(out/'original_broker.hpp').write_text(broker)
    cmake=one(text(OLD/'CMakeLists.txt'),'format_observer_x86.asm boundaries.asm','format_observer_x86.asm widget_observer_x86.asm fps_observer_x86.asm boundaries.asm');(out/'CMakeLists.txt').write_text(cmake)
    # Exhaustive source-patch family audit: additions must never alias any
    # inherited source replay, capture broker or connected MFC hook. Named IAT
    # cells are separately recorded; they are not instruction descriptors.
    hooks=[dict(family='FS',pc=v['PC'],bytes=len(bytes.fromhex(v['raw_bytes'])))for v in fs+add]
    for field,family_name,file_text,implicit_size in(('null_hooks','NULL',ref,5),('vtable_hooks','vtable',ref,None),('lockit_hooks','Lockit',ref,None),('format_hooks','format',text(OLD/'format_observer.hpp'),None),('widget_hooks','GDI',text(FAMILY/'widget_observer.hpp'),None),('connected_patches','MFC1168',text(OLD/'connected_observer.hpp'),None)):
        match=re.search(r'\b'+field+r'\s*\{\{(.*?)\}\};',file_text,re.S);need(match is not None,'Complete actual hook family '+field)
        pattern=r'\{(0x[0-9a-f]+),'+(r'&[^,]+,\{'if implicit_size else r'(\d+),&[^,]+,\{')
        parsed=re.findall(pattern,match[1]);need(parsed,'Nonempty actual hook family '+field)
        for item in parsed:
            pc=int(item if implicit_size else item[0],16);size=implicit_size or int(item[1]);hooks.append(dict(family=family_name,pc=pc,bytes=size))
    hooks.extend([dict(family='FPS',pc=0x5a2f6e,bytes=6),dict(family='capture',pc=0x5ac3f0,bytes=5),dict(family='sentinel',pc=0x5ac3ec,bytes=5)])
    # Sentinel terminal patch precedes and may overlap the otherwise empty
    # capture broker only if the physical constant says so; here they are
    # adjacent distinct windows. Authenticate the actual constant below.
    capture_match=re.search(r'capture_pc=(0x[0-9a-f]+)',text(OLD/'protocol.hpp'));need(capture_match is not None,'Actual declared terminal capture source PC')
    hooks[-2]['pc']=int(capture_match[1],16)
    for i,a in enumerate(hooks):
        for b in hooks[i+1:]:need(a['pc']+a['bytes']<=b['pc']or b['pc']+b['bytes']<=a['pc'],'Zero active source patch overlaps '+str((a,b)))
    iats=dict(GDI=[0x5bb070,0x5bb074,0x5bb068],FPS=[0x5bb53c],formatting=[0x5bb5a8,0x5bb664,0x5bb658],Lockit_API=[0x78146198,0x78146184],registry_API=[0x7802e094,0x7802e090,0x7802e1dc,0x7802e0b4,0x7802e03c,0x7802e044,0x7802e048,0x7802e040])
    for field,cells in iats.items():
        for cell in cells:
            for h in hooks:need(cell+4<=h['pc']or h['pc']+h['bytes']<=cell,'Named IAT cell must not alias source hook')
    for filename,payload in(('selected-order.json',selected),('source-page-union.json',dict(fixed_original=fixed,extra_original=extra,whole=whole)),('fs-hook-bindings.json',fs+add),('source-overlays.json',overlay),('source-deltas.json',deltas),('source-hook-inventory.json',dict(hooks=hooks,named_IAT_cells=iats,zero_active_source_patch_overlaps=True))):(out/filename).write_text(json.dumps(payload,indent=2)+'\n')
    contracts=dict(selected_order=selected,widget_roots=list(ROOTS),widget_phases=list(PHASES),source_frame=0x20001800,sequences=6,phases=828,callbacks=108,whole_source_pages=69,fixed_Record_bytes=356992,original_fixed_pages=43,extra_whole_page_endpoints=26,inherited_FS_bytes=1216,inherited_FS_record_bytes=12,widget_FS_bytes=1224,widget_FS_record_bytes=16,widget_FS_bound=2048,GDI_snapshot_bytes=287444,FPS_snapshot_bytes=550180,GDI_snapshots_bound=384,FPS_snapshots_bound=8,inherited_observer_scope_unchanged=True,new_root_FS_ledger_is_separate=True,actual_GDI_resource_lifecycle_only=True,GetStockObject_borrowed=True,CreateFont_owned_if_actual_nonzero=True,conditional_DeleteObject_actual_only=True,manual_owned_font_cleanup_research_only=True,actual_GDI_DS_ES_SS_descriptors=True,source_selector_effective_limit_validation_pending=True,provider_preinvoked=False,predicted_source_values_supplied=False,per_phase_reseed=False,AFTER_machine_seed=False,initializer_credit=0)
    (out/'contracts.json').write_text(json.dumps(contracts,indent=2)+'\n')
    for p in out.rglob('*'):
        if p.is_file():pin(p)
    pin(R/'tools/m4-startup138-original/prepare.py');pin(R/'tools/m4-capture-direct/capture_direct_v3.cpp');pin(R/'tools/m4-capture-direct/capture_direct_v3.hpp');pin(__file__)
    report=dict(passed=True,scope='Unbuilt authentic chronological original138 preparation, preserving full131 source/domain observations and real seven sorted widget/FPS roots',parent_preparation_path=str(OLD/'report.json'),parent_preparation_sha256=sha(OLD/'report.json'),family_preparation_sha256=sha(FAMILY/'report.json'),native_preparation_sha256=sha(JOINT/'report.json'),original_sequences=6,original_roots=138,original_phases=828,callback_count=108,record_bytes=356992,source_spans=spans,observed_pages=fixed,extra_whole_source_pages=extra,combined_source_page_count=69,sparse_pack_pages=len(records),pack_sha256=sha(out/'pages.bin'),pack_bytes=len(pack),FS_hooks=len(fs)+len(add),selected_order=selected,new_game_source_rows=len(new),source_frame=0x20001800,provider_preinvoked=False,predicted_values_supplied_to_execution=False,source_output_seed=False,original_executed=False,capture_reader_opened=False,writer_admitted=False,initializer_credit=0,contracts=str(out/'contracts.json'),files=files)
    p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files={**files,str(p.resolve()):sha(p)}),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(p),sha256=sha(p),original_roots=138,original_phases=828,whole_source_pages=69)))
if __name__=='__main__':
    try:main(sys.argv[1])
    except Exception as e:
        out=R/'reports/m4-startup138-original'/sys.argv[1]
        if out.is_dir()and not(out/'report.json').exists():
            files={str(p.resolve()):sha(p)for p in out.rglob('*')if p.is_file()}
            (out/'report.json').write_text(json.dumps(dict(passed=False,error=str(e),scope='Failed preparation only; no worker/capture execution',original_executed=False,capture_reader_opened=False,files=files),indent=2)+'\n')
        raise
