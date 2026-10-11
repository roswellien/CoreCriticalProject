"""Prepare a full138 persistent source comparer, without reading captures."""
from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
PARENT = 'e520d40b74a9e32dbe8102ebf892f3fd76139ae16d7622c2fdd6713eb520b86d'
NATIVE = '2203162c6c12c3f4c4b35009c39f2ddaaf52bea3abca9a8823d36237d7f0a4f6'
PREP = 'a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a'

def main(name):
    out = R/'reports/m4-joint-startup138-source'/name
    assert not out.exists(); out.mkdir(parents=True)
    pins = {}; changes = []
    def pin(path, expected=None):
        path = Path(path).resolve(); assert path.suffix.lower() not in ('.mwb','.zip')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert expected is None or digest == expected, str(path)
        assert str(path) not in pins or pins[str(path)] == digest
        pins[str(path)] = digest; return path
    def read(path, expected=None):
        return json.loads(pin(path, expected).read_bytes())
    parent = read(R/'reports/m4-joint-startup131-source/combined-source-provider-r2/report.json',PARENT)
    native = read(R/'reports/m4-joint-startup138-root/execution-r3/report.json',NATIVE)
    prep_path = R/'reports/m4-joint-startup138/preparation-r4/report.json'
    prep = read(prep_path,PREP)
    gdi_preparation = read(R/'reports/m4-widget-growth-review/persistent-gdi-preparation-r2/report.json',
        'bf18a74560d29a10a373fd6244bb9367393386b85cbb51084020f1383c5e5bc2')
    assert gdi_preparation['passed']
    pin(R/'tools/m4-widget-growth-review/persistent_gdi.py','c7815d110a92f164dbee0a2f8ccd4cee2d0097c7a1c03e9fa3c183ad24178d73')
    pin(R/'tools/m4-widget-growth-review/gdi_identity.py')
    assert parent['passed'] and native['passed'] and native['all_workers_terminal'] and native['all_bounded_readers_closed']
    assert prep['passed'] and len(prep['selected_order']) == 138
    page_path = prep_path.parent/'source-page-union.json'; pages = read(page_path)
    assert len(pages['fixed']) == 17 and len(pages['extra']) == 52 and len(pages['union']) == 69
    main_parent = pin(R/'tools/m4-joint-startup131/compare_provider_v6.py')
    assert str(main_parent) in parent['files'] and pins[str(main_parent)] == parent['files'][str(main_parent)]
    source = main_parent.read_text()
    def one(old,new,label):
        nonlocal source
        assert source.count(old) == 1,(label,source.count(old))
        source = source.replace(old,new)
        changes.append(dict(label=label,before=old,after=new))
    one("ROOT=Path(__file__).resolve().parents[2]", "ROOT=Path(__file__).resolve().parents[3]", 'Generated comparer remains bound to workspace root')
    one("sys.path.insert(0,str(ROOT/'tools/m4-joint-startup131'));", "sys.path.insert(0,str(Path(__file__).resolve().parent));sys.path.insert(0,str(ROOT/'tools/m4-joint-startup138'));sys.path.insert(0,str(ROOT/'tools/m4-widget-growth-review'));sys.path.insert(0,str(ROOT/'tools/m4-joint-startup131'));", 'Current helpers before unchanged inherited source modules')
    one('import continuity131 as A','import continuity138 as A','Complete current138 continuity')
    one('import final_observer130_v2 as F','import final_observer138_v2 as F\nimport persistent_widgets as PW\nimport persistent_gdi as PG\nimport flag_domain as GDIF\nimport gdi_identity as GI','Current complete provider observer and finite GDI source adapter')
    old_pages = 'PAGES=LEGACY_PAGES+(0x5cd000,0x5e3000,0x5e9000)'
    tree = ast.parse(source)
    constants = [node for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id in ('LEGACY_PAGES','PAGES') for target in node.targets)]
    namespace = {}; exec(compile(ast.Module(body=constants,type_ignores=[]),'constants','exec'),namespace)
    fresh = sorted(set(pages['union'])-set(namespace['PAGES']))
    assert len(fresh) == 23 and set(namespace['PAGES']) <= set(pages['union'])
    one(old_pages,old_pages+'+('+','.join(hex(p) for p in fresh)+',)','Preserve exact first43 numeric page order and all69 current pages')
    one("out=ROOT/'reports/m4-joint-startup131-source'/name", "out=ROOT/'reports/m4-joint-startup138-source'/name", 'Fresh output namespace')
    one('provider_scope_rows=[];executed_lineage={};loader_rows=[];flag_rows=[];paired_exports=[];', 'provider_scope_rows=[];executed_lineage={};loader_rows=[];flag_rows=[];paired_exports=[];widget_rows=[];widget_cleanup_rows=[];', 'Retain full current widget derivations')
    one("need(nr['passed'],'All current actual native130 sequences complete')", "need(nr['passed'] and nr['all_workers_terminal'] and nr['all_bounded_readers_closed'],'Both current138 actual/structural workers terminal and readers closed');need(sha(native_report)=='"+NATIVE+"','Exact current admitted138 execution')", 'Bind current actual closed positive execution')
    one("len(joint131['selected_order'])==131", "len(joint131['selected_order'])==138", 'Current physically prepared schedule count')
    one("parent_native=pin(Path(joint131['native_library']).parent/'report.json','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3');", "parent_native=pin(ROOT/'reports/m4-formatting-native/preparation-r19/report.json','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3');service_path=pin(Path(joint131['native_library']).parent/'report.json','cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9');", 'Preserve actual inherited provider and additive two-guard service relation')
    one('inherited_native_preparation_sha256=sha(parent_native))', 'inherited_native_preparation_sha256=sha(parent_native),current_service_preparation=str(service_path),current_service_preparation_sha256=sha(service_path))', 'Actual additive service physical lineage')
    one("G=load('persistent130_game',pin(model_receipt['model'],model_receipt['model_sha256']));", "pin(model_receipt['model'],model_receipt['model_sha256']);G=load('persistent138_widgets',ROOT/'reports/m4-fps-original/source-preparation-r4/game_model.py');", 'Widget literal model inherits the unchanged accepted persistent model')
    one("D=load('persistent54_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');", "D=load('persistent138_direct',ROOT/'tools/m4-crt-allocation-root/run_storage.py');", 'Same strict canonical reader with declared G storage allowlist')
    one("mfc=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL'", "crt_image=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes());mfc=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL'", 'Physically derive five new CRT input pages')
    one("   if p==0x5f4cc000:", "   if p in (0x7800f000,0x78010000,0x78023000,0x7802e000,0x78037000):\n    result=bytearray(4096)\n    for sec in crt_image.sections:\n     lo=max(p,crt_image.image_base+sec['virtual_address']);hi=min(p+4096,crt_image.image_base+sec['virtual_address']+sec['raw_size'])\n     if hi>lo:offset=sec['raw_offset']+lo-crt_image.image_base-sec['virtual_address'];result[lo-p:hi-p]=crt_image.data[offset:offset+hi-lo]\n    return bytes(result)\n   if p==0x5f4cc000:", 'Only physical own CRT page bytes enter missing bootstrap pages')
    one('program,callbacks=G.source_program();static=', 'roots.update(dict(zip(PW.WIDGETS,PW.CALLBACKS)));program,callbacks=G.source_program();static=', 'Exact seven additional literal registrations')
    one("len(order)==131 and order[13]", "len(order)==138 and order[13]", 'Current complete table order')
    one("a=D.DirectSet(Path(native_report).parent/level/'transport.json',pin)", "current_level=next(r for r in nr['levels'] if r['level']==level);a=D.DirectSet(current_level['capture'],pin)", 'Use actual declared current storage transport, not guessed directory')
    one("   continuity_rows.append(dict(level=level,**A.audit(a,m,J)));pin(ROOT/'tools/m4-tree-source/continuity125.py')\n   try:", "   try:\n    continuity_rows.append(dict(level=level,**A.audit(a,m,J)));pin(ROOT/'tools/m4-tree-source/continuity125.py')", 'Close the current strict reader even if scheduler continuity refuses')
    one("checkpoint_index=C.checkpoints(a,stem)", "checkpoint_index=PW.checkpoint_index(a,stem)", 'Retain all seven duplicate borrowed source checkpoint pairs')
    one('F.configure(G,m,a,seq,level,pin)', "F.F.Observer=PW.observer_class(F.Observer);F.configure(G,m,a,seq,level,pin);F.S.CURRENT.index=checkpoint_index", 'Suppress only component-owned checkpoints and preserve all actual provider checkpoints')
    one("     resource=a.words(stem+'lockit-resource.bin'", "     ObservedMachine=PW.machine_class(ObservedMachine)\n     resource=a.words(stem+'lockit-resource.bin'", 'Explicit component versus provider journal owners')
    one('V.configure(machine,lambda model:', "component_data=json.loads(pin(ROOT/'reports/m4-fps-native/connected-component-preparation-r4/contracts.json').read_bytes());literal_declarations=pin(ROOT/'reports/m4-fps-native/connected-component-preparation-r4/literals.hpp').read_text();gdi=PG.GDIAdapter(component_data,literal_declarations,a.data(f'sequence-{seq}/Widget/root-{PW.WIDGETS[-1]}/after/APIs.bin'),GDIF);gdi.configure_imports(machine);association=PW.JournalAssociation(machine,F.S.CURRENT,gdi,a,seq,level,pin);machine.widget_association=association\n     V.configure(machine,lambda model:", 'Actual GDI facts and literal import roles; no endpoint machine seed')
    one("       F.begin(machine);machine.call_stack.append((entry,FRAME,BROKER,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0));G.complete_root(machine,api=responses);F.end(machine)", "       machine.call_stack.append((entry,FRAME,BROKER,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0))\n       if entry in PW.WIDGETS:\n        association.begin(entry)\n        def leaf(model,target):\n         if target in PG.GDI_TARGETS:\n          model._source_undefined_flags=gdi.external(model,target,model._source_undefined_flags)\n         else:responses(model,target)\n        G.complete_root(machine,api=leaf);widget_rows.append(association.end());counts['literal_widget_roots']+=1\n       else:F.begin(machine);G.complete_root(machine,api=responses);F.end(machine)", 'One carried root with genuine typed GDI leaf facts and accepted source registration provider')
    one("need(len(expected_callbacks)==101", "association.prove_projection_rows(a.data(stem+'registry-research-projections.bin'));need(len(association.root_result)==7,'Every literal widget prefix/provider/tail closes');widget_cleanup_rows.append(association.cleanup(GI));counts['actual_manual_owned_font_frees']+=widget_cleanup_rows[-1]['actual_owned_font_frees'];counts['actual_GDI_source_calls']+=149;counts['complete_widget_caller_cleanup_restores']+=1;need(len(expected_callbacks)==108", 'All additional source callback byteflows, borrowed associations and genuine manual ownership cleanup')
    source = source.replace('==786:', '==828:').replace('len(rows)==1572','len(rows)==1656').replace('==1572*46','==1656*69')
    one("  seen_modules=set();modules=[G]", "  q=out/'Widget-source-derivations.json';q.write_text(json.dumps(widget_rows,indent=2)+'\\n');pin(q);need(len(widget_rows)==84 and len(widget_cleanup_rows)==12 and counts['actual_manual_owned_font_frees']==180,'Every seven literal widget root and fifteen real owned-font frees across12 current carried sequences');pin(PW.__file__);pin(PG.__file__);pin(GDIF.__file__);pin(GI.__file__);pin(A.__file__);pin(F.__file__);pin(F.F.__file__);pin(EX.__file__)\n  seen_modules=set();modules=[G]", 'Complete bounded widget source export and executed helper pins')
    one("('Literal-defined-flag-consumers.json',flag_rows)", "('Widget-source-derivations.json',widget_rows),('Widget-manual-native-cleanup.json',widget_cleanup_rows),('Literal-defined-flag-consumers.json',flag_rows)", 'Retain every completed widget proof on success or diagnostic refusal')
    # Only descriptive current counts change; every old source/model contract path remains frozen.
    source = source.replace("'persistent131_sequences'", "'persistent138_sequences'")
    one("scope='One true bootstrap BEFORE plus original source/finite actual API responses and admitted old numerical oracles; persistent native131 game State/FX/CPU/ENV and entire46pages in actual table order'", "scope='One true bootstrap BEFORE plus original source/finite actual API responses and admitted old numerical oracles; persistent native138 game State/FX/CPU/ENV and entire69pages in actual table order. Component and provider source journals share exactly two literal borrowed CALL operands; actual native GDI scalar facts admit source-derived typed handle tokens only'", 'Exact current whole carried source and journal scope')
    ast.parse(source)
    main_path = out/'compare_provider138.py'; main_path.write_text(source)
    continuity = pin(R/'tools/m4-joint-startup131/continuity131.py').read_text()
    for old,new in [('selected-table.bin\',131','selected-table.bin\',138'),('registration-roots.bin\',101','registration-roots.bin\',108'),('len(pages)==29','len(pages)==52')]:
        assert old in continuity;continuity=continuity.replace(old,new)
    ast.parse(continuity);(out/'continuity138.py').write_text(continuity)
    observer = pin(R/'tools/m4-formatting-source/final_observer130.py').read_text()
    source_anchor="_source=Path(__file__).resolve().parents[1]/'m4-tree-source/final_observer125_v2.py'"
    assert observer.count(source_anchor)==1
    observer=observer.replace(source_anchor,"_source=Path(__file__).resolve().parents[3]/'tools/m4-tree-source/final_observer125_v2.py'")
    anchor="exec(compile(_text,str(_source),'exec'),globals())"
    assert observer.count(anchor)==1
    observer=observer.replace(anchor,"assert _text.count('ROOT=Path(__file__).resolve().parents[2]')==1\n_text=_text.replace('ROOT=Path(__file__).resolve().parents[2]','ROOT=Path(__file__).resolve().parents[3]')\nassert _text.count('len(roots)==101')==1 and _text.count('registry-replay-{101+n}')==2 and _text.count(\"COUNTS['selected_registration_closures']+=101\")==1\n_text=_text.replace('len(roots)==101','len(roots)==108').replace('registry-replay-{101+n}','registry-replay-{108+n}').replace(\"COUNTS['selected_registration_closures']+=101\",\"COUNTS['selected_registration_closures']+=108\")\n"+anchor)
    ast.parse(observer);(out/'final_observer138.py').write_text(observer)
    observer_v2=pin(R/'tools/m4-formatting-source/final_observer130_v2.py').read_text()
    assert observer_v2.count('import final_observer130 as F')==1
    observer_v2=observer_v2.replace('import final_observer130 as F','import final_observer138 as F')
    ast.parse(observer_v2);(out/'final_observer138_v2.py').write_text(observer_v2)
    exports=pin(R/'tools/m4-joint-startup131/paired_exports.py').read_text()
    anchor="def selected(key):\n"
    assert exports.count(anchor)==1
    exports=exports.replace(anchor,anchor+" if re.fullmatch(r'sequence-\\d+/Widget/.*',key):return True\n")
    ast.parse(exports);(out/'paired_exports.py').write_text(exports)
    for path in (R/'tools/m4-joint-startup138/persistent_widgets.py',R/'tools/m4-widget-growth-review/persistent_gdi.py',R/'reports/m4-fps-original/source-preparation-r4/game_model.py',R/'reports/m4-fps-native/connected-component-preparation-r4/literals.hpp'):
        text=pin(path).read_text()
        if path.suffix=='.py':ast.parse(text)
    for path in out.iterdir():
        if path.is_file():pin(path)
    pin(__file__);pin(sys.executable)
    report=dict(passed=True,scope='Unexecuted complete138 source preparation from physically bound accepted131 comparer plus seven source widget intervals',
        parent_source_sha256=PARENT,native_execution_sha256=NATIVE,joint_preparation_sha256=PREP,
        GDI_source_preparation_sha256='bf18a74560d29a10a373fd6244bb9367393386b85cbb51084020f1383c5e5bc2',
        entrypoint=str(main_path),source_changes=changes,source_roots=138,source_cases=12,source_phases=1656,
        whole_source_pages_per_endpoint=69,preserved_accepted_numeric_page_order=True,
        provider_journal_relation='Only component prefix/tail operands excluded from Session-owned journal; exactly two literal CALL operands belong to both',
        source_GDI_facts='Actual native scalar RAX/RCX/RDX/flags with source-derived guest handle tokens and same-source frame/arguments; no GDI output/State seed',
        prior131_proof_gates_retained=True,AFTER_State_or_memory_seed=False,per_phase_reseed=False,
        original138_required_before_reader=True,writer_executed=False,capture_archive_reader_opened=False,
        initializer_credit=0,files=pins)
    path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),changes=len(changes),files=len(pins))))

if __name__=='__main__':
    main(sys.argv[1])
