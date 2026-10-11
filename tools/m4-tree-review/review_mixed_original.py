"""Independent compact mixed formatter/MFC/FS/Lockit source and byte review."""
import collections
import importlib.util
import json
import struct
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
import review_connected125_v2 as C
import review_formatting_source_v3 as F
import review_formatting_observers as W


def module(path,name):
    spec = importlib.util.spec_from_file_location(name,C.pin(path)); value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value); return value


def main(name):
    out = ROOT / 'reports/m4-tree-review' / name; C.need(not out.exists(),'Fresh mixed review'); out.mkdir(parents=True)
    counts = collections.Counter(); passed = False
    try:
        for p in (__file__,C.__file__,F.__file__,W.__file__): C.pin(p)
        area = ROOT / 'reports/m4-mixed-format-original'
        source = C.read(area/'original-source-r7/report.json','3a30f008243812bc5205487cbb08265e4ab9fd1e0e8377cb7ccd176230929823')
        attribution = C.read(area/'linked-observer-r2/report.json','f736dd6b086964f6a96b23d5ce6d6174e0a8be88b4cfeebb49bbd445de91a335')
        C.need(source['passed'] and attribution['passed'] and source['reader_closed'] and attribution['reader_closed'] and
               source['complete_executed_dependency_chain_pinned'] and source['allocator_FS_frames_literal_only'] and
               source['original_game_FS_observations']==6 and not source['source_post_state_seed'] and
               source['undefined_flag_control_denied'] and source['write_operand_before_from_literal_backing'] and
               not source['native_executed'] and not source['initializer_credit'] and not attribution['return_hook_runtime_page_observed'],
               'Exact mixed literal and observer scope retained')
        for report in (source,attribution):
            for p,h in report['files'].items():
                path=Path(p)
                if path.suffix not in ('.mwb','.zip') and path.stat().st_size<=64*1024*1024:
                    C.pin(path,h)
        compare_path=ROOT/'tools/m4-mixed-format-original/compare_source_v8.py'; compare=C.pin(compare_path,source['files'][str(compare_path)]).read_text()
        for text in ("raw[2276+i*4096:2276+(i+1)*4096]", "source_pc>=0x78000000:return", "u(model.bytes(frame+104,4))[0]==owner_inputs[i]['CALL_pc']+5",
                     "pc!=0x780012b3 or int.from_bytes(self.bytes(self.reg('esp'),4),'little')==0x4deab7", "site==0x7800137f",
                     "len(retained_owners)==4", "cp_index[0]==6", "fs_index[0]==6", "model.api_return(site,1,ac[0],[(0x78145640,cs)])",
                     "AUDITED_READS<=set(PINS)"):
            C.need(text in compare,'Exact reviewed source/occurrence/finite API/audit seam '+text)
        derivations=C.read(area/'original-source-r7/source-derivations.json',source['files'][str(area/'original-source-r7/source-derivations.json')])
        joins=C.read(area/'original-source-r7/instruction-joins.json',source['files'][str(area/'original-source-r7/instruction-joins.json')])
        api=C.read(area/'original-source-r7/finite-API-inputs.json',source['files'][str(area/'original-source-r7/finite-API-inputs.json')])
        C.need(len(derivations)==1 and len(joins)==797 and len(api)==6,'Exactly one genuine mixed root,797 instructions and six finite API responses')
        M=module(ROOT/'tools/m4-formatting-source/provider_model.py','mixed_review_provider')
        G=module(ROOT/'tools/m4-lockit-source/game_model.py','mixed_review_game')
        program,_=G.source_program(); provider,_=M.source_program()
        for pc,row in provider.items():
            C.need(pc not in program or program[pc]==row,'Exact shared literal program'); program[pc]=row
        for file in (ROOT/'reports/m4-onexit-review/interface-r1/instruction-contracts.json',area/'recovery-r1/instruction-contracts.json'):
            recovered=C.read(file,source['files'][str(file)])
            for row in recovered['instructions']:
                C.need(row['pc'] not in program or program[row['pc']]==row,'Exact recovered mixed source'); program[row['pc']]=row
        provider_PCs=set(provider)&{row['pc'] for row in C.read(ROOT/'reports/m4-formatting-source/provider-recovery-r2/instruction-contracts.json',source['files'][str(ROOT/'reports/m4-formatting-source/provider-recovery-r2/instruction-contracts.json')])['instructions']}
        phase=derivations[0]; domain={}; index=0; scan=0
        for pc in phase['source_PCs']:
            row=program[pc]; current=joins[index] if pc in provider_PCs else None
            cpu=current['CPU_before'] if current else None
            if row['mnemonic']=='scasb':
                iteration=phase['string_iterations'][scan]; C.need(iteration['PC']==pc and iteration['ECX_before'],'Exact finite scan source count')
                if current: C.need(cpu[1]==iteration['ECX_before'],'Actual provider scan count')
                else: cpu=[None,iteration['ECX_before']]
                scan+=1
            C.need(not set(domain)&F.CONSUMED.get(row['mnemonic'],set()),'Every modeled control/carry/DF source input is defined')
            following=F.flag_domain(row,domain,cpu)
            if current:
                C.need(current['index']==index and current['PC']==pc and F.causes(current['undefined_flags_before'])==domain and F.causes(current['undefined_flags_after'])==following,
                       'Exact independent flag cause/lifetime at every genuine provider instruction')
                C.need(F.projected(current['CPU_before'],domain)==F.projected(current['actual_CPU_before'],domain) and
                       F.projected(current['CPU_after'],following)==F.projected(current['actual_CPU_after'],following),'Whole defined CPU side relation')
                for cell in current['operands']:
                    expected=collections.Counter((cell['before'] if d==0 else cell['after'],d)for d,on in ((0,cell['read']),(1,cell['write']))if on)
                    C.need(expected==collections.Counter((r[2],r[4])for r in cell['source_rows']) and all(r[0]==pc and r[1]==cell['address'] and r[3]==cell['width']for r in cell['source_rows']),
                           'Every actual source operand value/direction/width')
                    if cell['write']: C.need(cell['before']==cell['source_before_value'],'Literal whole write BEFORE value'); counts['write_before_joins']+=1
                    counts['exact_operand_joins']+=1
                F.selected_extended(row,current,counts)
                counts['whole_defined_CPU_sides']+=2; counts['independent_flag_lifetime_instruction_joins']+=1; index+=1
            domain=following
            if pc in (0x7800137f,0x7810a30b,0x7810a35e): domain={}
        C.need(index==797 and scan==len(phase['string_iterations']) and [r['index']for r in phase['dispatches']]==[1,7,1,7],'Complete actual provider/scan and dispatch extent')
        mixed=C.read(area/'trace-prefix-validation-r1/actual-mixed-owned-relations.json',source['files'][str(area/'trace-prefix-validation-r1/actual-mixed-owned-relations.json')])
        formatter=C.read(area/'trace-prefix-validation-r1/actual-owners.json',source['files'][str(area/'trace-prefix-validation-r1/actual-owners.json')])[0]
        owners={r['API_index']:r for r in mixed+[formatter]}
        acquisitions=[r for r in api if r['source_CALL']==0x7800137f]
        C.need(len(owners)==len(acquisitions)==4 and len({r['actual_EAX']for r in acquisitions})==4,'Four distinct actual logical owner occurrences')
        for row in acquisitions:
            owner=owners[row['API_index']]; C.need(row['actual_EAX']==owner['pointer'] and row['initial_hex']==owner['initial_hex'] and row['initial_capacity']==owner['capacity'] and row['AFTER_machine_seed'] is False,
                                                'Exact same occurrence initial backing/current API pointer')
            if 'source_frame'in owner:
                C.need(row['frame']+104==owner['source_frame'] and row['source_game_CALL']==owner['CALL_pc'] and int.from_bytes(bytes.fromhex(owner['actual_source_frame32_hex'])[:4],'little')==owner['CALL_pc']+5,
                       'Repeated request/ESP resolved by actual source frame and exact game CALL return')
                full=bytearray(bytes.fromhex(owner['initial_hex']))
                for store in owner['literal_source_stores']:
                    a=store['offset']; n=store['width']; C.need(a+n<=owner['source_request'],'Exact source requested owner extent')
                    full[a:a+n]=store['value'].to_bytes(n,'little'); counts['independent_MFC_store_byteflows']+=1
                C.need(full.hex()==owner['final_hex'],'Entire genuine MFC capacity reconstructed from initial/source stores'); counts['whole_MFC_capacity_byteflows']+=1
            else:
                C.need(owner['request']==11 and owner['capacity']==16 and owner['output_hex']=='76616c7665732e7a726400' and owner['final_hex'][22:]==owner['initial_hex'][22:], 'Whole actual valves filename plus carried capacity tail')
        C.need(len({(r['source_game_CALL'],r['API_index'])for r in acquisitions})==4,'No first-site/first-request owner shortcut')
        CP=C.read(area/'trace-prefix-validation-r1/actual-Lockit-boundaries.json',source['files'][str(area/'trace-prefix-validation-r1/actual-Lockit-boundaries.json')])
        FS=C.read(area/'trace-prefix-validation-r1/actual-FS-events.json',source['files'][str(area/'trace-prefix-validation-r1/actual-FS-events.json')])
        C.need(len(CP)==len(FS)==6 and [r['kind']for r in FS]==[0,1,0,1,2,2],'Two nested six-event normal game FS scopes')
        C.need([r['source_CALL']for r in api if r['source_CALL']!=0x7800137f]==[0x7810a30b,0x7810a35e] and api[2]['original_ctor_response_scope']=='pre-epilogue7810A311' and not api[2]['original_source_postRET_seed'],
               'Two finite actual CS APIs retain precise pre-epilogue/preRET boundaries')
        PE=module(ROOT/'tools/analysis/pe.py','mixed_review_PE'); COFF=module(ROOT/'tools/m4-fs-source/observer_attribution.py','mixed_review_COFF')
        L=module(ROOT/'tools/m4-lockit-review/full_original_review.py','mixed_review_CP_pattern')
        bindings=C.read(ROOT/'reports/m4-lockit-original/original-preparation-r4/lockit-hook-bindings.json')
        rows=C.read(area/'linked-observer-r2/compiled-observer-attribution.json',attribution['files'][str(area/'linked-observer-r2/compiled-observer-attribution.json')])
        for gate in ('prefix-validation-r1','trace-prefix-validation-r1'):
            validation=C.read(area/gate/'report.json',attribution['files'][str(area/gate/'report.json')])
            execution=C.read(validation['execution_path'],validation['execution_sha256']); build=C.read(execution['build_path'],execution['build_sha256'])
            prepdir=Path(build['preparation']); worker=PE.PEImage(C.pin(build['worker'],build['worker_sha256']).read_bytes())
            release=Path(execution['build_path']).parent/'build-x86/mw34_joint_startup124_original.dir/Release'
            fshooks=C.read(prepdir/'fs-hook-bindings.json',attribution['files'][str(prepdir/'fs-hook-bindings.json')])
            shared={}
            for row in [r for r in rows if r['gate']==gate]:
                family=row.get('family','format'); pc=row['source_PC']; kind=row['kind']
                if family=='format':
                    expected,rel=W.expected(pc,kind,row['tail_field_index'],bytes.fromhex(row['replay_hex'])); symbol=row['symbol']; obj='format_observer_x86.obj'
                elif family=='FS':
                    h=next(x for x in fshooks if x['PC']==pc); expected,rel,_=COFF.expected_function(pc,kind,bytes.fromhex(h['raw_bytes'])); symbol='_'+h['declared_observer']; obj='fs_observer_x86.obj'
                else:
                    if pc:
                        h=next(x for x in bindings if x['pc']==pc); symbol='_'+h['name'].replace('probe_','lockit_')
                        replay=bytes.fromhex(h['replay']); continuation='_lockit_continue_'+format(pc,'x')if h['continuation']else None; target=None
                    else:
                        symbol='_lockit_api_'+('Enter'if kind==1 else'Leave'); replay=b''; continuation=None; target='_lockit_actual_'+('Enter'if kind==1 else'Leave')
                    expected,rel=L.expected_lockit(pc,kind,replay,continuation,target); obj='lockit_observer_x86.obj'
                object_path=release/obj; symbols,sections=COFF.parse_coff(C.pin(object_path,attribution['files'][str(object_path)]).read_bytes())
                definition=next(x for x in symbols.values()if x['name']==symbol and x['section']>0); sec=sections[definition['section']]
                C.need(sec['bytes'][definition['value']:definition['value']+len(expected)]==expected and
                       [(a-definition['value'],n,t)for a,n,t in sec['relocations']if definition['value']<=a<definition['value']+len(expected)]==rel,'Entire exact independent compiled wrapper and every relocation')
                address=row['actual_worker_target']; start,_=worker.rva_range(address-worker.image_base,len(expected)); raw=worker.data[start:start+len(expected)]; normalized=bytearray(raw)
                for offset,name_,typ in rel:
                    addend=struct.unpack_from('<I',expected,offset)[0]; value=struct.unpack_from('<I',raw,offset)[0]
                    actual=(value-addend)&0xffffffff if typ==6 else(address+offset+4+value-addend)&0xffffffff
                    C.need(typ in (6,20) and (name_ not in shared or shared[name_]==actual),'Coherent typed final linked storage/call target')
                    shared[name_]=actual; normalized[offset:offset+4]=expected[offset:offset+4]
                C.need(bytes(normalized)==expected,'Every whole final linked observer byte')
                counts['independent_'+family+'_functions']+=1; counts['independent_'+family+'_bytes']+=len(expected); counts['independent_'+family+'_relocations']+=len(rel)
        C.need(counts['independent_format_functions']==12 and counts['independent_FS_functions']==102 and counts['independent_Lockit_functions']==12 and counts['exact_operand_joins']==428 and counts['write_before_joins']==189,
               'Complete independent bounded mixed executable/source extent')
        passed=True
    finally:
        report=dict(passed=passed,scope='Independent bounded mixed source/flag/operand/owner occurrence and all compiled/final-linked observers review',counts=dict(counts),
                    original_source_sha256='3a30f008243812bc5205487cbb08265e4ab9fd1e0e8377cb7ccd176230929823',observer_attribution_sha256='f736dd6b086964f6a96b23d5ce6d6174e0a8be88b4cfeebb49bbd445de91a335',
                    capture_archives_opened=0,runtime_game_patch_pages_independently_observed=False,original_postRET_machine_seed=False,
                    allocator_FS_actual_observation_credit=False,native_equivalence=False,generic_formatter_closed=False,initializer_credit=0,files=C.PINS)
        target=out/'report.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=C.hashlib.sha256(target.read_bytes()).hexdigest(),counts=dict(counts))))


if __name__=='__main__':main(sys.argv[1])
