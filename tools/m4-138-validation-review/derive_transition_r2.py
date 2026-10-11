from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-138-validation-review/diagnose_transition_r1.py'
t=p.read_text().replace("mfc-transition-r1'", "mfc-transition-r2'")
a="    reader_path=pin(ROOT/'tools/m4-crt-allocation-root/run_storage.py')"
z="""    coff_path=pin(ROOT/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py')
    coff_spec=importlib.util.spec_from_file_location('transition_coff',coff_path);coff_module=importlib.util.module_from_spec(coff_spec);coff_spec.loader.exec_module(coff_module)
    for family in ('fs_observer_x86','nullfree_observer_x86'):
        object_path=pin(ROOT/('reports/m4-startup138-original/build-r4/build-x86/mw34_joint_startup124_original.dir/Release/'+family+'.obj'))
        symbols,sections=coff_module.coff(object_path.read_bytes())
        proof=next(row for row in obs if row['family']=='whole-ASM' and row['symbol']==family+' whole source')
        indexes=[i for i,s in sections.items() if s['flags']&0x20000000 and s['bytes']]
        assert len(indexes)==1
        section=indexes[0];assert sections[section]['bytes'].hex()==proof['object_raw_hex']
        for symbol in symbols.values():
            if symbol['section']==section:
                value=proof['address']+symbol['value'];name=symbol['name']
                assert name not in resolutions or resolutions[name]==value
                resolutions[name]=value
    for hook in bindings:
        if hook['PC']>=0x78000000:assert '_'+hook['declared_observer'] in resolutions
    assert '_nullfree_entry_hook' in resolutions and '_nullfree_ret_hook' in resolutions
    reader_path=pin(ROOT/'tools/m4-crt-allocation-root/run_storage.py')"""
assert t.count(a)==1;t=t.replace(a,z)
q=p.with_name('diagnose_transition_r2.py');assert not q.exists();q.write_text(t)
