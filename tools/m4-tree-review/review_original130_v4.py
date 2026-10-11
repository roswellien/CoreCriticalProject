"""Independent bounded original130 prelaunch schedule/source/COFF review."""
import collections, importlib.util, json, re, struct, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
import review_connected125_v2 as C
import review_formatting_observers as W
def module(p,name):
    s=importlib.util.spec_from_file_location(name,C.pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main(name):
    out=R/'reports/m4-tree-review'/name;C.need(not out.exists(),'Fresh independent original130 review');out.mkdir(parents=True)
    passed=False;counts=collections.Counter();attributions=[]
    try:
        for p in (__file__,C.__file__,W.__file__):C.pin(p)
        area=R/'reports/m4-startup130-original'; prepdir=area/'preparation-r1';builddir=area/'build-r1'
        p=C.read(prepdir/'report.json','89e159e71b3ae0a367bb33ee32c161cccae1aea45c005c2498c7e4e6ffb51af6')
        b=C.read(builddir/'build.json','f1d29a95e80d91d282017339e0c7afd4676725f516b7b4e03b9c6e94d294d872')
        C.need(p['passed'] and b['passed'] and b['preparation_sha256']==C.PINS[str((prepdir/'report.json').resolve())] and not b['original_executed'] and not p['initializer_credit'],'Exact current unexecuted genuine preparation/build')
        for q,h in (p['files']|b['sources']).items():
            path=Path(q);C.need(path.suffix not in ('.mwb','.zip'),'No inherited capture archive');C.pin(path,h)
        PE=module(R/'tools/analysis/pe.py','original130_review_PE');COFF=module(R/'tools/m4-fs-source/observer_attribution.py','original130_review_COFF');L=module(R/'tools/m4-lockit-review/full_original_review.py','original130_review_CP')
        game=PE.PEImage(C.pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        crt=PE.PEImage(C.pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes());mfc=PE.PEImage(C.pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL').read_bytes());cp=PE.PEImage(C.pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL').read_bytes())
        def physical(image,a,n):return image.read(image.rva_range(a-image.image_base,n)[0],n)
        original=C.read(R/'reports/m4-tree-original/original125-preparation-r1/report.json')
        C.need(C.PINS[str((R/'reports/m4-tree-original/original125-preparation-r1/report.json').resolve())]==p['parent_preparation_sha256'],'Exact accepted125 original preparation')
        old=list(zip(original['table_slots'],original['entries'])) if 'entries' in original else [(r['slot'],r['entry'])for r in original['selected_order']]
        order=p['selected_order'];added={(0x5e0160,0x4b64f0),(0x5e01c8,0x4df610),(0x5e01cc,0x4e0710),(0x5e01d0,0x4e0810),(0x5e01d4,0x4e1ca0)}
        pairs=[(r['slot'],r['entry'])for r in order]
        C.need(len(order)==130 and [r['phase']for r in order]==list(range(130)) and pairs==sorted(pairs) and [r for r in pairs if r not in added]==old and set(pairs)-set(old)==added,'Physical complete130 relative-order preserves every125 root and adds exact5')
        for slot,entry in pairs:C.need(struct.unpack('<I',physical(game,slot,4))[0]==entry,'Every root slot physically belongs to game table');counts['physical_table_pairs']+=1
        for row in p['source_spans']:
            image=(game,cp)[row['origin']];a=row['pc'];n=row['size'];off=row['image_offset']
            C.need(image.data[off:off+n]==physical(image,a,n),'Every exact source PC/file-offset span');counts['physical_source_rows']+=1;counts['physical_source_bytes']+=n
        C.need((p['original_sequences'],p['original_roots'],p['original_phases'],p['callback_count'],p['record_bytes'],p['ordinary_record_pages'],p['combined_source_page_count'],p['FS_hooks'])==(6,130,780,101,356992,43,46,63),'Exact immutable original ABI/count scope')
        C.need(p['extra_whole_source_pages']==[0x5cd000,0x5e3000,0x5e9000] and len(set(p['observed_pages']))==43 and not(set(p['observed_pages'])&set(p['extra_whole_source_pages'])),'Exactly3 external whole pages in addition to fixed43')
        reference=C.pin(prepdir/'reference.cpp').read_text();observer=C.pin(prepdir/'format_observer.hpp').read_text();protocol=C.pin(prepdir/'protocol.hpp').read_text()
        C.need(observer.index('if(fs_phase_root!=0x4df610')<observer.index('const auto last_error'),'Outside-four-root observer stutters before host operations')
        C.need('mixed_owner_heaps[e.index]=registry_API_ledger[ai].args[0]'in reference and 'std::memcpy(mixed_owner_initial[e.index],registry_initial_bytes[ai],capacity)'in reference and 'mixed_owner_initial[a.index],a.capacity'in reference,'Whole mixed owner heap/initial input copied at actual API return and persists across ledger reset')
        C.need(reference.index('Actual original registry producer CALL/RET')<reference.index('install_format_hooks();')<reference.index('for(unsigned phase=0;phase<entries.size();'), 'New global IAT hooks installed only after genuine producer bootstrap')
        restore=reference.index('for(const auto&hook:format_hooks){DWORD prior{},ignored{};require(VirtualProtect',reference.index('for(unsigned phase=0;phase<entries.size();'))
        C.need(restore<reference.index('remove_CRT_hooks();',restore)<reference.index('\"/mixed-owner-count.bin\"',restore),'Format hooks/IAT and inherited observer restoration precede actual positive cleanup')
        C.need('registry_cleanup.restore();'in reference,'Registry source cells restored before cleanup')
        C.need('sequences=6'in protocol.replace(' ','') and 'roots=130'in protocol.replace(' ',''),'Exactly6 literal full sequence domains')
        worker=PE.PEImage(C.pin(b['worker'],b['worker_sha256']).read_bytes()); release=builddir/'build-x86/mw34_joint_startup124_original.dir/Release'
        def linked(expected,rel):
            omitted={i for x,_,_ in rel for i in range(x,x+4)};runs=[];start=None
            for i in range(len(expected)+1):
                if i<len(expected) and i not in omitted:
                    if start is None:start=i
                elif start is not None:runs.append((start,i-start));start=None
            anchor,size=max(runs,key=lambda z:z[1]);needle=expected[anchor:anchor+size];hits=[];cursor=0
            while True:
                k=worker.data.find(needle,cursor)
                if k<0:break
                cursor=k+1;j=k-anchor
                if j<0 or j+len(expected)>len(worker.data):continue
                raw=worker.data[j:j+len(expected)]
                if all(i in omitted or raw[i]==expected[i]for i in range(len(expected))):hits.append((j,raw))
            C.need(len(hits)==1,'Unique whole relocation-aware final worker function')
            offset,raw=hits[0];sec=next(s for s in worker.sections if s['raw_offset']<=offset< s['raw_offset']+s['raw_size']);target=worker.image_base+sec['virtual_address']+offset-sec['raw_offset'];normal=bytearray(raw);bindings=[]
            for x,symbol,t in rel:
                addend=struct.unpack_from('<I',expected,x)[0];v=struct.unpack_from('<I',raw,x)[0];address=(v-addend if t==6 else target+x+4+v-addend)&0xffffffff;normal[x:x+4]=expected[x:x+4];bindings.append(dict(offset=x,symbol=symbol,type=t,target=address))
                C.need(t in (6,20),'Only exact i386 DIR32/REL32 compiled observer relocation')
            C.need(bytes(normal)==expected,'Every whole final linked observer byte');return target,bindings
        def function(obj,symbol,expected,rel,family,pc):
            symbols,sections=COFF.parse_coff(C.pin(release/obj).read_bytes());d=next(x for x in symbols.values()if x['name']==symbol and x['section']>0);sec=sections[d['section']]
            C.need(sec['bytes'][d['value']:d['value']+len(expected)]==expected and [(o-d['value'],n,t)for o,n,t in sec['relocations']if d['value']<=o<d['value']+len(expected)]==rel,'Entire independently generated compiled observer and all relocations')
            target,bindings=linked(expected,rel);attributions.append(dict(family=family,source_PC=pc,symbol=symbol,target=target,bytes=len(expected),bindings=bindings));counts[family+'_functions']+=1;counts[family+'_bytes']+=len(expected);counts[family+'_relocations']+=len(rel);return target
        fs=C.read(prepdir/'fs-hook-bindings.json');C.need(len(fs)==63 and len({r['PC']for r in fs})==63,'Exact unique normal FS source points')
        for row in fs:
            raw=bytes.fromhex(row['raw_bytes']);C.need(physical(crt if row['PC']>=0x78000000 else game,row['PC'],len(raw))==raw,'Exact FS source instruction')
            expected,rel,_=COFF.expected_function(row['PC'],row['kind'],raw);target=function('fs_observer_x86.obj','_'+row['declared_observer'],expected,rel,'FS',row['PC'])
            key=struct.pack('<3I',row['PC'],row['continuation'],target);C.need(worker.data.count(key)==1,'Unique exact final FS initializer target')
        for index,(kind_,entry,returned,replay)in enumerate((('strrchr',0x780264a9,0x4dea1b,'83c4088bf0'),('malloc',0x780012b3,0x4deab7,'83c4048bf8'),('sprintf',0x78022b9a,0x4dead7,'83c4108bc75f5e'))):
            for kind,pc,raw in ((2*index,entry,b''),(2*index+1,returned,bytes.fromhex(replay))):
                expected,rel=W.expected(pc,kind,index,raw);target=function('format_observer_x86.obj','_format_'+('return_'if kind&1 else'entry_')+kind_,expected,rel,'format',pc)
                if kind&1:
                    C.need(physical(game,pc,len(raw))==raw,'Literal formatter caller replay bytes');key=struct.pack('<3I',pc,len(raw),target)+raw;C.need(worker.data.count(key)==1,'Unique exact final formatter return initializer target')
        bindings=C.read(R/'reports/m4-lockit-original/original-preparation-r4/lockit-hook-bindings.json')
        for row in bindings:
            pc=row['pc'];expected,rel=L.expected_lockit(pc,row['kind'],bytes.fromhex(row['replay']), '_lockit_continue_'+format(pc,'x')if row['continuation']else None);function('lockit_observer_x86.obj','_'+row['name'].replace('probe_','lockit_'),expected,rel,'Lockit',pc)
        for kind,name_ in ((1,'Enter'),(3,'Leave')):
            expected,rel=L.expected_lockit(0,kind,target='_lockit_actual_'+name_);function('lockit_observer_x86.obj','_lockit_api_'+name_,expected,rel,'Lockit',0)
        C.need(counts['FS_functions']==63 and counts['format_functions']==6 and counts['Lockit_functions']==6,'Complete current observer inventory')
        passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        (out/'compiled-observers.json').write_text(json.dumps(attributions,indent=2)+'\n')
        report=dict(passed=passed,scope='Independent light original130 prelaunch source/schedule and complete compiled/final-linked observer inventory; no execution credit',counts=dict(counts),preparation_sha256='89e159e71b3ae0a367bb33ee32c161cccae1aea45c005c2498c7e4e6ffb51af6',build_sha256='f1d29a95e80d91d282017339e0c7afd4676725f516b7b4e03b9c6e94d294d872',capture_archives_opened=0,live_hook_pages_observed=False,original_executed=False,native_executed=False,initializer_credit=0,files=C.PINS)
        target=out/'report.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=C.hashlib.sha256(target.read_bytes()).hexdigest(),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
