"""Execute the complete x64 allocation batch directly into strict archives."""
import json
from pathlib import Path
import struct
import sys
import time
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-allocation-root'
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import run_stage, verify_stage


def need(ok, why):
    if not ok:
        raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


class DirectSet:
    def __init__(self, manifest, pin):
        self.path = pin(manifest)
        self.value = read(manifest)
        value = self.value
        need(value['passed'] is True and value['format'] == 'mw34.capture.direct.v1' and
             value['transport_only'] is True and value['native_executed'] is False,
             'Exact direct transport; execution credit comes from the actual worker stage')
        self.bundles, self.entries = [], {}
        try:
            keys, physical, payload = set(), {self.path.name}, 0
            for part in value['parts']:
                name = part['bundle']
                need(Path(name).name == name and name.endswith('.mwb') and name not in physical,
                     'Distinct direct archive basename')
                physical.add(name)
                path = pin(self.path.parent / name, part['sha256'])
                with path.open('rb') as stream:
                    magic, index_bytes, index_sha = struct.unpack('<8sQ32s', stream.read(48))
                need(magic == b'MW34CAP1' and index_bytes == part['index_bytes'] and
                     index_sha.hex() == part['index_sha256'], 'Actual unchanged strict archive header')
                reader = CaptureBundle(path, part['sha256'])
                self.bundles.append(reader)
                need(len(reader.names()) == part['logical_files'] and path.stat().st_size == part['bundle_bytes'],
                     'Actual strict archive count and extent')
                part_bytes = 0
                for logical in reader.names():
                    need(logical.casefold() not in keys, 'Disjoint normalized union across archive parts')
                    keys.add(logical.casefold()); self.entries[logical] = reader
                    part_bytes += len(reader.read_bytes(logical))
                need(part_bytes == part['payload_bytes'], 'Actual strict part payload')
                payload += part_bytes
            need(len(self.entries) == value['logical_files'] and payload == value['payload_bytes'],
                 'Complete direct logical union')
            need({p.name for p in self.path.parent.iterdir()} == physical,
                 'No per-record physical files, later packing, or loose capture additions')
        except Exception:
            self.close()
            raise

    def data(self, name):
        need(name in self.entries, 'Required functional observation: ' + name)
        return self.entries[name].read_bytes(name)

    def words(self, name, count, kind='I'):
        raw = self.data(name)
        need(len(raw) == count * struct.calcsize(kind), 'Exact functional observation extent: ' + name)
        return struct.unpack('<' + str(count) + kind, raw)

    def close(self):
        for bundle in self.bundles:
            bundle.close()


