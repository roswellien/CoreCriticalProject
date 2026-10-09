"""Fresh static closure audit of filename prep8/build7 after frame repairs.

The frozen predecessor audit is reused only for physical/source/compiler/COFF
association checks. This revision separately reviews the immutable frame and
observer lifecycle source contract. No worker or original game code is run.
"""
import difflib
import importlib.util
import json
import ntpath
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OLD = Path(__file__).with_name('audit.py')
OLD_SHA = 'e4e01b6be2a2a24dc02c7495ca70d8e0fbc6e115b4657e223b76d99c2bfec05a'
BUILD_SHA = '1868574163cdbce4491afe2217688ef549189f184e20549e31f68e44930fb1d5'
PREP_PINS_SHA = '4646d4d7f8d9c969b623a41527f0c0eb34394406f7a39d69f28f6751e062ca3a'


def main():
    import hashlib
    def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    def need(ok, why):
        if not ok: raise ValueError(why)
    need(sha(OLD) == OLD_SHA, 'Preserved association audit changed')
    spec = importlib.util.spec_from_file_location('frozen_filename_association_audit', OLD)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    base = ROOT / 'reports/m4-crt-filename'
    prep = base / 'preparation-r8'
    build = base / 'build-r7'
    out = base / 'independent-contract-r2'
    association_name = 'independent-contract-r2-source-association'
    need(not out.exists(), 'Fresh independent contract output required')
    need(sha(build / 'build.json') == BUILD_SHA and sha(prep / 'pins.json') == PREP_PINS_SHA,
         'Exact final candidate/preparation identities')
    old.main('preparation-r8', 'build-r7', association_name)
    out.mkdir()
    header = (prep / 'filename.hpp').read_text()
    body = (prep / 'filename_binding.inc').read_text()
    old_body = (base / 'preparation-r6/filename_binding.inc').read_text()
    before_guard = body[body.index('void Binding::invoke'):body.index(' used=true;active=true;')]
    need(before_guard.index('guard();') < before_guard.index('caller_error=') < before_guard.index('errors.restored='),
         'Current owner validation must precede stale Binding metadata writes')
    need('Witness actual_witness_{};unsigned admitted_frame_{};' in header and
         'private:' in header[:header.index('unsigned admitted_frame_{};')], 'Private admission/witness storage')
    need('used=true;active=true;admitted_frame_=context.frame-44;frame=admitted_frame_;' in body,
         'Private admitted frame is captured once on admitted invoke')
    need(body.count('admitted_frame_=') == 1, 'No later private admission-frame write')
    need('frame!=admitted_frame_||context.frame!=admitted_frame_+44' in body,
         'Mutable public and Context frame must close against private frame')
    need('context.state.gpr.rsp.dword=admitted_frame_+16;' in body and
         'context.event(5,mg::import_return,admitted_frame_+16,result);' in body,
         'Guest RET ESP and route use private immutable admission')
    need('if(!used||!active||api_called||stored||returned||stopped||failed||stage!=1||hook_count!=1)' in body,
         'Observer point1 exact pre-API admission lifecycle')
    for term in ('point==2&&active&&!stored&&!returned&&!stopped',
                 'point==3&&active&&stored&&!returned&&!stopped',
                 'point==4&&active&&stored&&returned&&!stopped',
                 'point==5&&!active&&stored&&returned&&!stopped'):
        need(term in body, 'Exact lifecycle closure: ' + term)
    for point in (2, 3, 4):
        need(f'hook({point});witness_closure({point});' in body, 'Immediate post-hook witness/frame/lifecycle closure')
    stop = body[body.index('[[noreturn]]void Binding::stop'):]
    need('context.source_identity();checkpoint(context.runtime,"filename-commandline-before");hook(5);guard();context.source_identity();witness_closure(5);' in stop,
         'Literal provider identity is rechecked before stop capture and after final observer')
    need('context.state.gpr.rsp.dword!=admitted_frame_+16' in stop and
         'std::memcmp(return_state_.data(),&context.state,sizeof(State))' in stop and
         'std::equal(return_fx_.begin(),return_fx_.end(),context.runtime.fx().begin())' in stop,
         'Exact carried post-RET State3504/FX512 closes before unresolved source read')
    invoke = body[body.index('void Binding::invoke'):body.index('[[noreturn]]void Binding::stop')]
    ordered = ['witness=native_filename(', 'actual_witness_=witness;', 'hook(2);witness_closure(2);closure(s,target);',
               'memory().write({buffer},actual_witness_.after)', 'stored=true;', 'hook(3);witness_closure(3);',
               'context.state.gpr.rax.dword=actual_witness_.result;', 'context.state.gpr.rsp.dword=admitted_frame_+16;',
               'context.state.gpr.rip.dword=mg::import_return;', 'std::memcpy(return_state_.data()',
               'hook(4);witness_closure(4);active=false;']
    positions = [invoke.index(term) for term in ordered]
    need(positions == sorted(positions) and len(set(positions)) == len(positions),
         'Actual API, immutable witness, checked full-store, private RET publication ordering')
    need('w.last_error=GetLastError(); // Capture immediately;' in header,
         'Immediate native API LastError capture before metadata')
    diff = ''.join(difflib.unified_diff(old_body.splitlines(True), body.splitlines(True),
                                      fromfile='preserved-prep6', tofile='final-prep8'))
    (out / 'repair-source-diff.txt').write_text(diff)
    association = json.loads((base / association_name / 'report.json').read_text())
    need(association['passed'] and association['build_sha256'] == BUILD_SHA, 'Fresh actual artifact association')
    report = dict(passed=True,
        scope='Independent final additive filename source/API/ABI/build/COFF association and immutable frame/lifecycle source closure review',
        build_sha256=BUILD_SHA, preparation_pins_sha256=PREP_PINS_SHA,
        source_association_receipt=str(base / association_name / 'report.json'),
        source_association_sha256=sha(base / association_name / 'report.json'),
        preserved_prior_audit=str(base / 'independent-contract-r1/report.json'),
        predecessor_semantic_gap='Prep6 used mutable public Binding.frame for RET; superseded by private admitted frame, exact hook lifecycle, and final source identity checks',
        mutable_frame_denied_against_private_admission=True,
        private_frame_used_for_guest_RET_ESP_and_event=True,
        observer_points_1_through_5_exact_lifecycle=True,
        original_provider_identity_before_stop_and_after_hook5=True,
        stale_binding_owner_validated_before_metadata_effects=True,
        immutable_actual_API_witness_and_post_RET_State_FX=True,
        actual_service_and_checked_store_before_RET_publication=True,
        no_new_maps_or_State_FX_seed=True,
        unchanged_guest_COFF_objects=12, unchanged_FDIV_libraries=2, unchanged_ancestor_components=11,
        original_executed=False, native_worker_executed=False, game_launched=False,
        source_contract=association['source_contract'],
        limitations=association['limitations'] + [
            'These deterministic source checks support the read-only review; independent rich compiled fixtures and root BEFORE-only comparison remain separate acceptance gates.',
            'The preserved predecessor audit is source/artifact association evidence for a superseded candidate, and is not a semantic acceptance of the repaired candidate.'])
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    inherited = json.loads((base / association_name / 'pins.json').read_text())['files']
    pins = dict(inherited)
    for p in (OLD, Path(__file__), base / association_name / 'report.json', base / association_name / 'pins.json',
              base / 'independent-contract-r1/report.json', base / 'independent-contract-r1/pins.json',
              base / 'preparation-r6/filename_binding.inc', out / 'repair-source-diff.txt', out / 'report.json'):
        pins[str(p)] = sha(p)
    canonical = {}
    for p, expected in pins.items():
        actual = sha(p)
        key = ntpath.normcase(ntpath.normpath(p))
        need(actual == expected and (key not in canonical or canonical[key] == actual),
             'Final physical source/artifact binding conflict or change: ' + p)
        canonical[key] = actual
    (out / 'pins.json').write_text(json.dumps(dict(files=pins), indent=2) + '\n')
    print(json.dumps(dict(passed=True, report_sha256=sha(out / 'report.json'),
                         pins_sha256=sha(out / 'pins.json'), physical_associations=len(canonical))))


if __name__ == '__main__': main()
