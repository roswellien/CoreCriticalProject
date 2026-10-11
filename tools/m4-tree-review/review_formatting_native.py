"""Independent compact formatter source, dynamic private joins and native gates."""
import collections, json, struct, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
import review_connected125_v2 as C

def main(name):
    out=R/'reports/m4-tree-review'/name;C.need(not out.exists(),'Fresh compact formatter native review');out.mkdir(parents=True);counts=collections.Counter();passed=False
    try:
        C.pin(__file__);C.pin(C.__file__)
        area=R/'reports/m4-formatting-source'
        source=C.read(area/'native-source-r9/report.json','0f2e817ff2bf938e32be26d7018d3921be5142461bf54ddfe70e0a676daa2306');witness=C.read(area/'native-witnesses-r4/report.json','284091a7d9efd64e695d399e89de94496a8c8c9181e4f0a3ecf589ef3d864510')
        C.need(source['passed'] and witness['passed'] and witness['source_receipt_sha256']==C.PINS[str((area/'native-source-r9/report.json').resolve())] and source['reader_closed'] and witness['reader_closed'] and source['native_whole_stack_compared'] and not source['candidate_AFTER_machine_seed'] and not source['root_BEFORE_machine_seed'] and not witness['candidate_AFTER_source_seed'] and not source['initializer_credit'],'Current exact producer receipts preserve persistent whole machine source scope')
        for report in (source,witness):
            for q,h in report['files'].items():
                if Path(q).suffix not in ('.mwb','.zip'):C.pin(q,h)
        native=C.read(R/'reports/m4-formatting-native/preparation-r15/report.json','bbe18a53a6c8c400f3274e470a28ded84d7c7c45c4fc860cf5e598ed4d5730aa')
        execution=C.read(R/'reports/m4-formatting-native/fixture-execution-r4/report.json','55ecbdc1a115f73ab046ea92f6e33f5af0020d92a530dbe2a3e145af7d37bba0');build=C.read(execution['build_path'],execution['build_sha256']);prep=C.read(build['preparation'],build['preparation_sha256'])
        C.need(execution['passed'] and build['passed'] and prep['native_preparation_sha256']==build['native_preparation_sha256']==C.PINS[str((R/'reports/m4-formatting-native/preparation-r15/report.json').resolve())] and prep['actual_Runtime_selected_call'] and prep['selected_roots']==[0x4df610,0x4e0710,0x4e0810], 'All source/private proofs bind actual registered Runtime three-root native15/build7')
        for q,h in native['files'].items():
            if Path(q).parent==Path(native['native_include']):C.pin(q,h)
        cpp=C.pin(area/'persistent-model-r3/persistent_model.py','48df981dd7ebbe2d12d1c69196ee18d5e7393eb7dcacc3ead5674580a7d56b4d').read_text()
        C.need('class Machine(G.Machine):'in cpp,'Formatter semantic methods inherit exact accepted persistent Machine')
        checker=C.pin(R/'tools/m4-formatting-source/compare_native_fixture_v9.py',source['files'][str((R/'tools/m4-formatting-source/compare_native_fixture_v9.py').resolve())]).read_text()
        for text in ('machine,responses=B2.bootstrap(before,facts,heap,material,Observed,program,callbacks,pc,sp', 'G.begin_root(machine,entry)', 'G.complete_root(machine,api=responses)', "equal(bytes(machine.state),record[141540:145044]", "equal(bytes(machine.state),record[145044:148548]", "equal(machine.bytes(page,4096),reader.data(f'actual-after-root-{phase}/current-page-{page}.bin')", "equal([tuple(r)for r in machine.accesses],actual_accesses", "equal(bytes(machine.state),reader.data('sample.bin')[4272:7776]", 'responses.complete()', "need(READS<=set(PINS)"):
            C.need(text in checker,'Exact current persistent full source/memory/lifecycle/audit seam '+text)
        C.need(checker.count('B2.bootstrap(')==1 and checker.index('for phase,entry in enumerate(ROOTS)')>checker.index('B2.bootstrap('),'Single bootstrap BEFORE machine feeds all three phases without root reseed')
        private=C.pin(R/'tools/m4-formatting-source/compare_native_witnesses_v4.py',witness['files'][str((R/'tools/m4-formatting-source/compare_native_witnesses_v4.py').resolve())]).read_text()
        for text in ("source_accesses[base:],[tuple(row)for row in r['source_accesses']]", "rows(a,stem+'formatting-calls.bin',16)", "rows(a,stem+'formatting-owned.bin',12)", "rows(a,stem+'formatting-publications.bin',12)", "rows(a,stem+'formatting-dispatches.bin',8)", 'before[8]and before[9]==1 and after[8:10]==(0,0)', "equal(enters,leaves", "before[10:12]==(0,0)"):
            C.need(text in private,'Every whole private row/current generation and actual lifecycle relation '+text)
        normal=C.read(area/'normal-contracts-r1/normal-contracts.json','121d091142d4a72a84e26aeb8254724b8f3a6ebac1593dc8296eecc2160e18aa')
        rows=C.read(area/'native-source-r9/source-derivations.json',source['files'][str((area/'native-source-r9/source-derivations.json').resolve())]);proofs=C.read(area/'native-witnesses-r4/witness-source-relations.json',witness['files'][str((area/'native-witnesses-r4/witness-source-relations.json').resolve())]);C.need(len(rows)==len(proofs)==6,'Six full current source/private phase artifacts')
        for r,p in zip(rows,proofs):
            C.need((r['level'],r['phase'],r['root'])==(p['level'],p['phase'],p['root']),'Exact actual perlevel phase/root identity')
            phase=r['phase'];owner=r['owner'];contract=normal['cases'][phase];guest=owner['guest'];generation=owner['generation'];start=p['source_access_start'];access=r['source_accesses'];initial=bytes.fromhex(owner['initial']);full=bytearray(initial)
            C.need(owner==p['owner'] and owner['extent']==16 and owner['requested']==(8,10,12)[phase] and generation>0 and owner['native'] and owner['live'] and len(initial)==16,'Same real requested/current native pointer generation/initial capacity')
            F=r['calls'][0]['frame']+36
            for ci,call in enumerate(r['calls']):
                expect=[1,r['root'],call['PC'],call['target'],call['frame'],F,len(call['args'])]+call['args']+[0]*(4-len(call['args']))+[0,guest if ci else 0,generation if ci else 0,1,call['result']]
                C.need(call['returned'] and call['returned_ESP']==call['frame']+4 and p['calls'][ci]==expect,'Every full16Q current source cdecl CALL/RET frame and result relation');counts['independent_cdecl16Q_joins']+=1
            expected_owned=[]
            for i,(pc,address,value,width,writing)in enumerate(access):
                if pc not in (0x7801042a,0x78022bd5):continue
                C.need(guest<=address and address+width<=guest+owner['requested'],'Exact source-owned requested interval')
                expected_owned.append([1,r['root'],len(expected_owned),pc,address,width,writing,value,guest,generation,address-guest,start+i+1])
                offset=address-guest
                if writing:full[offset:offset+width]=value.to_bytes(width,'little');counts['independent_literal_owner_stores']+=1
                else:C.need(width==1 and full[offset]==initial[offset]==value,'Actual source NUL RMW uses untouched current native acquired byte');counts['genuine_initial_NUL_read_joins']+=1
            C.need(expected_owned==p['owned'] and [(w[3],w[10],w[5],bool(w[6]))for w in expected_owned]==[(w['PC'],w['offset'],w['width'],w['writing'])for w in contract['owned_accesses']],'Every complete12Q private owner row exactly equals independent source causal order')
            C.need(full.hex()==owner['source_final_hex'] and full[owner['requested']:]==initial[owner['requested']:],'Entire genuine capacity16 byteflow from actual initial/source stores with untouched tails');counts['whole16B_capacity_byteflows']+=1;counts['independent_owned12Q_joins']+=len(expected_owned)
            field=contract['root_contract']['owned_pointer_field'];pub=[(i,a)for i,a in enumerate(access)if a[0]==0x4deabc and a[1]==field];C.need(len(pub)==1 and pub[0][1]==[0x4deabc,field,guest,4,1],'Exact literal primary publication')
            C.need(p['publication']==[1,r['root'],0x4deabc,field,guest,generation,owner['requested'],owner['extent'],start+pub[0][0]+1,0,0,0],'All12Q publication fields bind current acquired generation');counts['independent_publication12Q_joins']+=1
            for i,d in enumerate(r['dispatches']):
                C.need(d['index']==(1,7,1,7)[i] and d['table_read']==0x780103fa+4*d['index'] and d['target']==(0x7800fd04 if d['index']==1 else 0x7800fe69),'Source-derived precise normal table branch')
                C.need(p['dispatches'][i]==[1,r['root'],i,d['PC'],d['index'],d['table_read'],d['target'],d['source_access_index']+1],'Every whole8Q actual private dispatch matches physical current source table read');counts['independent_dispatch8Q_joins']+=1
            C.need(p['status']==[1,0,phase+1,F,guest,generation,len(expected_owned),4,1,0],'Every whole10DWORD completed normal source lifetime status');counts['whole_current_lifetime_statuses']+=1
        operations=C.pin(Path(native['native_include'])/'formatting_operations.inc').read_text();guard=C.pin(Path(native['native_include'])/'locale_batch_binding.inc').read_text()
        for text in ('a->guest!=formatting_owner_||a->generation!=formatting_generation_||a->kind!=1', 'std::uint64_t(address)+bytes>std::uint64_t(a->guest)+a->requested', 'e.pc!=pc||e.offset!=address-a->guest||e.bytes!=bytes||e.writing!=writing||(writing&&e.value!=value)', 'a->initial[address-a->guest]!=std::byte(value)', 'index!=order[formatting_dispatch_cursor_]', 'frame!=formatting_base_+spec->frame_offset', 'state.gpr.rsp.dword!=frame+4'):
            C.need(text in operations,'Exact native dynamic normal guard '+text)
        C.need('const auto formatting_calls=formatting_calls_'in guard and 'formatting_calls!=formatting_calls_'in guard and 'formatting_owned!=formatting_owned_'in guard and 'formatting_publications!=formatting_publication_records_'in guard and 'formatting_dispatches!=formatting_dispatches_'in guard,'Actual complete private histories are protected across observer callbacks')
        for key,value in {'strict_native_phases':6,'whole_BEFORE_pages':420,'whole_AFTER_pages':420,'whole_source_access_records':7966,'whole_native_owner_backings':6,'literal_cdecl_CALL_RET':18,'literal_table_dispatches':24,'complete_actual_lifecycles':2,'whole_provider_checkpoints':148,'whole_heap_prefix_checkpoints':42,'literal_producer_source_frees':2,'actual_native_CS_deletes':10,'actual_native_formatter_cleanup_frees':6}.items():C.need(source['counts'][key]==value,'Exact producing source count '+key);counts[key]=value
        for key,value in {'literal_private_cdecl_rows':18,'literal_private_owned_operands':66,'literal_private_publications':6,'literal_private_table_dispatches':24,'actual_cleaned_allocation_lifetimes':8,'actual_cleaned_native_CS_lifetimes':10,'outside_return_whole_State_source_proofs_consumed':2}.items():C.need(witness['counts'][key]==value,'Exact producing private/lifecycle count '+key);counts[key]=value
        passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        report=dict(passed=passed,scope='Independent bounded native15 formatter3 normal source, actual current generation/private row byteflows and complete actual lifecycle receipt review',source_receipt_sha256='0f2e817ff2bf938e32be26d7018d3921be5142461bf54ddfe70e0a676daa2306',witness_receipt_sha256='284091a7d9efd64e695d399e89de94496a8c8c9181e4f0a3ecf589ef3d864510',native_preparation_sha256='bbe18a53a6c8c400f3274e470a28ded84d7c7c45c4fc860cf5e598ed4d5730aa',counts=dict(counts),capture_archives_opened=0,native_source_machine_seed=False,original_API_volatile_equality_claim=False,generic_formatter_closed=False,initializer_credit=0,files=C.PINS)
        target=out/'report.json';target.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=C.hashlib.sha256(target.read_bytes()).hexdigest(),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
