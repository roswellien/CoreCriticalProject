"""Seal the unchanged independent native/checker identities and source review."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized,verify_manifest
from paths import publish_bytes,workspace_path
from transport import read,need

def main(directory):
    base=ROOT/'reports/m4-crt-allocation-review';out=workspace_path(directory,reports=True)
    need(out.parent==base and not out.exists(),'Fresh independent source/ABI seal')
    check_path=base/'check-r3/report.json';check=read(check_path)
    need(sha_file(check_path)=='3aad1b66ba450b2f3493d8b5198ef4f5bc28d6ac83a29994375984d0a9f21abe' and check['passed'],'Frozen successful raw checker')
    native_path=Path(check['native_path']);native=read(native_path)
    need(sha_file(native_path)==check['native_sha256'] and native['passed'] and not native['native_rerun'],'Exact once-run native corpus')
    build=read(native['build_path']);need(sha_file(native['build_path'])==native['build_sha256'] and build['passed'],'Exact frozen independent build')
    author=read(build['author_build']);prep=read(ROOT/'reports/m4-crt-allocation/preparation-r7/report.json')
    need(sha_file(build['author_build'])==build['author_build_sha256'] and author['passed'] and prep['passed'],'Exact frozen author readiness')
    need(build['entry_objects']==author['entry_objects'] and len(build['entry_objects'])==64 and len(prep['reused_object_hashes'])==38 and prep['new_guest_objects']==26,'64 byte-identical literal guest objects;38 accepted reused')
    need(all(build['entry_objects'].get(p)==h for p,h in prep['reused_object_hashes'].items()) and build['libraries']==prep['reused_library_hashes'],'Unchanged accepted COFFs and two frozen FDIV libraries')
    need(prep['new_compiled_source_bytes']==532 and prep['new_unique_source_identity_bytes']==469 and prep['overlapping_compiled_source_bytes']==63,'No double credit for overlapping literal entry tails')
    need(prep['State_bytes']==3504 and prep['FX_bytes']==512 and prep['CPU_bytes']==40 and not prep['State_reseed_after_writer'],'Full carried State/FX/CPU ABI')
    files=dict(check['files'])
    def pin(p):
        p=Path(p).absolute();key=normalized(str(p));h=sha_file(p);need(key not in files or files[key]==h,'Conflict-free sealed dependency identity');files[key]=h;return h
    for p in (check_path,native_path,Path(native['build_path']),Path(__file__),Path(__file__).parent/'README.md'):pin(p)
    history={}
    for label in ('build-preflight-r1','check-r1','check-r2'):
        p=base/label/'report.json';history[label]={'path':str(p),'sha256':pin(p),'success_credit':False}
    for p in (ROOT/'tools/m4-crt-allocation-review/check.py',ROOT/'tools/m4-crt-allocation-review/check_v2.py'):pin(p)
    closure=verify_manifest(files)
    source_review=dict(passed=True,private_full64_HANDLE_and_pointer=True,guest_token_separate=True,
        final_posthook_clone_preflight=True,active_original_IAT_guards=True,immutable_physical_forwarder_witness=True,
        exact_original_carried_FS_upper_page_admission=True,State_reseed=False,
        source_api_stdcall_return_reads=True,source_normal_free_and_cleanup_distinct=True,
        destroy_refuses_live_owned_allocation=True,unobserved_OS_failure_execution_claimed=False,
        complete_binding_and_literal_guest_bodies_unchanged_in_independent_fixture=True,
        hand_review_scope='Frozen preparation-r7 allocation.hpp/binding/operations/forward_identity and64 reused/new COFF receipts; independent observer/fixture changes only')
    report=dict(passed=True,scope='Independent compiled/source/ABI and actual finite ownership/HW review; no game/full-M4 credit',
        native_path=str(native_path),native_sha256=check['native_sha256'],native_execution_path=str(native_path),native_execution_sha256=check['native_sha256'],
        check_path=str(check_path),check_sha256=sha_file(check_path),build_path=native['build_path'],build_sha256=native['build_sha256'],
        levels=native['levels'],metrics=check['metrics'],source_review=source_review,
        reused_guest_objects=38,new_guest_objects=26,guest_objects_total=64,new_unique_source_bytes=469,
        history=history,files=files,current_physical_closure=closure,native_rerun=False,
        game_launched=False,original_executed=False,full_CRT_complete=False,whole_M4_complete=False)
    out.mkdir(parents=True);publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','levels')}))

if __name__=='__main__':main(*sys.argv[1:])
