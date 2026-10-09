"""Seal the causal raw-control audit together with exact persistent source copies."""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import verify_manifest


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def seal(auditpath,digest,name):
    out=ROOT/'reports/m4-strings-control-audit'/name
    assert not out.exists();out.mkdir(parents=True)
    pins={};passed=False;counts={}
    def pin(p,h=None):
        p=Path(p).resolve();value=sha(p);assert h is None or value==h,(p,h,value)
        assert str(p)not in pins or pins[str(p)]==value
        pins[str(p)]=value;return p
    try:
        audit=json.loads(pin(auditpath,digest).read_bytes());assert audit['passed']and not audit['findings']
        assert len(audit['cases'])==28 and audit['checks']['all_actual_controls_present']
        for p,h in audit['physical_inputs'].items():pin(p,h)
        copiespath=pin(ROOT/'reports/m4-strings-review/control-source-snapshot-r2/report.json',
                       'd895dcf4509b6f3fe5f0dadd5028a5d7ef0a03a53a4937309962a09c51932f15')
        copies=json.loads(copiespath.read_bytes());assert copies['passed']and len(copies['copied_sources'])==9
        assert copies['actual_control_report_sha256']=='80031604b0af92783eb12cce2e401d2188fe08b660c5e142303f1bb4380c3a92'
        for row in copies['copied_sources']:
            original=pin(row['source'],row['sha256']);copy=pin(row['copy'],row['sha256'])
            assert original.read_bytes()==copy.read_bytes()
        for p,h in copies['files'].items():pin(p,h)
        for path in(pin(__file__),pin(ROOT/'tools/m4-strings-control-audit/audit_v9.py')):
            target=out/'sources'/path.name;target.parent.mkdir(exist_ok=True)
            target.write_bytes(path.read_bytes());pin(target,sha(path));assert target.read_bytes()==path.read_bytes()
        causal=[r for r in audit['cases']if r['case']]
        assert len(causal)==26 and all(not r['result'] and r['hits']==1 for r in causal)
        iat=[r for r in causal if r['case']==12]
        assert len(iat)==2 and all(r['completed_roots']==20 and r['registry_fault']['pc']==0x48eb22
                                  and r['registry_fault']['address']==0x5bb670
                                  and r['registry_fault']['reason']=='Exact string source import relocation'for r in iat)
        counts=dict(actual_control_cases=28,actual_attempts_including_poisoned_retries=56,causal_refusals=26,
                    exact_machine_owner_retries=28,strict_outside_hardware_pairs=sum(r['strict_outside_hardware_pairs']for r in audit['cases']),
                    partial_4byte_copy_full_owner_mirrors=sum(r.get('full_owned_mirror_partial_commit_verified',False)for r in audit['cases']),
                    fullwidth_native_corruption_guard_refusals=sum(r['case']==13 for r in audit['cases']),
                    corrected_exact_IAT_guard_refusals=2,physical_HeapDestroy_identity_triplets=28,persistent_reviewer_source_copies=9,
                    persistent_auditor_source_copies=2)
        passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        report=dict(schema='mw34-independent-string-control-audit-final-v1',passed=passed,
                    audit=str(auditpath),audit_sha256=digest,
                    corrected_controls_sha256='80031604b0af92783eb12cce2e401d2188fe08b660c5e142303f1bb4380c3a92',
                    corrected_build_sha256='4b15dddb158bda59c646f1a1a2c66eff3d7f7bde148349844240aa29b1bbf393',
                    persistent_source_gate_sha256='d895dcf4509b6f3fe5f0dadd5028a5d7ef0a03a53a4937309962a09c51932f15',
                    counts=counts,source_bodies_modified=False,API_response_injection=False,AFTER_state_fabrication=False,
                    superseded_IAT_scope='Earlier audit-r8 and controls-r3 did not prove changed-IAT guard causality; exact revised case12 is mandatory here. Previous receipts remain intact.',
                    no_new_forced_native_move_claim=True,initializer_credit=False,whole_M4_complete=False,
                    files=pins,physical_closure=verify_manifest(pins))
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        (out/'pins.json').write_text(json.dumps(dict(files=pins|{str(out/'report.json'):sha(out/'report.json')}),indent=2)+'\n')
        print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'),counts=counts)))


if __name__=='__main__':seal(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
