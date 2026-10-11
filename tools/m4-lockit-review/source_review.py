"""Light source-observer bootstrap and sealed persistent124 proof review.

No capture reader is constructed. The review verifies the additive seam itself,
source-machine seed boundaries, whole-phase ABI comparisons, actual receipt
extent/order and exact current execution/build/native identities.
"""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def need(value,message):
    if not value: raise ValueError(message)


def main(source_report,name):
    out=ROOT/'reports/m4-lockit-review'/name;need(not out.exists(),'Fresh bounded source review');out.mkdir(parents=True)
    pins={};counts=Counter();passed=False;reviewed={}
    def pin(path,digest=None):
        path=Path(path).resolve();actual=sha(path);need(digest is None or actual==digest,'Exact current source input '+str(path))
        need(str(path)not in pins or pins[str(path)]==actual,'Immutable bounded source input');pins[str(path)]=actual;return path
    def read(path,digest=None):return json.loads(pin(path,digest).read_bytes())
    try:
        pin(__file__);source_report=Path(source_report).resolve();report=read(source_report)
        need(report['passed'],'Fresh actual persistent124 source proof passed')
        execution_path=ROOT/'reports/m4-joint-startup124-root/execution-r2/report.json'
        execution=read(execution_path,'e0ca3ce031afbcde80ff84c0968d30850972625d2f6d8e2a8c8934386a2e7732')
        need(report['files'][str(execution_path.resolve())]==sha(execution_path),'Source proof directly binds exact final actual native execution')
        build=read(execution['build_path'],execution['build_sha256']);need(execution['passed']and build['passed']and
             execution['build_sha256']=='05a198d319f2e3ee2259b998a8989db23df0b20afd40416fb185e7a0b1d17c30','Exact finalprep5/build4 source run')
        prep=read(ROOT/'reports/m4-lockit-native/preparation-r5/report.json','965ea738333677c308749108b7f0b211772e89d4dd5e2ed14ea561cb63d0bdc1')
        association=read(ROOT/'reports/m4-lockit-source/association-preparation-r2/report.json','bbc28d6feb2644136d123d283acc9a1564650ec313d70e995f054b4283806a8c')
        need(association['passed']and association['association_index']==4 and association['resource_generation']==5 and association['producer_HeapAlloc_index']==5,
             'Measured fifth CS resource has actual zero-based API index4/generation5, preceding producer index5')
        diag=read(ROOT/'reports/m4-lockit-source/bootstrap-diagnostic-r1/report.json')
        need(len(diag['rows'])==6 and [row['words'][1]for row in diag['rows']]==list(range(6)), 'Actual bounded first-six API index evidence')
        need(all(row['contract']['name']=='InitializeCriticalSection'and row['words'][31]==0 for row in diag['rows'][:4])and
             diag['rows'][4]['words'][:5]==[1,4,0,0x78146190,0x866ce]and diag['rows'][4]['words'][31]==1 and
             diag['rows'][5]['contract']['name']=='HeapAlloc'and diag['rows'][5]['words'][31]==0,'Genuine source API/research association/source allocation chronology')
        paths={name:ROOT/'tools/m4-lockit-source'/name for name in ('compare_connected_v6.py','responses_v3.py','bridge_v2.py')}
        for name,path in paths.items():
            pin(path,association['files'][str(path.resolve())]);need(report['files'][str(path.resolve())]==sha(path),'Executed final observer source sealed '+name)
        for relative in ('tools/m4-onexit-review/provider_bridge.py','tools/m4-lockit-source/game_model.py',
                         'tools/m4-lockit-source/capture.py','tools/m4-lockit-source/continuity.py',
                         'tools/m4-lockit-source/header_derivations.py','tools/m4-onexit-review/provider_responses_v2.py',
                         'tools/m4-onexit-review/provider_responses.py'):
            path=ROOT/relative;pin(path,report['files'][str(path.resolve())])
        original_response=pin(ROOT/'tools/m4-lockit-source/responses.py').read_text(encoding='utf-8')
        exact_response=original_response.replace('self.index==5 and w[:5]==(1,5,0,','self.index==4 and w[:5]==(1,4,0,')
        exact_response+='\n# Preserve the explicit contract interface used by the capture adapter.\nB=PRIOR.B\nNEW_CONTRACTS=PRIOR.NEW_CONTRACTS\n'
        need(paths['responses_v3.py'].read_text(encoding='utf-8')==exact_response,'Only actual association index and inherited adapter interface change; API math remains exact')
        bridge=paths['bridge_v2.py'].read_text(encoding='utf-8');tree=ast.parse(bridge)
        function=next(node for node in tree.body if isinstance(node,ast.FunctionDef))
        replacements=[node for node in ast.walk(function)if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and node.func.attr=='replace']
        need(len(replacements)==2 and len([node for node in ast.walk(function)if isinstance(node,ast.Call)and isinstance(node.func,ast.Name)and node.func.id=='exec'])==1,
             'Bootstrap derivative performs only two declared source-text changes')
        need(isinstance(replacements[0].args[0],ast.Name)and replacements[0].args[0].id=='anchor',
             'One exact four-lock bootstrap anchor')
        need(ast.literal_eval(replacements[1].args[0])=="I.need(responses.index==5 and empty['begin']==empty['next']"and
             ast.literal_eval(replacements[1].args[1])=="I.need(responses.index==6 and empty['begin']==empty['next']",
             'Only final producer API count accounts for explicit association')
        need("anchor+'\\n _RESOURCE_ASSOCIATION(m,responses)'"in bridge and
             "Genuine four static lock initializations"in bridge and "namespace=dict(vars(B))"in bridge,
             'Inherited literal bootstrap code retained; association immediately follows exact four-lock source closure')
        basebridge=pin(ROOT/'tools/m4-onexit-review/provider_bridge.py').read_text(encoding='utf-8')
        four=basebridge.index("I.need(len(responses.sections)==4 and responses.index==4")
        producer=basebridge.index('m.invoke_external(0x78004482,0xffffff90,responses)')
        need(four<producer,'Exact old source bootstrap site precedes genuine producer source allocation')
        source=paths['compare_connected_v6.py'].read_text(encoding='utf-8');source_tree=ast.parse(source)
        association_calls=[node for node in ast.walk(source_tree)if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and node.func.attr=='associate_lockit']
        need(len(association_calls)==1 and 'machine,responses=B2.bootstrap('in source,
             'One explicit resource association executed inside inherited bootstrap')
        assoc_func=next(node for node in ast.walk(source_tree)if isinstance(node,ast.FunctionDef)and node.name=='resource_association')
        forbidden={'write','store_bytes','reg','word','project','api_return'}
        need(not any(isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and
                     isinstance(node.func.value,ast.Name)and node.func.value.id=='machine'and node.func.attr in forbidden
                     for node in ast.walk(assoc_func)), 'Association closure cannot seed or mutate guest CPU/State/memory')
        need("equal(bytes(machine.state),association['state']"in source and
             "equal(B.cpu(machine.state),association['cpu']"in source and
             "equal(machine.fx,association['fx']"in source and
             "equal(machine.bytes(page,4096),association['memory'][page]"in source,
             'Whole State/CPU/FX/4096B page equality at both actual association boundaries')
        # Candidate phase records are only comparison observations in all machine mutations.
        for node in ast.walk(source_tree):
            if isinstance(node,ast.Assign)and any(isinstance(target,ast.Attribute)and isinstance(target.value,ast.Name)
                and target.value.id=='machine'and target.attr in ('state','cpu','fx','cursor')for target in node.targets):
                names={n.id for n in ast.walk(node.value)if isinstance(n,ast.Name)}
                need(not names&{'a','b'},'No captured native BEFORE/AFTER phase machine seeds persistent state')
                counts['reviewed_machine_mutations']+=1
        fixed={"CPU BEFORE":"b[36:76]","CPU AFTER":"b[76:116]","FX BEFORE":"b[116:628]","FX AFTER":"b[628:1140]",
               "ENV BEFORE":"b[2164:2192]","ENV AFTER":"b[2192:2220]"}
        for label,extent in fixed.items():
            need(extent in source and ('Whole source '+label)in source,'Immutable physical captured ABI comparison '+label)
        need('b[141540:145044]'in source and 'b[145044:148548]'in source,'Entire3504B State BEFORE/AFTER independently compared')
        need(not report['per_phase_BEFORE_machine_seed']and not report['candidate_AFTER_machine_seed']and
             not report['paired_original_game_equivalence']and not report['initializer_credit']and
             not report['whole_M4_complete']and report['loaded_state2_source_input']and
             not report['native_CS40_opaque_copy']and report['guest_CS24_semantic_output']and not report['native_DllMain_credit'],
             'Source gate preserves declared finite API/oracle scope and separate acceptance')
        expected={'persistent_phases':1488,'persistent124_sequences':12,'whole_page_BEFORE':63984,'whole_page_AFTER':63984,
                  'actual_native_CS_resource_associations':12,'literal_Lockit_CALL_RET_pairs':96,
                  'actual_native_CS40_source_API_relations':96,'literal_indirect_CALL_RET_derivations':72,
                  'actual_native_indirect_CALL_RET_joins':72,'actual_native_indirect_full_State_CPU_FX_boundary_joins':144}
        for key,value in expected.items():need(report['counts'][key]==value,'All actual source observations '+key)
        path=(source_report.parent/'phases.json').resolve();phases=read(path,report['files'][str(path)])
        need(len(phases)==1488,'All actual native table phases emitted')
        cases={(level,seq)for level in ('O0','O2')for seq in range(6)}
        contract=read(ROOT/'reports/m4-lockit-source/recovery-r1/instruction-contracts.json');order=contract['selected_order']
        need(len(order)==124,'Literal original recovered table order')
        for case in cases:
            rows=[row for row in phases if(row['level'],row['sequence'])==case]
            need([row['phase']for row in rows]==list(range(124))and [row['entry']for row in rows]==[row['entry']for row in order],
                 'Each genuine persistent sequence retains complete exact source table order')
            need(rows[-1]['registry_calls']==96,'All96 actual source callback registrations carried to final phase')
        # Bind exact authentic final input pages; no raw BSS or reseeded state2.
        for key in ('loaded_input_page','loaded_IAT_page'):
            pin(prep[key],prep[key+'_sha256']);need(report['files'][str(Path(prep[key]).resolve())]==prep[key+'_sha256'],
                 'Source proof binds entire exact final original loaded provider page')
        counts['whole_43page_endpoint_comparisons']=127968;counts['complete_persistent_sequences']=12
        counts['complete_persistent_phases']=1488;counts['unchanged_guest_resource_associations']=12
        reviewed=dict(source_report=str(source_report),actual_zero_based_resource_API_index=4,actual_resource_generation=5,
            actual_producer_HeapAlloc_index=5,candidate_phase_seeding=False,association_guest_mutation=False,
            whole512FX_comparison=True,whole3504State_comparison=True,whole40CPU_comparison=True,
            full43pages_comparison=True,finite_API_responses=True,old_FP_numerical_oracle_scope=report['old_numerical_oracle_scope'])
        passed=True
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        (out/'reviewed-boundaries.json').write_text(json.dumps(reviewed,indent=2)+'\n',encoding='utf-8');pin(out/'reviewed-boundaries.json')
        receipt=dict(passed=passed,scope='Independent bounded current persistent source observer/association review and final actual source receipt; entire original/native archive observations remain attributed to source reader',
                     native_capture_archive_opened=False,original_capture_archive_opened=False,
                     native_DllMain_credit=False,initializer_credit=False,counts=dict(counts),files=pins)
        path=out/'report.json';path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(passed=passed,report_sha256=sha(path),counts=dict(counts))))


if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])
