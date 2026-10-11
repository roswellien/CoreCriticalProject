"""Independent bounded source/receipt review, without reopening control data."""
from pathlib import Path
import ast,hashlib,json,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    out=R/'reports/m4-widget-original-review/controls-r1'
    if out.exists():raise ValueError('Fresh additive review required')
    files={}
    def pin(p,h=None):
        p=Path(p).resolve()
        if p.suffix.lower()in('.mwb','.zip'):raise ValueError('No capture archive reader')
        v=sha(p)
        if h is not None and h!=v:raise ValueError('Exact physical bounded input '+str(p))
        files[str(p)]=v;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    qpath=pin(R/'reports/m4-widget-native/controls-verification-r2/report.json','44760b4e05decc5a63204fa24fab93158c390be0b7d5a4b17d338e15546936ab');q=json.loads(qpath.read_bytes())
    if not q['passed']or q['archive_reader_opened']:raise ValueError('Passed current bounded ordinary-file gate')
    counts=q['counts']
    expected={'whole_physical_bootstrap_sentinel_instructions':2,'exact_actual_bootstrap_sentinel_store_joins':32,'exact_first_refusal_relations':16,'whole_exported_retry_files_equal':47968,'whole_ASM_FX512_ENV28_restore_pairs':48,'actual_poisoned_cleanup_relations':16}
    if any(counts.get(k)!=v for k,v in expected.items()):raise ValueError('Exact current measured extents')
    for k in('partial_fault_State_register_prediction','source_scalar_register_value_prediction','permission_bytes_observed','hidden_Runtime_vector_bytes_observed','bootstrap_and_cleanup_source_execution_modeled'):
        if q[k]is not False:raise ValueError('Keep exact bounded claim '+k)
    parent=pin(R/'tools/m4-widget-native/check_controls.py','40f7b545055c86f4b183c164b33f40dd0c240c43d6a3ba18a49ad4a8a9cd028a')
    checker=pin(R/'tools/m4-widget-native/check_controls_v2.py',q['files'][str((R/'tools/m4-widget-native/check_controls_v2.py').resolve())]);derivation=pin(R/'tools/m4-widget-native/derive_check_controls_v2.py',q['files'][str((R/'tools/m4-widget-native/derive_check_controls_v2.py').resolve())])
    p=parent.read_text();t=checker.read_text();ast.parse(t)
    # Independently recover exactly the two literal replacement assignments
    # from the frozen recipe; do not run it or import its checker.
    tree=ast.parse(derivation.read_text());pairs=[];needle=None
    for node in tree.body:
        if isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            n=node.targets[0].id
            if n=='needle':needle=ast.literal_eval(node.value)
            elif n=='replacement':
                if needle is None:raise ValueError('Ordered recipe hunk')
                pairs.append((needle,ast.literal_eval(node.value)))
    if len(pairs)!=2:raise ValueError('Exactly two bounded bootstrap additions')
    rebuilt=p
    for a,b in pairs:
        if rebuilt.count(a)!=1:raise ValueError('Exact parent occurrence')
        rebuilt=rebuilt.replace(a,b,1)
    rebuilt=rebuilt.replace('bootstrap_and_cleanup_source_execution_modeled=False,hardware_scope=',"bootstrap_and_cleanup_source_execution_modeled=False,finite_bootstrap_effects='Only two physically authenticated MOV DWORD sentinel stores joined to actual source ledger; entire remaining own Game input remains exact',hardware_scope=")
    if rebuilt!=t:raise ValueError('No changed legacy control/refusal/retry predicates')
    causes_path=R/'reports/m4-widget-native/controls-verification-r2/actual-causes.json';causes=read(causes_path,q['files'][str(causes_path.resolve())])
    if len(causes)!=16 or {(v['level'],v['mode'])for v in causes}!={(l,m)for l in('O0','O2')for m in range(1,9)}:raise ValueError('All distinct actual causes retained')
    reasons={1:'Flat source DS/ES/SS/current owned minimal TIB',2:'Source forward-string DF input',3:'Exact current owning IAT operand preimage',4:'Complete physical widget source instruction bytes',5:'Guest access permission denied',6:'Guest access permission denied',7:'Guest access permission denied',8:'Exact selected source root and actual Runtime route'}
    for c in causes:
        m=c['mode'];target=0x40ef50 if m==8 else 0x40e250;site=c['actual_Runtime_fault_site']
        if c['target']!=target or(m!=6 and site!=target):raise ValueError('Exact runtime target/site')
        if c['actual_first_reason']!=f'memory_access site=0x{site:08x} target=0x{target:08x}: Admitted native callback failed: {reasons[m]}':raise ValueError('Exact literal first cause')
        if c['actual_retry_reason']!=f'poisoned site=0x{site:08x} target=0x{site:08x}: Earlier admitted callback failed; create a new context':raise ValueError('Exact same poisoned-context refusal')
        if c['whole_hidden_Runtime_or_permissions_claim']is not False:raise ValueError('No hidden state equality claim')
        if m in(5,7):
            if c['last_denied_write']is None or c['attempted_write_committed']is not False:raise ValueError('Actual uncommitted final write retained')
        elif c['last_denied_write']is not None:raise ValueError('No invented denied write')
    for rel,h in(('reports/m4-widget-native/controls-execution-r1/report.json',q['execution_sha256']),('reports/m4-widget-native/controls-preparation-r1/report.json',q['preparation_sha256']),('reports/m4-widget-native/controls-build-r2/build.json',q['build_sha256'])):
        j=read(R/rel,h)
        if not j['passed']:raise ValueError('Exact actual current writer/build receipt')
    # The complete execution/ordinary manifest was checked by the producer;
    # this bounded review pins that result and does not repeat its data reader.
    for rel in('reports/m4-widget-native/service-preparation-r3/session_impl.inc','reports/m4-widget-native/preparation-r6/component.cpp','reports/m4-widget-native/preparation-r6/contracts.json','runtime/memory/guest_memory.cpp','MW3/Mech3.exe'):
        p=R/rel;pin(p,q['files'][str(p.resolve())])
    pin(__file__);out.mkdir();report=dict(passed=True,scope='Independent bounded exact checker delta, actual retained first causes and current receipt review; no second ordinary control dataset or archive reader',controls_validation_sha256=sha(qpath),counts_reviewed=expected,exact_first_causes_reviewed=16,legacy_checker_predicates_preserved=True,whole_raw_retry_recomputed=False,whole_partial_fault_CPU_State_claim=False,hidden_Runtime_or_permission_equality_claim=False,caller_hardware_scope=q['hardware_scope'],archive_reader_opened=False,initializer_credit=0,files=files)
    p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p))))
if __name__=='__main__':main()
