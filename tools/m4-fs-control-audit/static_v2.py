"""Independent read-only FS boundary/control admission review. No runtime credit."""
import hashlib,json,sys,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def need(value,message):
    if not value:raise ValueError(message)
def main(directory):
    out=Path(directory).resolve();need(out.parent==ROOT/'reports/m4-fs-control-audit' and not out.exists(),'Fresh independent FS review');out.mkdir(parents=True);files={}
    def pin(path,expected=None):
        path=Path(path).resolve();digest=sha(path);need(expected is None or digest==expected,'Frozen physical input: '+str(path));files[str(path)]=digest;return path
    home=ROOT/'reports/m4-fs-native/preparation-r2';receipt=json.loads(pin(home/'report.json','b9580fb47ba9cfb59505dcfedbba0b6408021349f499b55870ef84d31c7d14b5').read_bytes());need(receipt['passed'],'Passed preparation; runtime remains separate')
    interface=json.loads(pin(home/'fs-interface.json').read_bytes());ops=pin(home/'fs_operations.inc').read_text();writes=pin(home/'locale_batch_operations.inc').read_text();before=pin(ROOT/'reports/m4-fs-native/preparation-r1/locale_batch_operations.inc').read_text()
    start=writes.index('void Binding::write(unsigned a,std::uint64_t v,unsigned n)');end=writes.index('unsigned char Binding::batch_undefined()',start);body=writes[start:end]
    anchors=['runtime.memory().write({a}','expected_store(a,&v,n)',';source_access(a,v,n,true)','fs_write_after(a,v,n)','fs_owner_after(a,v,n,true)'];positions=[body.index(x) for x in anchors];need(positions==sorted(positions),'Observer after-hooks follow actual store, mirror and source ledger commit')
    need(body.count('fs_write_after(')==1,'Single exact source anchor')
    old_start=before.index('void Binding::write(unsigned a,std::uint64_t v,unsigned n)');old_end=before.index('unsigned char Binding::batch_undefined()',old_start);oldbody=before[old_start:old_end]
    need(oldbody.index('fs_write_after(a,v,n)')<oldbody.index('runtime.memory().write({a}'),'Failed predecessor genuinely observed before commit')
    fs_frames=[(0x4e78d0,0x5b986b,0x4e78d7,0x4e78de,0x4e7997,0x4e799f,0x4e79aa),(0x48f290,0x5b5233,0x48f297,0x48f29e,0x48f353,0x48f360,0x48f36b),(0x4d48f0,0x5b8538,0x4d48f7,0x4d48fe,0x4d492a,0x4d4948,0x4d4953)]
    need(interface['frames']==[list(x) for x in fs_frames],'Exact three literal frame geometries')
    need(interface['native_TIB_base']==0x7ffde000 and interface['native_sentinel']==0xffffffff,'Explicit owned-native provenance')
    for phrase in ['std::uint64_t(a->guest)+a->requested','i.owner_root==owner->words[2]','i.owner_call==owner->words[4]','address==a->guest+i.offset','fs_active_.back()','previous<=head','w[17]!=value','std::memcmp(actual.data()']:
        if phrase=='std::memcmp(actual.data()':continue
        need(phrase in ops,'Bounded owner/active-chain check retained: '+phrase)
    # No host TEB import or pointer dereference belongs to the chain bookkeeping.
    for phrase in ['__readfsdword','NtCurrentTeb','GetThreadContext','SetThreadContext']:need(phrase not in ops,'No host-chain seed/control')
    inputs=json.loads(pin(ROOT/'reports/m4-fs-source/allocation-interface-r1/allocation-inputs.json').read_bytes());need(len(inputs)==10,'Actual geometry has ten allocation sites')
    shared=[x for x in inputs if x['shared_registry_role']=='append_node'];need(len(shared)==5 and all(x['CALL_pc']==0x4e795c for x in shared),'Five genuine append CALLs, no root-count owner inference')
    free=pin(home/'mfc_operations.inc').read_text();need('!fs_allowed_cross(address,bytes)' in free,'Cross-root requested stores require exact FS owner proof')
    pin(__file__);pin(ROOT/'tools/m4-pipeline/manifests.py')
    (out/'source-anchor.diff').write_text(''.join(difflib.unified_diff(oldbody.splitlines(True),body.splitlines(True),fromfile='failed-prep1-write',tofile='prep2-write')));pin(out/'source-anchor.diff')
    report={'passed':True,'native_executed':False,'original_executed':False,'initializer_credit':0,'source_anchor_order':anchors,'frame_specs':fs_frames,'source_allocation_sites':10,'shared_append_sites':5,'normal_shared_counts':[1,1,2,3,4,5],'required_runtime_controls':['Every point80..87 throw must retain exact source prefix/State/CPU/FX/ENV and raw ownership; first refusal stage is captured before cleanup.','RO install/restore tests must reach literal source memory store, retaining all pre-store committed stack/record bytes.','Mutation tests must classify the guard actually reached: State observer versus chain/provider/page ownership, without claiming a later guard.','Nested parentIndexPlus1/nonzero controls must preserve both complete twelve-byte records and exact inner-to-outer FS0 relationship.','Precise prior live node write tests require literal root/PC/owner-generation/offset proof and complete native/guest partial prefix equality.','Cleanup must prove each actual allocation freed once using source MFC825/CRTfree on normal path or explicit private safeguard on fault, followed by physical same-HANDLE HeapDestroy.','Retry must preserve complete captured machine/owned bytes, all source/native ledger counts and physical identities; no new producer calls.','Fault-after-install does not authorize invented FS unwind: pending source virtual chain may remain; exception-handler/TLS semantics are excluded.','Isolated bootstrap+six root owner counts are derived from actual allocation/API ledger; full109 totals are a separate normal execution gate.'],'scope':'Read-only static admission/control plan; actual O0/O2 isolated fixture and complete109 semantic gates remain required.','files':files,'current_physical_closure':verify_manifest(files)}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'sha256':sha(out/'report.json'),'native_executed':False}))
if __name__=='__main__':main(*sys.argv[1:])
