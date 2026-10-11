"""Current constructor admission with independently resolved MFC/CRT exports."""
from pathlib import Path
import hashlib, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
review_source=R/'tools/m4-tree-review/review_constructor37_prelaunch.py'
assert hashlib.sha256(review_source.read_bytes()).hexdigest()=='b41fb7810010189edba1ebf22f121e5c6d5db18a5adbf556840dad50b63ee67f'
text=review_source.read_text()
changes={
 '75651d2e01281c8bfea102bdf4d8b32649eeff379789afadc1d2079fd6f1d507':'6d3f97e734647085ee51c00538527e3e82ad31880d1310f946839be0e15720a0',
 'bcf2cc5e4c9e197cf99374a47f136fa88db2e6e48fe558bc8ba565628aeeb054':'60e23288b3067cc7d78bbef9e2ca1286c941142a576a781ad7c2ffd2b2a53ac7',
 'chronological-preparation-r4':'chronological-preparation-r7',
 'chronological-build-r2':'chronological-build-r5',
 'permission in(1,2)':'permission in(0,1,2)',
 'address not in oldpack and permission==2':'address not in oldpack and permission in(0,2)',
 "assert 'mov eax,DWORD PTR [ecx+4]'in asm and 'ret'in asm":"assert physical(game,0x40a850,4)==bytes.fromhex('8b4104c3') and ' db 08bh,041h,004h' in asm and ' db 0c3h' in asm",
 "assert 'if(phase<15)constructor_collect' in main_cpp":"assert main_cpp.count('constructor_collect(phase,phase_stem);if(constructor_phase)')==1",
 "for obj in sorted(release.glob('*.obj')):":"for obj in [release/(leaf+'.obj') for leaf in ('reference_x86','boundaries','api_boundaries','preserve_x86','fs_observer_x86','nullfree_observer_x86','vtable_observer_x86','lockit_observer_x86','format_observer_x86','constructor_observer_x86')]:",
 "pin(R/'tools/m4-constructor-original/run.py');pin(__file__);":"pin(review_source);pin(R/'tools/m4-constructor-original/run.py');pin(__file__);",
}
for before,after in changes.items():
 assert before in text,before;text=text.replace(before,after)
before="        C=load(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','ctor37_actual_coff')"
after='''
        chain=read(R/'reports/m4-constructor-original/entry-chain-r1/report.json','80bc3b7041473bd8fb643aa0b5e0839bae1d185659adca2fc802728bcccd18a7')
        assert chain['passed'] and not chain['source_AFTER_seed'] and not chain['new_constructor_reached_path_observed']
        for path,identity in chain['files'].items():pin(path,identity)
        mfc=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes())
        crt=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
        for ordinal in (823,825):
            actual=next(row for row in mfc.exports()if row['ordinal']==ordinal)
            assert 'forwarder'not in actual and actual['rva']+mfc.image_base==chain['MFC_exports'][str(ordinal)]['target']
            assert '==0x%x'%chain['MFC_exports'][str(ordinal)]['target']in main_cpp
            counts['independently_resolved_named_MFC_exports']+=1
        for name in ('malloc','free'):
            actual=next(row for row in crt.exports()if name in row['names'])
            assert 'forwarder'not in actual and actual['rva']+crt.image_base==chain['CRT_named_exports'][name]['target']
            counts['independently_resolved_named_CRT_exports']+=1
        owning={mfc.image_base+s['iat_rva']:(row['library'],s)for row in mfc.imports()for s in row['symbols']}
        for cell,name in ((0x5f49814c,'malloc'),(0x5f498148,'free')):
            library,source=owning[cell];assert library.casefold()=='msvcrt.dll'and source['name']==name
            assert source=={k:v for k,v in chain['MFC_CRT_IAT'][str(cell)].items()if k!='library'}
            assert 'dword(0x%x)==reinterpret_cast<unsigned>(GetProcAddress(crt,"%s"))'%(cell,name)in main_cpp
            counts['independently_resolved_owning_MFC_CRT_cells']+=1
        for ordinal,pc,cell in ((823,0x5abd26,0x5bb4bc),(825,0x5abd1a,0x5bb4c8)):
            assert physical(game,pc,6)==bytes.fromhex('ff25')+struct.pack('<I',cell)
            raw=struct.unpack('<I',physical(game,cell,4))[0];assert raw==0x80000000|ordinal
            counts['physical_game_ordinal_import_cells']+=1
        deltas={}
        for role,value in chain['source_frames'].items():
            current=0
            for row in value['rows']:
                raw=bytes.fromhex(row['bytes_hex']);image=mfc if row['PC']<0x78000000 else crt
                assert raw==physical(image,row['PC'],len(raw))
                if raw[:2]==bytes.fromhex('83ec'):adjustment=-raw[2]
                elif raw[:2]==bytes.fromhex('81ec'):adjustment=-struct.unpack_from('<I',raw,2)[0]
                else:
                    assert (0x50<=raw[0]<=0x57 or raw[0]in(0x68,0x6a,0xe8)or raw[0]==0xff and (raw[1]>>3)&7 in(2,6))
                    adjustment=-4
                current+=adjustment;assert current==row['ESP_delta_after'];counts['whole_physical_source_stack_adjustments']+=1
            assert current==value.get('entry_to_callee_delta',value.get('entry_to_API_delta'));deltas[role]=current
        assert deltas['MFC823_to_malloc']+deltas['CRT_malloc_to_HeapAlloc']==chain['MFC823_entry_to_HeapAlloc_before_delta']==-104
        assert deltas['MFC825_to_free']+deltas['CRT_free_to_HeapFree']==chain['MFC825_entry_to_HeapFree_before_delta']==-80
        for role,key in (('CRT_malloc_to_HeapAlloc','HeapAlloc_source_saved_return'),('CRT_free_to_HeapFree','HeapFree_source_saved_return')):
            last=chain['source_frames'][role]['rows'][-1];assert last['PC']+len(bytes.fromhex(last['bytes_hex']))==chain[key]
        assert contract['source_MFC_entry_chain_sha256']=='80bc3b7041473bd8fb643aa0b5e0839bae1d185659adca2fc802728bcccd18a7'
        assert contract['source_MFC_entry_target']==chain['MFC_exports']['823']['target'] and contract['source_MFC_release_target']==chain['MFC_exports']['825']['target']
        assert 'out.append("constructor/provider-entries.bin",ctor_named_entries.data(),sizeof(ctor_named_entries))'in cpp
        C=load(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','ctor37_actual_coff')
'''
assert text.count(before)==1;text=text.replace(before,after)
exec(compile(text,str(review_source),'exec'),globals())
