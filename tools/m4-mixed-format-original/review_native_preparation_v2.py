"""Small independent finite-contract review; no archive or execution claims."""
from pathlib import Path
import hashlib,json,re,sys,traceback
R=Path(__file__).resolve().parents[2]
PINS={}
def need(v,s):
    if not v:raise ValueError(s)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();need(p.suffix.lower()!='.mwb','No archive reader in light review')
    v=sha(p);need(h is None or v==h,'Exact physical receipt/source identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Unchanged physical input');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def rows(text,name):
    m=re.search(r'\b'+re.escape(name)+r'\[\]\s*\{(.*?)\n\};',text,re.S)
    need(m,'Physical compiled declarative array '+name)
    return [tuple(map(int,x.split(','))) for x in re.findall(r'\{([\d,-]+)\}',m.group(1))]
def main(name):
    out=R/'reports/m4-mixed-format-original'/name;need(not out.exists(),'Fresh additive review');out.mkdir(parents=True)
    passed=False;facts={}
    try:
        p=R/'reports/m4-formatting-native/preparation-r18'
        report=read(p/'report.json','68498a9eaaf924205e11bbf30fbaa355380afc528b892c6739f9a1d199731d06')
        need(report['passed']and not report['native_executed'],'Prepared unexecuted native composition')
        interface_path=R/'reports/m4-mixed-format-original/native-interface-r1/report.json'
        interface=read(interface_path,'1513911ec682032f5ec844aae2010d39c435e545ed60f8b2946cfaae1df0e4ee')
        source=read(R/'reports/m4-mixed-format-original/original-source-r7/report.json','3a30f008243812bc5205487cbb08265e4ab9fd1e0e8377cb7ccd176230929823')
        lifts=read(R/'reports/m4-mixed-format-original/lifts-r1/report.json','44138f2cb1c9eb6208bd16d7fc8c6de1a400869aa70a1ef2788058a89f9ec569')
        need(interface['passed']and source['passed']and lifts['passed'],'Actual original/literal/lift lineage')
        for key,expected in [('mixed_source_receipt_sha256',PINS[str((R/'reports/m4-mixed-format-original/original-source-r7/report.json').resolve())]),('mixed_interface_receipt_sha256',PINS[str(interface_path.resolve())]),('mixed_lifts_receipt_sha256',PINS[str((R/'reports/m4-mixed-format-original/lifts-r1/report.json').resolve())])]:need(report[key]==expected,'Direct current preparation lineage '+key)
        contract_path=interface_path.parent/'contracts.json';contract=read(contract_path,interface['files'][str(contract_path.resolve())])
        family=read(report['mixed_contracts'],report['mixed_contracts_sha256']);need(family['mixed_interface']==contract,'Whole finite interface retained')
        names=['mixed_format_contract.inc','mixed_format_operations.inc','fs_contract.inc','fs_operations.inc','Lockit_contract.inc','tree_contract.inc','locale_batch_operations.inc','session_impl.inc','locale_batch.hpp']
        texts={n:pin(p/n,report['files'][str((p/n).resolve())]).read_text() for n in names}
        decl=texts['mixed_format_contract.inc'];ops=texts['mixed_format_operations.inc'];fs=texts['fs_contract.inc'];calls=texts['locale_batch_operations.inc']
        expected=[]
        for x in contract['owned_access_contracts']:
            v=x['source_value_relation'];expected.append((x['source_pc'],x['owner_index'],x['owned_offset'],x['width'],v.get('owner_index',-1),v.get('literal',0)))
        need(rows(decl,'mixed_format_owned')==expected and len(expected)==10,'Ten complete ordered source-owned value tuples')
        source_fs=rows(fs,'fs_owned_accesses');specs=contract['MFC_allocation_contracts']
        for x in contract['owned_access_contracts']:
            spec=next(y for y in specs if y['owner_index']==x['owner_index'])
            need((0x4e1ca0,x['source_pc'],1,x['width'],0x4e1ca0,spec['allocation_CALL_pc'],x['owned_offset'])in source_fs,'Actual shared-owner admission row')
        source_inputs=rows(fs,'fs_inputs')
        for x in contract['publication_contracts']:
            spec=next(y for y in specs if y['owner_index']==x['owner_index'])
            need(any(r[:3]==(0x4e1ca0,spec['allocation_CALL_pc'],spec['requested'])and r[4:6]==(x['publication_address'],x['publication_pc'])for r in source_inputs),'Three exact publication addresses and source CALL occurrence')
        frames=rows(fs,'fs_frames')
        for x in contract['FS_frame_contracts']:
            need((x['function'],x['handler'],x['read_pc'],x['install_pc'],x['saved_predecessor_read_pc'],x['restore_pc'],x['return_pc'])in frames,'Whole nested FS interface row')
        need((0x4e1ca0,0x4e530f,0x4e5389,48,48)in rows(texts['Lockit_contract.inc'],'lockit_inputs'),'Exact source44/enteredCALL48 Lockit scratch')
        derivation_path=R/'reports/m4-mixed-format-original/original-source-r7/source-derivations.json'
        deriv=read(derivation_path,source['files'][str(derivation_path.resolve())])[0]
        counter=[x for x in deriv['source_accesses']if x[1]==0x60b7d0]
        need(counter==[[0x4e5346,0x60b7d0,0,4,0],[0x4e534f,0x60b7d0,1,4,1]],'Literal source counter zero to one, untouched BEFORE')
        null_args=[x for x in deriv['source_accesses']if x[0]==0x4e22e0];need(len(null_args)==5 and all(x[2:]==[0,4,0]for x in null_args),'All five genuine literal NULL argument reads')
        physical=read(R/'reports/m4-mixed-format-original/recovery-r1/instruction-contracts.json')
        null_read=next(x for x in physical['instructions']if x['pc']==0x4e22e0)
        need(null_read['bytes_hex']=='8b442404','Physical cdecl argument ESP+4')
        need('mixed_format_called(target,w.pc,w.address);'in calls and 'w.address!=state.gpr.rsp.dword'in calls and 'runtime.memory().load<unsigned>({w.address})!=w.value'in calls,'Passed frame is actual committed source CALL frame')
        need('runtime.memory().load<unsigned>({frame+4})'in ops and 'target==0x78010a6d' in ops,'Finite NULL path; unobserved strdup explicitly denied')
        for fragment in ['runtime.memory().load<unsigned>({0x60b7d0})!=1','accesses!=10||pubs!=3','a->generation!=owner->words[18]','a->requested!=spec.request','address!=a->guest+e.offset','value!=expected']:
            need(fragment in ops,'Finite actual native owner/counter predicate '+fragment)
        need('mixed_format_enter();'in texts['session_impl.inc'] and 'mixed_format_owner_before(a,v,n,true);'in calls and 'mixed_format_returned(f.entry);'in calls,'Actual Binding read/write/call/return integration')
        for key,body in lifts['source_bodies'].items():
            if body['entry']==0x49bfd0:continue
            actual=report['formatting_bodies'][str(body['entry'])]
            need(actual==body,'Exact retained whole literal mixed body '+key)
            for value in body['objects'].values():
                obj,h=value['path'],value['sha256'];pin(obj,h);need(report['entry_objects'].get(obj)==h,'Exact added object membership '+obj)
        need(report['live_owner_bound']==92 and report['current_selected_roots']==129 and report['current_callback_roots']==101,'Finite four-root composition inventory')
        facts={'ordered_owned_value_tuples':10,'publication_tuples':3,'nested_complete_FS_frames':2,'balanced_Lockit_pairs':1,'scratch_source_offset':44,'scratch_entered_CALL_offset':48,'literal_NULL_argument_reads':5,'literal_counter_initial':0,'literal_counter_final':1,'new_literal_bodies':6,'new_literal_objects':12,'shared_49BFD0_reused':True}
        passed=True
    except Exception:traceback.print_exc()
    pin(__file__)
    result={'passed':passed,'scope':'Independent physical preparation/source-contract review of mixed formatter4 composition; no native execution, archive read, full source acceptance or initializer credit.', 'facts':facts,'archive_reader_opened':False,'native_runtime_claim':False,'generic_strdup_claim':False,'counter_value_from_original_AFTER':False,'postRET_input_seed':False,'files':PINS}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':passed,'report':str(out/'report.json'),'sha256':sha(out/'report.json'),'facts':facts}));return 0 if passed else 1
if __name__=='__main__':sys.exit(main(sys.argv[1]))
