"""Whole physical/source/compiled admission for the original 138-root worker.

Reads ordinary immutable inputs only. Actual execution, selector domains,
source comparisons and carried initializer acceptance are separate gates.
"""
from pathlib import Path
from collections import Counter
import hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
PH = 'e3d4cf14f17132d4dcf08bbef503711820b2f095f0ec52aedff27d088ef8d3c2'
BH = '748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69'
ROOTS = (0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0)
PHASES = (15,16,17,47,134,135,136)


def main(name):
    out = R / 'reports/m4-tree-review' / name
    assert not out.exists()
    out.mkdir()
    pins, counts, links = {}, Counter(), []
    passed = False

    def pin(p, expected=None):
        p = Path(p).resolve()
        assert p.suffix.lower() not in ('.mwb','.zip')
        with p.open('rb') as f:
            h = hashlib.file_digest(f,'sha256').hexdigest()
        assert expected is None or expected == h, (p,expected,h)
        assert str(p) not in pins or pins[str(p)] == h
        pins[str(p)] = h
        return p

    def read(p, expected=None):
        return json.loads(pin(p,expected).read_bytes())

    def module(p,n):
        spec = importlib.util.spec_from_file_location(n,pin(p))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def sparse(p,h):
        data = pin(p,h).read_bytes()
        assert data[:8] == b'MW4J124P'
        count = struct.unpack_from('<I',data,8)[0]
        assert len(data) == 12 + count*4104
        rows = {}
        for i in range(count):
            page,perm = struct.unpack_from('<2I',data,12+i*4104)
            assert not page%4096 and page not in rows and perm in (0,1,2)
            rows[page] = (perm,bytearray(data[20+i*4104:4116+i*4104]))
        return rows

    try:
        folder = R/'reports/m4-startup138-original/preparation-r7'
        bf = R/'reports/m4-startup138-original/build-r4'
        oldfolder = R/'reports/m4-startup131-original/preparation-r4'
        familyfolder = R/'reports/m4-fps-original/preparation-r1'
        p,b = read(folder/'report.json',PH),read(bf/'build.json',BH)
        old = read(oldfolder/'report.json','1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb')
        family = read(familyfolder/'report.json','7c2aea9d60270b768b1c9ecdd63ed7f2898decfa72f5536c43151e7b7e1278a1')
        prior_review = read(R/'reports/m4-tree-review/original131-prelaunch-r4/report.json','e5a09a7c7771c0c7f99cc907000ca999903e21b87d1342160684f237452608ed')
        assert all(v['passed'] for v in (p,b,old,family,prior_review))
        for d,key in ((p,'files'),(b,'sources'),(read(bf/'pins.json'),'files')):
            for q,h in d[key].items():
                pin(q,h)
        assert b['preparation_sha256'] == PH and Path(b['preparation']) == folder
        assert all(c['exit_code']==0 for c in b['commands'])
        assert (p['original_roots'],p['original_sequences'],p['original_phases'],p['callback_count'],p['record_bytes'],p['source_frame']) == (138,6,828,108,356992,0x20001800)
        for key in ('provider_preinvoked','predicted_values_supplied_to_execution','source_output_seed','original_executed','capture_reader_opened','writer_admitted','initializer_credit'):
            assert not p[key], key
        assert p['observed_pages'] == old['observed_pages'] and len(p['observed_pages']) == 43
        whole = p['observed_pages'] + p['extra_whole_source_pages']
        assert len(whole) == len(set(whole)) == 69
        joint = read(R/'reports/m4-joint-startup138/preparation-r4/report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a')
        assert p['selected_order'] == joint['selected_order']
        selected = p['selected_order']
        assert tuple(selected[i]['entry'] for i in PHASES) == ROOTS
        assert [r for r in selected if r['entry'] not in ROOTS] == old['selected_order']
        native_pages = read(R/'reports/m4-joint-startup138/preparation-r4/source-page-union.json')['union']
        assert set(whole) == set(native_pages)
        PE = module(R/'tools/analysis/pe.py','original138_physical')
        game = PE.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        cp = PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())

        def physical(image,a,n):
            off,_ = image.rva_range(a-image.image_base,n)
            return image.data[off:off+n]

        actual_pack = sparse(folder/'pages.bin',p['pack_sha256'])
        expected_pack = sparse(oldfolder/'pages.bin',old['pack_sha256'])
        family_pack = sparse(familyfolder/'pages.bin',family['pack_sha256'])
        assert len(expected_pack) == 134 and len(actual_pack) == 161
        for page,value in family_pack.items():
            if page not in expected_pack:
                expected_pack[page] = value
                counts['whole_family_added_sparse_pages'] += 1
            else:
                assert expected_pack[page][0] == value[0]
                if value[0] == 2:
                    assert expected_pack[page][1] == value[1]
        known = {r['pc']:r for r in old['source_spans']}
        new,overlays = [],[]
        for row in family['source_spans']:
            if row['pc'] in known:
                assert known[row['pc']] == row
                continue
            assert row['origin'] == 0
            source = physical(game,row['pc'],row['size'])
            for i,value in enumerate(source):
                a = row['pc']+i
                page,offset = a&~4095,a&4095
                if page not in expected_pack:
                    expected_pack[page]=(1,bytearray(b'\xcc'*4096))
                perm,data = expected_pack[page]
                assert perm == 1 and data[offset] in (0xcc,value)
                if data[offset] != value:
                    overlays.append(dict(address=a,before=data[offset],after=value,source_PC=row['pc']))
                data[offset]=value
            new.append(row)
            known[row['pc']] = row
        assert len(new)==1060 and p['source_spans']==old['source_spans']+new
        assert overlays == read(folder/'source-overlays.json') and len(overlays)==1594
        assert expected_pack == actual_pack
        counts['whole_reconstructed_sparse_pages'] = len(actual_pack)
        counts['exact_physical_RX_padding_overlay_bytes'] = len(overlays)
        for row in p['source_spans']:
            image = cp if row['origin'] else game
            source = physical(image,row['pc'],row['size'])
            assert image.data[row['image_offset']:row['image_offset']+row['size']] == source
            if not row['origin']:
                assert all(actual_pack[(row['pc']+i)&~4095][1][(row['pc']+i)&4095]==v for i,v in enumerate(source))
            counts['whole_physical_source_spans'] += 1
        for row in selected:
            assert physical(game,row['slot'],4)==struct.pack('<I',row['entry'])
            assert struct.unpack_from('<I',actual_pack[row['slot']&~4095][1],row['slot']&4095)[0]==row['entry']
            counts['physical_selected_initializer_cells'] += 1

        def text(q): return pin(q).read_text(encoding='utf-8-sig')
        cpp = text(folder/'reference.cpp')
        delta = read(folder/'source-deltas.json')
        assert len(delta)==24 and all(set(r)=={'before','after'} for r in delta)
        def normalize(s):
            for a,z in (('/828 actual original initializer phases','/786 actual original initializer phases'),('std::array<void*,161> pages','std::array<void*,134> pages'),('MW4J138D','MW4J131D'),('MW4J138O','MW4J131O'),('Original138','Original131'),('full138','full131'),('Exact108callback','Exact101callback')):
                s=s.replace(a,z)
            return s
        inverted=normalize(cpp)
        for row in reversed(delta):
            a,z=normalize(row['after']),normalize(row['before'])
            assert inverted.count(a)==1, row['before'][:80]
            inverted=inverted.replace(a,z,1)
        assert inverted==text(oldfolder/'reference.cpp')
        counts['whole_explicit_original_CPP_delta_inversion']=1
        assert text(folder/'protocol.hpp') == text(oldfolder/'protocol.hpp').replace('sequences=6, roots=131','sequences=6, roots=138').replace('memory_size==151552','memory_size==176128')
        for fn in ('connected_observer.hpp','prerequisite_observer.hpp','format_observer.hpp','reference_x86.asm','boundaries.asm','api_boundaries.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','format_observer_x86.asm'):
            assert pin(folder/fn).read_bytes()==pin(oldfolder/fn).read_bytes()
            counts['whole_unchanged_accepted131_observers'] += 1
        for fn,size,oldsize in (('widget_observer.hpp',287444,266964),('fps_observer.hpp',550180,529700)):
            assert text(folder/fn)==text(familyfolder/fn).replace(',pages[64*4096]',',pages[69*4096]').replace('=='+str(oldsize),'=='+str(size))
            counts['whole_exact_family_observer_geometry_deltas'] += 1
        for fn in ('widget_observer_x86.asm','fps_observer_x86.asm'):
            assert pin(folder/fn).read_bytes()==pin(familyfolder/fn).read_bytes()
            counts['whole_unchanged_family_ASM_sources'] += 1
        fs,oldfs,familyfs=read(folder/'fs-hook-bindings.json'),read(oldfolder/'fs-hook-bindings.json'),read(familyfolder/'fs-hook-bindings.json')
        added=[r for r in familyfs if r['PC'] not in {v['PC'] for v in oldfs}]
        assert fs==oldfs+added and len(fs)==93 and len(added)==30
        asm=text(oldfolder/'fs_observer_x86.asm')
        declarations,definitions=[],[]
        for row in added:
            n=row['declared_observer']
            matches=re.findall(r'PUBLIC '+n+r'\n'+n+r' PROC\n.*?'+n+r' ENDP\n',text(familyfolder/'fs_observer_x86.asm'),re.S)
            assert len(matches)==1
            declarations.append('EXTERN fs_continue_%x:DWORD'%row['PC'])
            definitions.append(matches[0])
        assert text(folder/'fs_observer_x86.asm')==asm.replace('.code\n','\n'.join(declarations)+'\n.code\n',1).replace('END\n',''.join(definitions)+'END\n',1)
        for row in fs:
            raw=bytes.fromhex(row['raw_bytes'])
            assert physical(game,row['PC'],len(raw))==raw and row['continuation']==row['PC']+len(raw)
            counts['whole_physical_FS_hook_spans']+=1
        inventory=read(folder/'source-hook-inventory.json')
        hooks=sorted(inventory['hooks'],key=lambda x:x['pc'])
        assert inventory['zero_active_source_patch_overlaps']
        assert all(a['pc']+a['bytes']<=z['pc'] for a,z in zip(hooks,hooks[1:]))
        for row in hooks:
            physical(game,row['pc'],row['bytes'])
            counts['disjoint_active_source_patch_spans']+=1
        broker=text(folder/'original_broker.hpp')
        oldbroker=text(oldfolder/'original_broker.hpp')
        pat=r'bases\{([^;]+)\};'
        bases=[int(v,16) for v in re.search(pat,broker)[1].split(',')]
        assert len(bases)==len(set(bases)) and all(page&~65535 in bases for page in actual_pack)
        assert re.sub(r'std::array<unsigned,\d+> bases\{[^;]+\};','BASES',broker)==re.sub(r'std::array<unsigned,\d+> bases\{[^;]+\};','BASES',oldbroker)
        contracts=read(folder/'contracts.json')
        assert (contracts['whole_source_pages'],contracts['inherited_FS_bytes'],contracts['inherited_FS_record_bytes'],contracts['widget_FS_bytes'],contracts['widget_FS_record_bytes'])==(69,1216,12,1224,16)
        assert contracts['source_selector_effective_limit_validation_pending']
        assert contracts['manual_owned_font_cleanup_research_only'] and not contracts['AFTER_machine_seed'] and not contracts['per_phase_reseed']
        main_cpp=cpp[cpp.index('int main('):]
        for token in ('Genuine named GDI export','Actual GDI forwarder owner','Actual GDI module path','Actual GDI named target before observer','GDI named IAT restored','fps/identity.bin','registry-before-backing.bin','/CRT-before/','/CRT-after/','/extra-before/','/extra-after/','widget-fs-events.bin','WidgetFsEvent','constructor_graph(phase_stem+"/BEFORE-MFC")','constructor_graph(phase_stem+"/AFTER-MFC")','Exact108callback vector extent'):
            assert token in cpp,token
        assert main_cpp.count('if(page_permissions[i]==2)std::memcpy')==1
        assert main_cpp.index('mixed_input.pc=0x78004482')<main_cpp.index('for(unsigned phase=0;phase<entries.size();++phase)')
        assert main_cpp.index('registry-before-backing.bin')<main_cpp.index('r->tag.status=execute();')
        assert main_cpp.index('r->tag.status=execute();')<main_cpp.index('/CRT-after/')
        for handler in ('nullfree_observe','vtable_observe'):
            assert 'void '+handler+'(){\n if(std::find(widget_selected_roots.begin(),widget_selected_roots.end(),fs_phase_root)!=widget_selected_roots.end())return;' in cpp

        C=module(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','original138_coff')
        worker=PE.PEImage(pin(b['worker'],b['worker_sha256']).read_bytes())
        assert worker.machine==0x14c and worker.image_base==0x18000000
        release=bf/'build-x86/mw34_joint_startup124_original.dir/Release'
        for file in ('reference_x86','boundaries','api_boundaries','preserve_x86','fs_observer_x86','nullfree_observer_x86','vtable_observer_x86','lockit_observer_x86','format_observer_x86','widget_observer_x86','fps_observer_x86'):
            sy,se=C.coff(pin(release/(file+'.obj')).read_bytes())
            indexes=[i for i,s in se.items() if s['flags']&0x20000000 and s['bytes']]
            assert len(indexes)==1
            fake={0:dict(name=file+' whole source',value=0,section=indexes[0],type=0x20,storage=2)}
            proof=C.linked_function(worker,fake,se,file+' whole source')
            links.append(dict(proof,family='whole-ASM'))
            counts['whole_linked_ASM_sections']+=1
            counts['whole_linked_ASM_bytes']+=proof['bytes']
        sy,se=C.coff(pin(release/'reference.obj').read_bytes())
        exact={'_main','_observe_boundary','_observe_named_API','_widget_fs_observe_before','_widget_fs_observe_after','_fs_observe_before','_fs_observe_after','_nullfree_observe','_vtable_observe','_widget_observe','_fps_observe'}
        names=[s['name'] for s in sy.values() if s['section']>0 and s['type']==0x20 and (s['name'] in exact or s['name'].startswith(('?constructor_dump@@','?constructor_live@@','?constructor_capacity@@','?constructor_collect@@','?constructor_graph@@','?widget_cleanup_resource@@')))]
        assert len(names)==len(set(names))==17 and exact<=set(names)
        for n in names:
            proof=C.linked_function(worker,sy,se,n)
            links.append(dict(proof,family='CPP'))
            counts['whole_linked_CPP_functions']+=1
        targets={r['symbol']:r['address'] for r in links if r['family']=='CPP'}
        resolutions={}
        for row in links:
            for rel in row['relocations']:
                if rel['symbol_section']!=0 or rel['resolution_kind']!='virtual address':
                    continue
                n,a=rel['symbol'],rel['actual_symbol_address']
                assert n not in resolutions or resolutions[n]==a,(n,resolutions.get(n),a)
                resolutions[n]=a
                if n in targets:
                    assert targets[n]==a
                    counts['actual_compiled_observer_target_joins']+=1
        counts['actual_external_symbol_identities']=len(resolutions)
        consumed=set()
        tlogs=list(release.rglob('CL.read.1.tlog'))
        assert len(tlogs)==1
        for line in pin(tlogs[0]).read_text(encoding='utf-16').splitlines():
            q=Path(line.strip().lstrip('^'))
            if q.is_absolute() and q.is_file(): consumed.add(pin(q))
        assert all((folder/f).resolve() in consumed for f in ('spec.hpp','protocol.hpp','connected_observer.hpp','prerequisite_observer.hpp','format_observer.hpp','original_broker.hpp','widget_observer.hpp','fps_observer.hpp'))
        counts['actual_consumed_compiler_inputs']=len(consumed)
        log=text(bf/'compile.log')
        assert '/MACHINE:X86' in log and '/W4 /WX' in log and '0 Warning(s)' in log and '0 Error(s)' in log
        pin(R/'tools/m4-startup138-original/prepare_v4.py')
        pin(R/'tools/m4-startup138-original/run_v2.py')
        pin(__file__)
        pin(sys.executable)
        for q,h in list(pins.items()): pin(q,h)
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        q=out/'compiled-observers.json'
        q.write_text(json.dumps(links,indent=2)+'\n')
        pin(q)
        d=dict(passed=passed,scope='Independent current original138 physical/whole source/link admission. Manual original fonts use actual ascending-index research cleanup; native reverse cleanup is a separate seam. Actual selectors, original/source/pair equality, refusal controls and carried144 acceptance remain pending.',preparation_sha256=PH,build_sha256=BH,counts=dict(counts),worker_launched=False,capture_archive_reader_opened=False,initializer_credit=0,files=pins)
        q=out/'report.json'
        q.write_text(json.dumps(d,indent=2)+'\n')
        print(json.dumps(dict(passed=passed,path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),counts=dict(counts))),flush=True)


if __name__=='__main__':main(sys.argv[1])
