"""Independent bounded source/receipt review of actual formatter controls.

No capture is opened; runtime outcomes are authenticated bounded exports from
the separate executed checker. Public API counterfactuals and private observer
mutations retain distinct scopes.
"""
from pathlib import Path
import collections,hashlib,json,sys,traceback
R=Path(__file__).resolve().parents[2];PINS={}
def need(v,s):
    if not v:raise ValueError(s)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();need(p.suffix.lower()!='.mwb'and p.stat().st_size<20*1024*1024,'Bounded review input; no archive')
    v=sha(p);need(h is None or h==v,'Actual source/receipt identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable source identity');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
    out=R/'reports/m4-formatting-original'/name;need(not out.exists(),'Fresh additive independent review');out.mkdir(parents=True);passed=False;counts={}
    try:
        folder=R/'reports/m4-tree-review/formatting-controls-validation-r2'
        validation=read(folder/'report.json','a6f755471aec327792ffc9e379cc0ba8001b7e02f0416cc47e99acbda073933c')
        execution_path=R/'reports/m4-tree-review/formatting-controls-execution-r1/report.json'
        execution=read(execution_path,validation['execution_sha256']);need(validation['passed']and execution['passed'],'Both genuine levels passed and reader closed')
        build=read(execution['build_path'],execution['build_sha256']);need(build['passed']and execution['build_sha256']==validation['build_sha256'],'Actual executed build')
        prep=read(build['preparation'],build['preparation_sha256'])
        native=read(prep['native_preparation'],prep['native_preparation_sha256'])
        need(prep['native_preparation_sha256']==build['native_preparation_sha256']==validation['native_preparation_sha256']==execution['native_preparation_sha256']=='bbe18a53a6c8c400f3274e470a28ded84d7c7c45c4fc860cf5e598ed4d5730aa','Exact finite formatter native15 current build')
        need(prep['control_scenarios']==14 and prep['control_attempts']==28 and prep['actual_Runtime_selected_call'],'Real registered Runtime path')
        fixture_path=Path(build['preparation']).parent/'fixture.cpp';fixture=pin(fixture_path,build['sources'][str(fixture_path.resolve())]).read_text()
        hook_path=fixture_path.with_name('control_hooks.hpp');hooks=pin(hook_path,build['sources'][str(hook_path.resolve())]).read_text()
        checker_path=R/'tools/m4-tree-review/check_formatting_controls_v2.py';checker=pin(checker_path,validation['files'][str(checker_path.resolve())]).read_text()
        hardware_path=R/'tools/m4-tree-review/check_controls_v3.py';hardware=pin(hardware_path,validation['files'][str(hardware_path.resolve())]).read_text()
        prep_source=pin(R/'tools/m4-tree-review/prepare_formatting_controls.py').read_text()
        pin(R/'tools/m4-tree-review/formatting_control_hooks.hpp')
        need('mw34_tree_controls::reset(n);Context c('in fixture and 'attempt(c,w,0);c.registry().test_hook=nullptr;attempt(c,w,1);'in fixture,'Fresh per-scenario Context; exact same Context/Session for retry')
        need('if(t.retry)t.c->registry().replay(tree_root)'in fixture and 'else{t.okay=t.c->invoke_selected_table('in fixture,'Real first schedule and same cleaned Session public replay')
        for token in ['sample.state_before==sample.state_after','sample.fx_before==sample.fx_after','sample.cpu_before==sample.cpu_after','c.registry().finish();','Every actual owner guest alias unmapped by cleanup']:
            need(token in fixture,'Actual whole-machine retry / cleanup predicate '+token)
        for token in ['pc!=0x7801042a','(void)m4_onexit::write(s.token(),address,value,1)','if(selected==2)address=owner+8','if(selected==3)address=owner+4096','value^=0x80','(void)m4_onexit::read(s.token(),address,4)','const auto address=0x780103fa+8','const_cast<std::byte*>(b.data())[at]^=std::byte{1}','private_before.assign','private_after.assign']:
            need(token in hooks,'Real scoped public source API or actual private witness intervention '+token)
        need('formatting-status.bin' in hooks and 'base=r[3];owner=r[4];generation=r[5]'in hooks,'Current actual allocation identity, not predicted pointer')
        operations_path=Path(prep['native_preparation']).parent/'locale_batch_binding.inc';operations=pin(operations_path,native['files'][str(operations_path.resolve())]).read_text()
        need('const auto calls=formatting_calls_'in operations or 'formatting_calls_'in operations,'Private current witnesses in real Binding')
        need('Formatter observer changed private invocation or source owner witnesses'in operations,'Private observer conservation is an actual native predicate')
        causes=read(folder/'actual-causes.json');need(len(causes)==26,'All bounded actual first reasons retained')
        by={(x['level'],x['scenario']):x for x in causes};need(len(by)==26 and set(by)=={(l,n)for l in ('O0','O2')for n in range(1,14)},'Complete unique two-level causal cases')
        expected={1:'Formatter exact malloc generation, requested bounds and finite operand order',2:'Formatter exact malloc generation, requested bounds and finite operand order',3:'Current source allocation token/extent/generation required',4:'Formatter exact literal byteflow and ordered source owner offset',5:'Formatter observer changed private invocation or source owner witnesses',6:'Formatter observer changed private invocation or source owner witnesses',7:'Formatter observer changed private invocation or source owner witnesses',8:'Formatter observer changed private invocation or source owner witnesses',9:'Formatter exact narrow table branch and current source index',10:'Exact formatter source import cell and owning read PC',11:'Checked actual source locale/parser store fault',12:'Heap creation observer changed State/FX or ownership/lifecycle ledgers',13:'Only committed source/API/research effects may change owned locale pages'}
        for(l,n),row in by.items():
            need(row['reason']==expected[n]and row['public_source_service']==(n<=4 or n==9),'Measured first reason and precise public/private scope')
            need(row['reason']in checker,'Executed checker authenticates exact first predicate')
            if n<=4:need(row['State_PC']==row['fault_PC']==0x7801042a and row['hook_point']==90,'True literal MOV [EDX],AL counterfactual')
            if n==9:need(row['State_PC']==0x7800fcef and row['hook_point']==89 and row['intervention'][2:4]==[2,0x78010402],'Actual narrow dispatch table source read')
        c=validation['counts'];need(c['causal_denials']==26 and c['same_session_refusals']==28 and c['registered_positive_roots']==6 and c['public_source_operand_denials']==8 and c['private_witness_denials']==8 and c['public_dispatch_denials']==2 and c['source_IAT_permission_FX_frame_denials']==8,'Executed scope counts')
        need(validation['reader_closed']and validation['whole_guest_State_retry']and validation['whole_guest_CPU_retry']and validation['whole_guest_FX_retry']and not validation['full_caller_FX512_equality_claim'],'Complete guest machine versus architectural host FP scope')
        need('old+suffix)==a.data(live+suffix)==a.data(clean+suffix)'in checker and 'first[4272:7776]==sample[768:4272]'in checker,'Same cleaned session full histories and first-cleaned source machine carry')
        need('full_caller_FX512_equality_claim=False'in checker and 'hardware(sample[8880:9424],sample[9424:9968],True)'in checker,'Architectural host FP boundary explicitly scoped')
        counts={k:c[k]for k in ('causal_denials','same_session_refusals','registered_positive_roots','whole_retry_history_joins','whole_retry_page_joins','whole_owner_backing_byteflows','source_owner_stores','public_source_operand_denials','private_witness_denials','public_dispatch_denials','source_IAT_permission_FX_frame_denials')};passed=True
    except Exception:traceback.print_exc()
    pin(__file__)
    result={'passed':passed,'scope':'Independent bounded source and executed receipt review; controls concern formatter3 native15, not new mixed/FCOS/full130. Actual public source API admissions, generic allocation-token refusal, private vector integrity, permission/IAT/FX/frame denial remain separate. No capture reopened or direct archive outcome recomputation.', 'execution_sha256':validation['execution_sha256']if'validation'in locals()else None,'build_sha256':validation['build_sha256']if'validation'in locals()else None,'native_preparation_sha256':validation['native_preparation_sha256']if'validation'in locals()else None,'counts':counts,'archive_reader_opened':False,'same_session_whole_State_CPU_FX_retry':passed,'full_caller_FX512_equality_claim':False,'private_witness_as_public_operand_claim':False,'generic_formatter_claim':False,'initializer_credit':0,'files':PINS}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':passed,'report':str(out/'report.json'),'sha256':sha(out/'report.json'),'counts':counts}));return 0 if passed else 1
if __name__=='__main__':sys.exit(main(sys.argv[1]))
