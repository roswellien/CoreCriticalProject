"""Read-only final original-BEFORE root oracle/source association review.

Does not run the observer, a worker, original/provider code, or the game.
"""
import hashlib
import json
import ntpath
import sys
from pathlib import Path

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-commandline-carry'
PROOF_SHA='7aa5faba4b659d03dfa2b86c289876e64ae4af6c4ff417bd2711accc417410d0'
EXEC_SHA='930355cc98ecb11eb7f9d57621b69fd9fa9c0ac1df8a14deee363738efa32bf9'
STAGE_SHA='658bce741486e612da967797a12c6369cc3a67de0023a5fb3837d5869709b984'
OBSERVER_SHA='76a1bbef4cc8f4e343495a4bf0209d051c547af5781c8d045bb6084c4e07e225'


def need(ok,why):
    if not ok:raise ValueError(why)


def unique(pairs):
    values={}
    for key,value in pairs:
        need(key not in values,'Duplicate JSON key')
        values[key]=value
    return values


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=unique)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    out=BASE/'independent-root-model-audit-r1'
    need(not out.exists(),'Fresh owned final root model audit')
    pins={}
    def bind(path,expected=None):
        path=Path(path).absolute();actual=sha(path);key=ntpath.normcase(ntpath.normpath(str(path)))
        need((expected is None or expected==actual) and (key not in pins or pins[key]==actual),'Physical association changed/conflicted '+str(path))
        pins[key]=actual
        return path
    proof_path=bind(BASE/'root-observer-r2/report.json',PROOF_SHA)
    exec_path=bind(BASE/'root-execution-r1/report.json',EXEC_SHA)
    proof,execution=read(proof_path),read(exec_path)
    need(proof['passed'] and execution['passed'],'Final matching root proof and native receipt')
    for receipt in (proof,execution):
        for path,digest in receipt['files'].items():bind(path,digest)
    observer_path=bind(ROOT/'tools/m4-crt-commandline-carry-root/observe.py',OBSERVER_SHA)
    model_path=bind(ROOT/'tools/m4-crt-commandline-carry-root/model.py','3614f7b417afd56f40a4f79122c15cd3e1d19508886a5b6172e85b0119750696')
    consumer_path=bind(ROOT/'tools/m4-crt-commandline-carry-root/consumer.py','01c0c248f00785acb73b5c1ce96f2ddda1b675db6c60a0602bf04c175b1b48a8')
    bind(ROOT/'tools/m4-crt-commandline-carry-root/run.py','9e0a4f416580f3bbb747361c0142f7363c70f6fe68395755221a05423e284052')
    observer,model,consumer=observer_path.read_text(),model_path.read_text(),consumer_path.read_text()
    stage_path=bind(BASE/'root-observer-stage-r2/stage.json',STAGE_SHA)
    stage=read(stage_path)
    need(stage['passed'] and stage['format']=='mw34.stage.v1' and stage['status']=='success' and
         stage['inputs_stable'] and not stage['process_file_open_attestation'] and not stage['command_shell_used'],
         'Actual successful stable observer stage; no process-open attestation claimed')
    invoked=Path(stage['cwd'])/stage['argv'][1]
    need(ntpath.normcase(ntpath.normpath(str(invoked)))==ntpath.normcase(str(observer_path)) and
         stage['required_outputs']==[str(proof_path)] and stage['elapsed_seconds']>=0,'Exact observer request/output/timing association')
    for group in ('input_sha256','final_input_sha256','artifact_sha256'):
        for path,digest in stage[group].items():bind(path,digest)
    bind(stage_path.with_name('stdout.bin'),stage['stdout_sha256']);bind(stage_path.with_name('stderr.bin'),stage['stderr_sha256'])
    expected=dict(checks=118807,selected_semantic_byte_corruption_denials=2000,independently_modeled_ordinary_sequences=48,
                  standard_causal_sequences_independently_modeled_by_root=0,State_bytes=3504,FX_bytes=512,borrowed_pages=16,
                  new_owned_buffer=0x33000000,main_initializer_count=27)
    for name,value in expected.items():need(proof[name]==value,'Exact final successful proof count '+name)
    for name in ('parser_body_executed','DllMain_or_original_scheduling_recovered','State_reseed','argument_initialization_complete',
                 'whole_M4_complete','game_launched','original_executed','author_expected_model_imported'):
        need(proof[name] is False,'Correct unclaimed original/API/parser/M4 scope '+name)
    need(proof['source_writer_and_consumer_executed'] and proof['physical_closure']['passed'] and
         proof['physical_closure']['unique_physical_dependencies']==728 and
         not proof['physical_closure']['metadata_only_cache_used'],'Whole physical source/input closure')
    need(execution['build_sha256']=='10969868ff59f5bd1c37b60065b2329d0649785ab3a5d48763696fe846759ce9' and
         execution['native_executed_by_root'] and execution['native_stages_completed']==2 and
         execution['positive_sequences']==48 and execution['causal_sequences']==24 and
         execution['original_executed'] is False and execution['game_launched'] is False,'Fresh actual immutable native candidate/counts')
    rows=proof['rows'];need(len(rows)==48,'Exactly48 root-modeled ordinary native rows')
    for level in ('O0','O2'):
        own=[r for r in rows if r['level']==level]
        need([r['index'] for r in own]==list(range(24)),'Exact per-level original corpus identity/order')
        for row in own:
            need(row['control']==0 and row['producer_source_bytes']==11 and row['consumer_source_instructions']==14 and
                 row['consumer_memory_accesses']==9 and row['borrowed_pages']==16 and row['owned_bytes']>1 and
                 row['parser_CALL_executed'] and not row['parser_body_executed'] and row['State3504_FX512'],
                 'Every actual nonempty producer/consumer/source/wholeState row')
    for fragment in (
        "originals = M.R.originals(original_path.read_bytes())",
        "payloads = [M.R.project(v) for v in originals[:24]]",
        "host_bytes == subprocess.list2cmdline(argv).encode('mbcs') + b'\\0'",
        "before == bytes(memory[0x7803b000][0x3f0:0x4f4])",
        "after[length + 1:] == before[length + 1:]",
        "consumed = consumer_predict(holder, program, host_bytes)",
        'F.full_stage(row, tag, values, attack and tag.startswith',
        "(row / 'commandline-accesses.bin').read_bytes() == producer + bytes(320 - len(producer))",
        "(row / 'commandline-consumer-accesses.bin').read_bytes() == accesses + bytes(320 - len(accesses))",
        "(row / 'filename-job.bin').read_bytes()",
        "(row / 'filename-reason.txt').read_text().strip()",
        "(row / 'commandline-reason.txt').read_text().strip()",
        'closure = verify_manifest(F.PHYSICAL)'):
        need(fragment in observer,'Reviewed original BEFORE/API/whole-stage/ledger metadata seam missing '+fragment)
    for fragment in (
        "class CarryEntry(M.Entry):", "if tag == 'mainargs-before':",
        "struct.pack_into('<I', self.state, 2472, WRITER)",
        "self.raw_store(frame - 4, RETURN)","self.r['esp'] = frame - 4",
        "self.cmd_snapshot('commandline-api-after')", 'self.cmd_owned = True',
        "self.cmd_snapshot('commandline-buffer-after')", "self.r['eax'], self.r['esp'] = BUFFER, frame",
        "self.raw_store(GLOBAL, BUFFER)","self.cmd_snapshot('commandline-producer-after')",
        "struct.pack_into('<I', self.state, 2472, saved_pc)","struct.pack_into('<I', runtime, 0, BUFFER)",
        "dict(OLD.expected.__globals__, M=facade, writer_result=F.writer)"):
        need(fragment in model,'Independent actual source/explicit seam expectation missing '+fragment)
    need(model.index("self.raw_store(frame - 4, RETURN)")<model.index("self.r['esp'] = frame - 4"),
         'Producer literal checked CALL store before ESP publication')
    need(model.index("self.cmd_snapshot('commandline-api-after')")<model.index('self.cmd_owned = True')<
         model.index("self.cmd_snapshot('commandline-buffer-after')")<model.index("self.r['eax'], self.r['esp'] = BUFFER, frame"),
         'Actual API witness and owned allocation are distinct before representative EAX/ESP/PC publication')
    need(consumer.index('write32(address, value)')<consumer.index("r['esp'] = address") and
         consumer.index('write32(address, END)')<consumer.index("r['esp'], pc = address, PARSER"),
         'Actual scalar source PUSH/CALL store-before-ESP and parserPC publication')
    need("flags = (flags & ~0x8d5)" in consumer and "(((byte.bit_count() & 1) == 0) << 2)" in consumer and
         consumer.index('byte = host_bytes[0]')<consumer.index('flags = (flags & ~0x8d5)'),
         'Actual first-byte CMP read before CF/PF/AF/ZF/SF/OF updates')
    need('memory = copy.deepcopy(entry.mem)' in consumer and 'cpu = bytes(entry.fx), bytes(entry.runtime_cpu)' in consumer,
         'Consumer starts from independently derived whole memory/State/FX with stale generic RuntimeCPU separate')
    need('tools/m4-crt-commandline-carry/observe.py' not in observer+model+consumer and
         'changed != value' not in observer,'No candidate expected-model import or tautological corruption count')
    # Count source-qualified attack locations independently, without executing
    # either oracle or candidate. The frozen validator is used by both normal
    # equality checks and every altered stage dictionary.
    frozen=bind(ROOT/'tools/m4-crt-filename-root/observe.py','405797301b25103cdc27dd0635e93e169a4ef86f415afb7c8a431da23703733e')
    text=frozen.read_text()
    need('validate_stage_record(actual, expected, tag)' in text and
         'validate_stage_record(corrupted, expected, tag)' in text and 'except AssertionError:' in text,
         'Actual unchanged shared positive/negative stage validator')
    sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
    from capture_bundle import CaptureBundle
    from stages import verify_stage
    positions=set()
    for level,identity in execution['levels'].items():
        for kind in ('native_stage','pack_stage'):
            directory=Path(identity[kind]);k=ntpath.normcase(ntpath.normpath(str(directory/'stage.json')))
            verify_stage(directory,pins[k])
        with CaptureBundle(identity['bundle'],identity['bundle_sha256']) as reader:
            for name in reader.names():
                parts=name.split('/')
                if len(parts)==3 and parts[0]=='row-0' and parts[1].startswith(('commandline-','filename-')):
                    value=reader.read_bytes(name)
                    for offset in sorted({0,len(value)-1}):
                        if offset>=0:positions.add((level,parts[1],parts[2],offset))
    need(len(positions)==2000,'Exact2000 distinct source-qualified stage byte corruption locations')
    for path,digest in [
        (BASE/'source-contract-r2/report.json','be9fb846df9d78448298310274af19fd43463fcbadf1787df680626adb362cf0'),
        (BASE/'source-contract-r2/pins.json','126647e98358f580104709ac33128db1ece2b76424420fbb856837ecf4841c9b'),
        (BASE/'root-observer-r1/report.json','ea75b260d558e909061f8569bcb1213075a37fd11c31b697ce0806a836c42ba4'),
        (BASE/'root-observer-stage-r1/stage.json','1452a72adde7b728e5c4ee9f1e72e52c93e8d65f2b55a8621d44db31c7664416'),
        (BASE/'root-observer-r1-source-snapshot/observe.py','502910f510c0934d058fe19e9469ec0220dea8084fd0247143d68a5538256f25')]:bind(path,digest)
    bind(Path(__file__));bind(ROOT/'tools/m4-crt-mainargs-root/model.py');bind(ROOT/'tools/m4-crt-mainargs-root/observe.py')
    for path,digest in list(pins.items()):bind(path,digest)
    out.mkdir()
    report=dict(passed=True,scope='Independent read-only audit of final BEFORE-derived ordinary carry root oracle and actual execution/source closure; no model/native rerun',
                root_proof_sha256=PROOF_SHA,root_execution_sha256=EXEC_SHA,root_observer_stage_sha256=STAGE_SHA,
                observer_sha256=OBSERVER_SHA,**expected,whole_source_identity_bytes=1151,
                unique_selected_stage_corruption_locations=len(positions),
                original_BEFORE_only_guest_expectations=True,stopped_native_AFTER_used_as_machine_seed=False,
                actual_API_witnesses_only_supply_declared_service_inputs_or_results=True,
                actual_root_launch_argv_commandline_bytes_and_full64bit_metadata_checked=True,
                actual_native_filename_scratch_and_untouched_tail_checked=True,
                source_writer_IAT_CALL_MOV_and_consumer_PUSHCALL_frame_ledgers_checked=True,
                normal_filename22word_lifecycle_and_both_first_reason_records_checked=True,
                entire3504State_512FX_16pages_and_owned_bytes_every_expected_stage_checked=True,
                actual_PUSHCALL_checked_store_beforeESP_and_CMP_read_beforeflags=True,
                explicit_late_PC_overlay_and_savedPC_RuntimeEAX_only_carry=True,
                stale_generic_RuntimeCPU_predicted_separately_from_consumer_State=True,
                independent_native_O0_and_O2=True,code_inputs_and_artifact_physical_hashes_checked=True,
                original_executed_by_auditor=False,native_executed_by_auditor=False,root_observer_rerun_by_auditor=False,
                game_launched=False,parser_body_implemented=False,argument_environment_initialized=False,whole_M4_complete=False,
                preserved_predecessor='Root observer1 was valid narrow wholeState/source proof; observer2 additionally closes filename22DWORD/reason and commandline reason metadata. Captures and candidate unchanged.',
                limitations=['Root models48ordinary source sequences;24standard injected native causal rows are not root-modeled and require the separate compiled-review gate.',
                    'Actual API inputs and explicit representative State service ABI do not establish originalx86 volatile equivalence or reconstructedDLL scheduling.',
                    'Actual native witnesses here are nonempty; source empty fallback is recovered but unexecuted.',
                    'Parser is refused after actual CALL frame publication; no argc/argv/env, fullCRT/MFC/window/menu or completeM4 credit.',
                    'Serial immutable published captures/source are assumed; stage associations are not process-file-open attestation.'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json')
    (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
    print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),physical_associations=len(pins))))


if __name__=='__main__':main()