def main(build_path, build_sha, directory):
    started = time.perf_counter()
    out = workspace_path(directory, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh coordinator execution report')
    out.mkdir(parents=True)
    files, levels, rows = {}, {}, []
    passed, completed, launched = False, 0, 0
    closure = None

    def pin(path, digest=None):
        path = Path(path).absolute()
        actual = sha_file(path)
        need(digest is None or actual == digest, 'Fixed current input: ' + str(path))
        key = normalized(str(path))
        need(key not in files or files[key] == actual, 'Consistent current input: ' + key)
        files[key] = actual
        return path

    try:
        build = read(pin(build_path, build_sha))
        need(build['passed'] is True, 'Successful frozen allocation build')
        for category in ('sources', 'tools', 'libraries', 'entry_objects', 'compiler_read_headers', 'artifacts'):
            for path, digest in build.get(category, {}).items():
                pin(path, digest)
        pin(build['preparation_path'], build['preparation_sha256'])
        pin(build['source_scope_note'], build['source_scope_note_sha256'])
        pin(build['direct_writer_build_path'], build['direct_writer_build_sha256'])
        for path, digest in build['direct_writer_objects'].items():
            pin(path, digest)
        game = pin(ROOT/'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
        provider = pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL', '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
        pack = pin(ROOT/'reports/m4-crt-fdiv/native-derived-r1/pack.bin', 'fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80')
        before = pin(ROOT/'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin', '4294b8d926966c04d305b6e22a9166f08a328f4cc1c62984b72677fe83dd638a')
        pin(__file__); pin(sys.executable)
        for name in ('capture_bundle.py', 'paths.py', 'stages.py', 'manifests.py'):
            pin(ROOT/'tools/m4-pipeline'/name)
        for level in ('O0', 'O2'):
            worker = pin(build['workers'][level])
            obj = pin(ROOT/f'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-{level}.obj')
            capture_dir, stage = out/('native-'+level), out/('run-'+level)
            argv = list(map(str, (worker, game, obj, provider, pack, before, capture_dir)))
            launched += 1
            result = run_stage(argv, stage, timeout_seconds=180,
                               required_outputs=[capture_dir/'transport.json'], inputs=list(files))
            stage_sha = sha_file(pin(stage/'stage.json'))
            verify_stage(stage, stage_sha)
            need(result['passed'] is True, 'Actual native allocation worker completed: ' + level)
            completed += 1
            verify_started = time.perf_counter()
            captures = DirectSet(capture_dir/'transport.json', pin)
            try:
                need(captures.data('COMPLETE') == b'COMPLETE', 'Logical native completion record')
                for index in range(18):
                    prefix = f'row-{index}/'
                    summary = json.loads(captures.data(prefix+'result.json'), object_pairs_hook=unique_object)
                    control = 0 if index < 6 else index+163
                    request = (0,1,24,31,32,4096)[index] if index < 6 else 24
                    need(summary['passed'] is True and summary['scenario'] == index and summary['control'] == control,
                         'Explicit functional row identity')
                    need(summary['poisoned_retry'] is True and summary['State_reseed_after_writer'] is False and
                         summary['full_CRT'] is False and summary['whole_M4_complete'] is False,
                         'Preserved original BEFORE seed and bounded terminal retry')
                    job = captures.words(prefix+'allocation-job.bin', 32)
                    progress = captures.words(prefix+'allocation-progress.bin', 16)
                    registry = captures.words(prefix+'allocation-registry.bin', 24, 'Q')
                    witness = captures.words(prefix+'allocation-witness.bin', 16, 'Q')
                    heap = captures.words(prefix+'allocation-heap-registry.bin', 18, 'Q')
                    created = captures.words(prefix+'allocation-heap-witness.bin', 16, 'Q')
                    need(job[0] == control and job[1] == request and progress[0] == registry[0] == 1 and
                         progress[7] == registry[5] == request, 'Private progress agrees with declared request')
                    need(progress[13] == progress[14] == registry[9] == registry[12] == 0,
                         'No live private pointer or backing after normal/partial fault cleanup')
                    need(job[22:27] == (heap[8],heap[9],registry[8],registry[10],registry[11]),
                         'Captured counters agree across ownership/job records')
                    need(heap[8] == heap[9] == heap[10] == 1 and heap[7] == 0 and heap[15] == 1 and
                         heap[4] == heap[16] == created[6] == registry[20] and heap[4] != 0,
                         'Same full-width actual heap created and destroyed once')
                    need(registry[4] == registry[21] == witness[3] and
                         (not registry[8] or witness[9] == heap[4]), 'Full native pointer/heap association')
                    need(registry[10] == registry[11] and registry[17] == registry[18] and
                         registry[10]+registry[17] == bool(registry[4]), 'Normal and fallback actual free ownership')
                    need(job[30] == job[31], 'Actual caller LastError restored')
                    if index < 6:
                        extent = ((request or 1)+15)&~15
                        need(registry[3] == job[27] == 0x31000000,
                             'Declared new allocation address leaves reserved runtime heap unchanged')
                        need(progress[1:7] == (1,1,1,1,1,1) and job[15:21] == (1,1,1,1,1,1),
                             'Complete genuine caller/malloc/client/free/NULLfree batch')
                        need(registry[8] == registry[10] == registry[11] == 1 and registry[17] == 0 and
                             witness[7] == 1 and witness[8] != 0 and witness[10] == registry[4],
                             'One actual source HeapFree; NULLfree makes no second OS call')
                        need(progress[8] == registry[6] == witness[2] == extent and job[28] == extent,
                             'Authentic bounded source allocation rounding')
                        initial = captures.data(prefix+'allocation-initial.bin')
                        pattern = captures.data(prefix+'allocation-pattern.bin')
                        expected = bytes((n*37+request*11+0x5a)&255 for n in range(extent))
                        need(len(initial) == extent and pattern == expected, 'Actual initial bytes and complete client pattern')
                        need(job[3] == (118 if request else 120) and job[4] == 4,
                             'Exact integrated source access and separate API-return ledger counts')
                    for boundary in ('writer', 'entry'):
                        a = captures.data(prefix+boundary+'-host-before.bin')
                        b = captures.data(prefix+boundary+'-host-after.bin')
                        need(len(a) == len(b) == 544 and a[512:540] == b[512:540] and
                             a[:5] == b[:5] and a[24:28] == b[24:28], 'Complete host legacy ENV and controls')
                        for register in range(8):
                            need(a[32+16*register:42+16*register] == b[32+16*register:42+16*register],
                                 'Each physical raw80 host register')
                        for register in range(6,16):
                            need(a[160+16*register:176+16*register] == b[160+16*register:176+16*register],
                                 'Each nonvolatile host XMM register')
                    rows.append(dict(level=level,scenario=index,control=control,request=request,
                                     rounded_extent=registry[6],source_accesses=job[3],API_return_reads=job[4],
                                     source_HeapAlloc_calls=registry[8],source_HeapFree_calls=registry[10],
                                     fallback_HeapFree_calls=registry[17],batch_complete=bool(progress[6])))
                levels[level] = dict(worker=str(worker), argv=argv,
                                     transport_manifest=str(captures.path), transport_sha256=sha_file(captures.path),
                                     logical_files=len(captures.entries), payload_bytes=captures.value['payload_bytes'],
                                     archive_parts=len(captures.bundles), per_record_physical_files=0,
                                     native_stage=str(stage), stage_sha256=stage_sha,
                                     native_and_emission_seconds=result['elapsed_seconds'],
                                     emit_seconds=captures.value['emit_seconds'],
                                     finalize_parts_seconds=captures.value['finalize_parts_seconds'],
                                     strict_verification_and_row_review_seconds=time.perf_counter()-verify_started)
            finally:
                captures.close()
            for name in ('stdout.bin', 'stderr.bin'):
                pin(stage/name)
        closure = verify_manifest(files)
        passed = True
    except Exception:
        publish_bytes(out/'failure.txt', traceback.format_exc().encode())
        raise
    finally:
        report = dict(passed=passed, build_path=str(build_path), build_sha256=build_sha,
                      native_executed_by_coordinator=launched>0,native_stages_completed=completed,
                      positive_sequences=12 if passed else 0,causal_sequences=24 if passed else 0,
                      actual_HeapCreate_calls=sum(1 for row in rows),
                      actual_HeapAlloc_calls=sum(row['source_HeapAlloc_calls'] for row in rows),
                      actual_source_HeapFree_calls=sum(row['source_HeapFree_calls'] for row in rows),
                      actual_fallback_HeapFree_calls=sum(row['fallback_HeapFree_calls'] for row in rows),
                      counter_scope='Verified row observations; failed partial windows are not totalled',
                      verified_row_observations=len(rows),
                      declared_allocation_guest_address=0x31000000,
                      source_HeapFree_and_cleanup_separate=True,all_main_captures_direct=True,
                      per_record_physical_files=0,later_copy_or_pack_passes=0,
                      original_executed=False,game_launched=False,original_attach_proved=False,
                      full_CRT_complete=False,whole_M4_complete=False,
                      levels=levels,rows=rows,files=files,current_physical_closure=closure,
                      elapsed_seconds=time.perf_counter()-started)
        publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
        print(json.dumps({k:v for k,v in report.items() if k not in ('files','rows','levels')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
