"""Independent finite chronological MFC original first-writer admission."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={};COUNTS=Counter()
PSHA='4f3510adc78d8766df79c9cd1c56bd1de754a483444d1caf3015e208f43850e1'
BSHA='d390e05cba9af8c96926d57f983ed985a4ae044a51d6326c593442dea2878fc2'
def need(v,s):
    if not v:raise ValueError(s)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip','.iso'),'No capture/archive consumer')
    v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable input');PINS[str(p)]=v;return p
def raw(p):return pin(p).read_bytes()
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def module(p,name):
    spec=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def sparse(b):
    need(b[:8]==b'MW4J124P','Actual sparse magic');n=struct.unpack_from('<I',b,8)[0];need(len(b)==12+n*4104,'Exact whole sparse page record extent')
    d={}
    for i in range(n):
        a,rights=struct.unpack_from('<2I',b,12+i*4104);need(a%4096==0 and a not in d and rights in(0,1,2),'Unique legacy0RO/1RX/2RW input page');d[a]=(rights,b[20+i*4104:12+(i+1)*4104])
    return d
def main(name):
    out=R/'reports/m4-tree-review'/name;need(re.fullmatch('mfc1168-connected-prelaunch-r[1-9][0-9]*',name)and not out.exists(),'Fresh owned output');out.mkdir();passed=False;links=[]
    try:
        area=R/'reports/m4-mfc1168-connected-original';folder=area/'preparation-r3';bf=area/'build-r2'
        p=read(folder/'report.json',PSHA);b=read(bf/'build.json',BSHA);contracts=read(p['contracts'])
        need(p['passed']and b['passed']and b['preparation_sha256']==PSHA and Path(b['preparation']).resolve()==folder.resolve(),'Current exact prepared/compiler input chain')
        for receipt,key in((p,'files'),(b,'sources'),(read(bf/'pins.json'),'files')):
            for path,digest in receipt[key].items():pin(path,digest)
        parent=read(R/'reports/m4-startup130-original/preparation-r2/report.json',p['parent_original130_preparation_sha256'])
        cached=read(R/'reports/m4-mfc1168-probe/preparation-r10/report.json',p['isolated_MFC_preparation_sha256'])
        cached_review=read(R/'reports/m4-tree-review/mfc1168-original-r1/report.json','ff1d38a87d2ff303902f7757e1a9075ae2215105e771ca90ab548bd7caf0cf01')
        need(parent['passed']and cached['passed']and cached_review['passed'],'Exact current original130 source and separately reviewed cached observer inputs')
        need([b[k]for k in('roots','sequences','phases','record_bytes','pages','external_pages','combined_pages','MFC_boundary_bytes','named_API_boundary_bytes')]==[14,1,14,356992,43,3,46,664,668],'Fixed finite chronology and unchanged source record ABI')
        for key in('original_executed','capture_reader_opened','preinvoked_provider','source_after_seed','predicted_values_supplied_to_observations','initializer_credit'):need(not p[key],'Preparation only '+key)
        need(all(x['exit_code']==0 for x in b['commands']),'Actual complete strict compilation')
        order=contracts['selected_order'];need(order==p['selected_order']and len(order)==14,'Exact declared current selected chronology')
        need(order[:13]==parent['selected_order'][:13]and order[13]==dict(phase=13,slot=0x5e0040,entry=0x5ae3e4),'Exact thirteen current preceding roots then literal1168 slot')
        need(contracts['unaccepted_omitted_slots']==[0x5e0038,0x5e003c]and contracts['source_frame']==contracts['bootstrap_frame']==0x20001800 and contracts['caller_domain']==dict(repeat=0,CW=0x7f,TOP=0),'Explicit finite carried source caller domain')
        PE=module(R/'tools/analysis/pe.py','connected_MFC_PE')
        game=PE.PEImage(raw(R/'MW3/Mech3.exe'));cp=PE.PEImage(raw(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'))
        worker=PE.PEImage(raw(pin(b['worker'],b['worker_sha256'])));need((worker.machine,worker.image_base)==(0x14c,0x18000000),'Actual fixed-base PE32 reference worker')
        nt=struct.unpack_from('<I',worker.data,60)[0];need(worker.image_base+struct.unpack_from('<I',worker.data,nt+80)[0]<0x20000000,'Worker/BSS does not alias actual guest stack')
        def physical(image,pc,n):
            a,_=image.rva_range(pc-image.image_base,n);return image.data[a:a+n]
        pack=sparse(raw(folder/'pages.bin'));old=sparse(raw(R/'reports/m4-startup130-original/preparation-r2/pages.bin'))
        need(len(pack)==p['sparse_pack_pages']and len(raw(folder/'pages.bin'))==p['pack_bytes'],'Whole current sparse carrier')
        graphs=read(R/'reports/m4-mfc1168-original/recovery-r2/game-graphs.json');rows={x['pc']:x for graph in graphs.values()for x in graph['instructions']}
        need(len(rows)==25,'Exact physically recovered new game source')
        declared={}
        for row in rows.values():
            source=bytes.fromhex(row['bytes']);need(physical(game,row['pc'],len(source))==source,'Whole actual game instruction source')
            for i,v in enumerate(source):
                at=row['pc']+i;declared[at]=v;need(pack[at&~4095][1][at&4095]==v,'Complete instruction from sparse BEFORE carrier')
            COUNTS['new_physical_game_rows']+=1
        overlays=[]
        for page,(rights,before)in old.items():
            need(pack[page][0]==rights,'All inherited source page permissions conserved')
            for i,(x,y)in enumerate(zip(before,pack[page][1])):
                if x!=y:need(rights==1 and x==0xcc and declared.get(page+i)==y,'Only exact new physical source bytes replace inherited padding');overlays.append(page+i)
            COUNTS['complete_inherited_page_relations']+=1
        for span in p['source_spans']:
            image=cp if span['origin']else game
            source=physical(image,span['pc'],span['size']);need(image.data[span['image_offset']:span['image_offset']+span['size']]==source,'Complete admitted physical source binding')
            COUNTS['physical_source_span_relations']+=1
        for row in order:need(struct.unpack_from('<I',pack[row['slot']&~4095][1],row['slot']&4095)[0]==row['entry'],'All fourteen physical initializer table slots')
        broker=pin(folder/'original_broker.hpp').read_text();m=re.search(r'array<std::uint32_t,(\d+)> bases\{([^}]+)\}',broker);need(m,'Actual broker base inventory')
        bases=list(map(lambda x:int(x,16),m[2].split(',')));need(len(bases)==int(m[1])and all(page&~65535 in bases for page in pack),'Every complete sparse page has pre-CRT reservation')
        COUNTS['complete_source_page_reservation_relations']=len(pack)
        patches=contracts['active_code_patches'];need(len(patches)==7,'Five game observers plus actual caller and sentinel only')
        for i,span in enumerate(patches):
            for other in patches[i+1:]:need(span['PC']+span['size']<=other['PC']or other['PC']+other['size']<=span['PC'],'All active source instrumentation disjoint')
            if 'raw'in span:need(physical(game,span['PC'],span['size']).hex()==span['raw'],'Complete replayed actual source patch bytes')
        cpp=pin(folder/'reference.cpp').read_text();main_cpp=cpp[cpp.index('int main('):];obs=pin(folder/'connected_observer.hpp').read_text();asm=pin(folder/'reference_x86.asm').read_text()
        need(all(marker not in main_cpp for marker in('for(const auto&hook:fs_hooks)','for(const auto&hook:null_hooks)','for(const auto&hook:vtable_hooks)','for(const auto&hook:format_hooks)','for(const auto&hook:lockit_hooks)')),'Unrelated provider code patches never installed')
        need(main_cpp.index('mixed_input.pc=0x78004482')<main_cpp.index('for(unsigned phase=0;phase<entries.size();++phase)'),'Authentic producer precedes complete selected chronology')
        need(main_cpp.count('if(page_permissions[i]==2)std::memcpy')==1 and 'if(phase){mixed_input=mixed_after;'in main_cpp,'Only once source initialization and actual complete per-root carry')
        need(main_cpp.index('registry_cleanup.restore();connected_named_identity();')<main_cpp.index('named_IAT(true);connected_patch_sources(true);')<main_cpp.index('r->tag.status=execute();')<main_cpp.index('named_IAT(false);connected_patch_sources(false);'),'Producer API shims restored, identities observed, actual source interval patched, then owning IAT/code restored')
        need('std::array<unsigned,3>extras{0x5cd000,0x5e3000,0x5e9000}'in main_cpp and 'module_pages("BEFORE/MFC",0x5f400000,0xed000)'in main_cpp and 'module_pages("BEFORE/CRT",0x78000000,0x40000)'in main_cpp,'Complete carried46 ordinary pages and actual provider regions BEFORE/AFTER')
        for marker in('producer-api-ledger.bin','producer-api-initial/','registry-before','registry-after','TEB-before.bin','TEB-after.bin','connected_lock("BEFORE/CRT-codepage-lock")','connected_lock("AFTER/CRT-codepage-lock")'):
            need(marker in main_cpp,'Current genuine BEFORE and full ownership/TEB/CS24 input '+marker)
        need(contracts['coherent_TEB_raw8192_before_and_after_root']and not contracts['MFC_provider_discovery_precall']and not contracts['source_AFTER_seed'],'No provider helper preinvocation or AFTER input discovery')
        need('service=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(1168))'in main_cpp and 'mbcp=GetProcAddress(crt,"_setmbcp")'in main_cpp and 'require(reinterpret_cast<unsigned>(service)==0x5f401083&&reinterpret_cast<unsigned>(mbcp)==0x78003ddb'in main_cpp,'Actual named/ordinal service ownership without invocation')
        need('for(unsigned i=0;i<4;++i){named_targets[i]=dword(named_cells[i]);'in obs and 'GetModuleHandleExW' in obs and '-owner-metadata.bin'in obs and '-entry64.bin'in obs,'Current real resolved API identity raw evidence prepared')
        need('named_count<64'in obs and 'boundary_count<16'in obs and 'SetLastError(gle)'in obs and 'static_assert(sizeof(Boundary)==664&&sizeof(NamedBoundary)==668)'in obs,'Bounded raw CPU40/FX512/ENV28/frame64 capture and guest LastError restoration')
        need('if(!api_phase)std::memcpy(&named_returns[api_kind],b.frame,4)'in obs and 'api_phase?named_returns[api_kind]:named_targets[api_kind]'in obs,'Exact observed named API return slot projection declared')
        need(asm.count('mov esi,DWORD PTR fs:[18h]')==2 and 'mov mixed_teb_before_base,esi'in asm and 'mov mixed_teb_after_base,esi'in asm and asm.count('mov ecx,2048')==2,'Actual complete coherent raw TEB entry/exit capture')
        need(asm.index('mov mixed_teb_before_base,esi')<asm.index('fxrstor mixed_guest_fx')<asm.index('jmp DWORD PTR mixed_input[36]'),'TEB current-root input captured before source execution')
        need('cmp eax,256\n jae api_ledger_overflow'in asm and main_cpp.index('Bounded producer ledger before export')<main_cpp.index('producer-api-ledger.bin'),'Every actual producer/phase ledger bounded before writes and reads')
        need('original_free(reinterpret_cast<void*>(*crtbegin))'in main_cpp and 'no borrowed manager/TLS/object released'in contracts['callback_cleanup_scope'],'Research cleanup frees only actual owned registry vector')
        C=module(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','connected_MFC_COFFER')
        release=bf/'build-x86/mw34_joint_startup124_original.dir/Release'
        for filename in('reference_x86.obj','boundaries.obj','api_boundaries.obj'):
            sy,secs=C.coff(raw(release/filename));executable=[i for i,s in secs.items()if s['flags']&0x20000000 and s['bytes']];need(len(executable)==1,'Whole single ASM source text')
            idx=executable[0];dummy={0:dict(name=filename+' whole source',value=0,section=idx,type=0x20,storage=2)}
            proof=C.linked_function(worker,dummy,secs,filename+' whole source');links.append(proof)
            COUNTS['whole_linked_assembly_sections']+=1;COUNTS['whole_linked_assembly_bytes']+=proof['bytes'];COUNTS['whole_linked_assembly_relocations']+=len(proof['relocations'])
            if filename!='reference_x86.obj':need(raw(folder/filename.replace('.obj','.asm'))==raw(R/'reports/m4-mfc1168-probe/preparation-r10'/filename.replace('.obj','.asm')),'Exact independently reviewed normal/API observer assembly')
        sy,secs=C.coff(raw(release/'reference.obj'))
        for symbol in('_observe_boundary','_observe_named_API'):
            links.append(C.linked_function(worker,sy,secs,symbol));COUNTS['whole_linked_CPP_observers']+=1
        compiler_log=pin(bf/'compile.log').read_text();need('/MACHINE:X86'in compiler_log and '/W4 /WX'in compiler_log and '0 Warning(s)'in compiler_log and '0 Error(s)'in compiler_log,'Actual strict clean source/ASM compiler and link')
        tlogs=list(release.rglob('CL.read.1.tlog'));need(len(tlogs)==1,'One actual compiler dependency ledger')
        consumed=set()
        for line in pin(tlogs[0]).read_text(encoding='utf-16').splitlines():
            path=Path(line.strip().lstrip('^'))
            if path.is_absolute()and path.is_file():consumed.add(pin(path))
        for name_ in('spec.hpp','protocol.hpp','original_broker.hpp','connected_observer.hpp'):need((folder/name_).resolve()in consumed,'Actual current compiler header '+name_)
        COUNTS['actual_compiler_input_files']=len(consumed)
        runner=pin(R/'tools/m4-mfc1168-connected-original/run.py').read_text()
        need("q['files'].get(str(build.resolve()))!=digest"in runner and "q['files'].get(str(Path(b['worker']).resolve()))!=b['worker_sha256']"in runner and'timeout_seconds=240'in runner,'Exact independent current-build/worker binding required by finite controller')
        pin(R/'tools/m4-pipeline/stages.py');pin(R/'tools/m4-mfc1168-connected-original/prepare_v2.py');pin(R/'tools/m4-mfc1168-connected-original/main_tail_v2.inc');pin(R/'tools/m4-mfc1168-connected-original/observer_tail.inc')
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        pin(__file__);pin(sys.executable);q=out/'compiled-observers.json';q.write_text(json.dumps(links,indent=2)+'\n');pin(q)
        report=dict(passed=passed,preparation_sha256=PSHA,build_sha256=BSHA,counts=dict(COUNTS),files=PINS,roots=14,phases=14,sequences=1,
            archive_reader_opened=False,worker_launched=False,all_bounded_readers_closed=True,initializer_credit=0,
            scope='Independent current chronological original first-writer prelaunch only. Same actual130 loader/producer followed by thirteen exact current selected roots then MFC1168; complete source/pack/reservations/whole compiled observers and carried ownership input preparation reviewed. Actual domain/values/API/CS/TEB/FP/source equality and native/carried-page merge require subsequent measured gates. No prior cached ownership alias or State/AFTER seed is admitted.',
            source_AFTER_seed=False,preinvoked_provider=False,actual_chronological_domain_observed=False,connected_native_acceptance=False)
        q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),files=len(PINS),counts=dict(COUNTS))))
if __name__=='__main__':main(sys.argv[1])
