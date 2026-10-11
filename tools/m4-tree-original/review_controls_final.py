"""Bind the independent control source review to the sealed causal audit.

Only small receipts, source and retained first-cause rows are read. No archive.
"""
from pathlib import Path
import hashlib, json, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
    if not v:raise ValueError(s)
def main(name):
    out=R/'reports/m4-tree-original'/name;need(not out.exists(),'Fresh final controls review');out.mkdir(parents=True);pins={}
    def pin(p,h=None):
        p=Path(p).resolve();need(p.suffix.lower()!='.mwb','No archive reader');a=sha(p);need(h is None or a==h,'Exact physical control audit input '+str(p));pins[str(p)]=a;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    src=read(R/'reports/m4-tree-original/control-source-review-r1/report.json','1b5502d9ea12282685c8fa7bddc0fc86027f85b4be55ccfea77b60282f7686db')
    path=R/'reports/m4-tree-review/controls-validation-r3/report.json'
    audit=read(path,'a369de58c7ecdd9b6494a57c74b8e135f85ac56d3588c06fda9e1093ed8eb6e2')
    need(src['passed']and audit['passed']and audit['reader_closed'],'Source and complete causal gates passed, archive reader closed')
    for k in('execution_sha256','build_sha256','native_preparation_sha256'):need(src[k]==audit[k],'Exact current control lineage '+k)
    for k,v in dict(levels=2,registered_positive_roots=2,same_session_refusals=36,exact_owner_service_denials=8,private_witness_denials=12,source_machine_permission_denials=12,actual_native40_denials=2,causal_denials=34,rich_caller_hardware_pairs=72,actual_cleanup_hardware_pairs=72,whole_retry_history_joins=1368,whole_retry_page_endpoint_joins=4680,whole_owner_page_source_replays=78).items():need(audit['counts'][k]==v,'Complete measured causal extent '+k)
    need(all(audit[k]for k in('wholeState_retry','wholeCPU_retry','wholeFX_retry'))and not audit['full_caller_FX512_equality_claim']and not audit['source_API_volatile_equality_claim']and audit['initializer_credit']==0,'Exact bounded equality and no initializer credit scope')
    for q,h in src['files'].items():pin(q,h)
    for q,h in audit['files'].items():
        p=Path(q)
        if p.suffix.lower() in('.py','.hpp','.inc','.cpp','.s'):
            pin(p,h)
    causes=read(path.parent/'actual-causes.json')
    need(len(causes)==34 and len({(x['level'],x['scenario'])for x in causes})==34,'Both levels have all17 actual first-cause rows')
    reasons={1:'Owned tree operand cannot use a foreign, expired or non-MFC allocation',2:'Tree access requires exact source operand and current requested owner generation',3:'Tree access retains its exact source PC, role occurrence, offset and causal order',4:'Tree access retains its exact source PC, role occurrence, offset and causal order',5:'Tree observer changed private scratch or invocation witnesses',6:'Tree observer changed private scratch or invocation witnesses',7:'Installed source FS predecessor/handler and active private frame identity',8:'FS observer changed private source-frame/chain witnesses',9:'FS observer changed private source-frame/chain witnesses',10:'Lockit observer changed private resource/source witnesses',11:'Exact tree source import definition and live Lockit resource required',12:'Only committed source/API/research effects may change owned locale pages',13:'Heap creation observer changed State/FX or ownership/lifecycle ledgers',14:'Distinct live loaded Lockit source/native generation and recursive depth required',15:'Lockit observer changed actual native resource bytes',16:'Only committed source/API/research effects may change owned locale pages',17:'Checked actual source locale/parser store fault'}
    for level in('O0','O2'):
        rows={x['scenario']:x for x in causes if x['level']==level};need(set(rows)==set(range(1,18)),'All actual scenario causes '+level)
        for case,row in rows.items():
            need(row['reason']==reasons[case]and row['exact_owner_service']==(case<=4),'Explicit bounded measured first predicate, scenario'+str(case))
            if case<=4:need(row['hook_point']==86 and row['actual_State_PC']==row['first_fault_PC']==0x4bab44,'Real public owner service seam')
            if case==7:need(row['first_fault_PC']==0x4ba370,'Active FS mutation trips actual source restoration integrity before conservation')
            if case==15:need(row['hook_point']==41,'Native40 mutation after actual Enter')
    checker=pin(R/'tools/m4-tree-review/check_controls_v3.py').read_text()
    need("'<2IQ2I'"in checker,'Exact24-byte source access row with fullQword value')
    need('finally:a.close()'in checker and 'first[4272:7776]==sample[768:4272]'in checker,'Reader closes and same-session retry inherits whole cleaned machine')
    pin(__file__)
    report=dict(passed=True,scope='Independent light final control review binds actual linked source scope to all34 measured first causes and36 whole-machine same-session retries',source_review_sha256=sha(R/'reports/m4-tree-original/control-source-review-r1/report.json'),controls_validation_sha256=sha(path),execution_sha256=src['execution_sha256'],build_sha256=src['build_sha256'],native_preparation_sha256=src['native_preparation_sha256'],counts=audit['counts'],exact_first_cause_rows=34,scenario7_source_FS_integrity_before_conservation=True,full_guest_retry=True,full_host_FX512_equality_claim=False,archive_reader_opened=False,initializer_credit=0,files=pins)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),files=len(pins))))
if __name__=='__main__':main(sys.argv[1])
