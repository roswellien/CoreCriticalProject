"""Independent whole trace-BEFORE coupling and current numeric link review."""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, subprocess, sys, traceback
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
A = R / 'reports/m4-hypot-native'
PINS = {}
ISHA = 'd91a51b3884ef8940fbf18eda2e9301b62077720eb3d9f00b467bd54fd1a9af4'
PSHA = 'd237d05453b2ba32a6b70678f057340a32b78ad2e839c7c3bff4815bf5e69993'
BSHA = 'f37bb8a2cb60454aa012ff07f37d5e2271747bc51ac99bd7f420689419857385'

def need(v, text):
    if not v: raise ValueError(text)

def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def pin(p, h=None):
    p = Path(p).resolve()
    need(p.suffix.lower() not in ('.mwb', '.zip'), 'No archive consumer')
    actual = sha(p)
    need(h is None or h == actual, 'Exact physical input ' + str(p))
    need(str(p) not in PINS or PINS[str(p)] == actual, 'Stable input')
    PINS[str(p)] = actual
    return p

def load(p, h=None): return json.loads(pin(p, h).read_text(encoding='utf-8-sig'))

def module(path, name):
    spec = importlib.util.spec_from_file_location(name, pin(path))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

def pack(p):
    blob = pin(p).read_bytes()
    need(blob[:8] == b'MW4J124P', 'Exact pack magic')
    n = struct.unpack_from('<I', blob, 8)[0]
    need(n == 190 and len(blob) == 12 + n * 4104, '190 complete pages')
    rows = {}
    for i in range(n):
        at = 12 + i * 4104
        page, right = struct.unpack_from('<2I', blob, at)
        need(page % 4096 == 0 and page not in rows and right in (0, 1, 2), 'Unique page and typed permission')
        rows[page] = (right, blob[at+8:at+4104])
    return blob, rows

def object_relation(old, new):
    before = pin(old).read_bytes(); after = pin(new).read_bytes()
    need(len(before) == len(after) and struct.unpack_from('<H', before)[0] == 0x8664, 'Whole same-size AMD64 COFF')
    changes = [i for i in range(len(before)) if before[i] != after[i]]
    # Retain exact raw hashes. Only the timestamp and two named O0 local
    # symbols can vary; every section byte, relocation, and other header byte
    # is conserved. The local symbols refer to identical symbol indices.
    allowed = set(range(4, 8)); names = []
    if old.name == 'control_runtime.cpp.obj':
        symoff, count = struct.unpack_from('<2I', before, 8)
        need(struct.unpack_from('<2I', after, 8) == (symoff, count), 'Exact symbol table geometry')
        table = symoff + count * 18
        need(struct.unpack_from('<I', before, table)[0] == len(before)-table, 'Complete COFF string table')
        patterns = [rb'\?admit@\?A0x([0-9A-F]{8})@@YAXPEAUState@@PEAX@Z\x00',
                    rb'\?normalized@\?A0x([0-9A-F]{8})@@YAGG@Z\x00']
        old_tags, new_tags = set(), set()
        for pattern in patterns:
            x = list(re.finditer(pattern, before[table:])); y = list(re.finditer(pattern, after[table:]))
            need(len(x) == len(y) and len(x) in (0, 1), 'Only exact two local control symbol names')
            if x:
                need(x[0].span() == y[0].span(), 'Same local symbol positions')
                lo, hi = x[0].span(1)
                allowed.update(range(table+lo, table+hi))
                old_tags.add(x[0][1]); new_tags.add(y[0][1])
                names.append(dict(before=x[0][0].decode('ascii').rstrip('\x00'), after=y[0][0].decode('ascii').rstrip('\x00'), offsets=list(range(table+lo, table+hi))))
        need(len(old_tags) <= 1 and len(new_tags) <= 1, 'One compiler-generated namespace per object')
    need(set(changes) <= allowed, 'No undeclared compiled object difference ' + str(new))
    return dict(before=str(old), after=str(new), before_sha256=sha(old), after_sha256=sha(new), differing_offsets=changes,
                timestamp_offsets=[i for i in changes if 4 <= i < 8], local_symbol_name_relations=names,
                all_code_data_relocations_and_other_header_bytes_identical=True)

def main(name):
    out = R / 'reports/m4-tree-review' / name
    need(re.fullmatch(r'hypot-coupled-prelaunch-r[1-9][0-9]*', name) and not out.exists(), 'Fresh independent output')
    out.mkdir(); passed = False; observations = []; objects = []; linked = []; deps = []
    try:
        prior = load(R/'reports/m4-tree-review/hypot-fixture-prelaunch-r1/report.json',
            '5895b7658e6f406a3bef32d6d6eef231c016a4cce922865223ab4e611a961817')
        need(prior['passed'] and not prior['worker_launched'] and prior['initializer_credit'] == 0, 'Independent finite parent review')
        inputs = load(A/'inputs-r5/report.json', ISHA)
        prep = load(A/'fixture-preparation-r4/report.json', PSHA)
        build = load(A/'fixture-build-r4/build.json', BSHA)
        old_inputs = load(inputs['parent_inputs'], inputs['parent_inputs_sha256'])
        old_prep = load(A/'fixture-preparation-r3/report.json', prior['preparation_sha256'])
        old_build = load(A/'fixture-build-r3/build.json', prior['build_sha256'])
        trace = load(inputs['source_trace'], inputs['source_trace_sha256'])
        trace_prep_path = R/'reports/m4-hypot-original/trace-preparation-r8/report.json'
        trace_prep = load(trace_prep_path, trace['files'][str(trace_prep_path.resolve())])
        for receipt in (prior, inputs, prep, build, old_inputs, old_prep, old_build, trace, trace_prep):
            need(receipt['passed'], 'Passed input receipt')
            for key in ('files', 'artifacts'):
                for path, digest in receipt.get(key, {}).items():
                    if Path(path).suffix.lower() not in ('.mwb', '.zip'): pin(path, digest)
        need(prep['inputs_sha256'] == ISHA and build['preparation_sha256'] == PSHA and prep['inputs'] == str((A/'inputs-r5/report.json').resolve()), 'Current exact coupling chain')
        need(not inputs['source_AFTER_seed'] and not inputs['numerical_results_seeded'] and not inputs['archive_reader_opened'], 'Only actual BEFORE page storage')
        need(all(not r['native_executed'] and r['initializer_credit'] == 0 for r in (inputs, prep, build)), 'Preparation only')
        need(inputs['permission_encoding'] == old_inputs['permission_encoding'] == {'0':'read execute','1':'read','2':'read write'}, 'Explicit unchanged unified rights')
        coupling = load(A/'inputs-r5/trace-BEFORE-coupling.json')
        states = pin(A/'inputs-r5/input-state.bin').read_bytes()
        need(states == pin(A/'inputs-r4/input-state.bin').read_bytes() and len(states) == 3480, 'Whole CPU/FX/ENV storage unchanged')
        for filename in ('input-mapping.json', 'page-permissions.json'):
            need(pin(A/'inputs-r5'/filename).read_bytes() == pin(A/'inputs-r4'/filename).read_bytes(), 'Whole retained mapping and rights metadata')
        stack_index = trace_prep['observed_pages'].index(0x20001000)
        offset = 2276 + stack_index * 4096
        need(trace_prep['record_bytes'] == 356992 and len(trace_prep['observed_pages']) == 43 and trace['reader_closed'], 'Exact closed genuine source record ABI')
        need(len(inputs['cases']) == len(old_inputs['cases']) == len(coupling) == 6, 'Six genuine input cases')
        for seq, (case, old, witness) in enumerate(zip(inputs['cases'], old_inputs['cases'], coupling)):
            need(case['sequence'] == old['sequence'] == witness['sequence'] == seq, 'Exact case occurrence')
            source_path = Path(inputs['source_trace']).parent/'raw-observations'/f'case-{seq}-record.bin'
            raw = pin(source_path, trace['files'][str(source_path.resolve())]).read_bytes()
            need(len(raw) == 356992 and struct.unpack_from('<9I', raw)[0] == seq, 'Actual trace input occurrence')
            before, previous = pack(pin(old['pack'], old['pack_sha256']))
            after, current = pack(pin(case['pack'], case['pack_sha256']))
            need(list(previous) == list(current), 'Entire ordered page inventory unchanged')
            differences = []
            for page, (right, payload) in current.items():
                old_right, old_payload = previous[page]
                need(right == old_right, 'Every permission DWORD unchanged')
                if page == 0x20001000:
                    need(payload == raw[offset:offset+4096], 'Whole genuine trace BEFORE stack page')
                    differences = [dict(address=page+i, ordinary=old_payload[i], trace=payload[i]) for i in range(4096) if old_payload[i] != payload[i]]
                    need([r['address'] for r in differences] == [0x200017ae,0x200017d0,0x200017d1], 'Complete measured three-byte input variation')
                    need(struct.unpack_from('<I',payload,0x800)[0] == 0x410a80, 'Unprojected genuine source return in input')
                else: need(payload == old_payload, '189 complete BEFORE pages unchanged')
            need(sum(a != b for a,b in zip(before,after)) == 3, 'No other complete pack difference')
            need(states[seq*580:(seq+1)*580] == raw[36:76]+raw[116:628]+raw[2164:2192], 'All actual trace whole BEFORE register/FX/ENV bytes')
            need(witness['changed_bytes'] == differences and witness['raw_BEFORE_offset'] == offset and witness['raw_source_sha256'] == sha(source_path), 'Exact independently measured coupling receipt')
            observations.append(dict(sequence=seq, whole_stack_BEFORE_sha256=hashlib.sha256(current[0x20001000][1]).hexdigest(), other_complete_pages_equal=189,
                permission_tags_equal=190, complete_CPU_FX_ENV_bytes_equal=580, input_byte_differences=differences))
        before_folder=A/'fixture-preparation-r3'; current_folder=A/'fixture-preparation-r4'
        prepared_files = sorted(q.name for q in before_folder.iterdir() if q.is_file() and q.name != 'report.json')
        need(prepared_files == sorted(q.name for q in current_folder.iterdir() if q.is_file() and q.name!='report.json'), 'Complete generated source/header inventory')
        for name_ in prepared_files: need(pin(before_folder/name_).read_bytes() == pin(current_folder/name_).read_bytes(), 'Every generated current source/header byte unchanged')
        need(prep['objects'] == old_prep['objects'] and prep['source_domain_sha256'] == old_prep['source_domain_sha256'], 'Exact42 retained literal object inputs and domain')
        coupling_code=pin(R/'tools/m4-hypot-native/couple_trace_before.py').read_text()
        need('raw[before_offset:before_offset + 4096]' in coupling_code and 'raw[36:76] + raw[116:628] + raw[2164:2192]' in coupling_code and 'pack[at:at + 4096] = actual_before' in coupling_code, 'Whole BEFORE operation in actual coupling tool')
        generator=pin(R/'tools/m4-hypot-native/prepare_fixture_v4.py').read_text()
        need(generator.count("'inputs-r5/report.json'") == 1 and ISHA in generator and 'prepare_fixture_v3.py' in generator and 'couple_trace_before.py' in generator, 'Actual additive generator changes input identity only')
        C=module(R/'tools/m4-tree-review/amd64_coff.py','coupled_coff')
        M=module(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','coupled_image')
        bodies=load(A/'reached-domain-r1/literal-bodies.json')
        ninja=pin('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
        need(set(build['workers']) == {'O0','O2'} and all(x['exit_code']==0 for x in build['commands']), 'Both actual successful compiler/link executions')
        for level, worker in build['workers'].items():
            bf=Path(worker['path']).parent; previous_bf=Path(old_build['workers'][level]['path']).parent
            image=M.AMD64Image(pin(worker['path'],worker['sha256']).read_bytes())
            need(worker['literal_objects']==old_build['workers'][level]['literal_objects'], 'Identical current actual literal input paths')
            need(pin(bf/'fixture_spec.hpp').read_bytes()==pin(current_folder/f'fixture_spec_{level}.hpp').read_bytes(), 'Actual consumed constant header')
            graph=pin(bf/'build.ninja').read_text()
            line=next(x for x in graph.splitlines() if x.startswith('build hypot-native.exe: CXX_EXECUTABLE_LINKER'))
            inputs_link={str((bf/Path(x.replace('$:',':'))).resolve()) for x in line.split(' ',3)[3].split(' |')[0].split(' ') if x.endswith('.obj')}
            need(len(inputs_link)==26 and set(worker['literal_objects']) < inputs_link, 'Actual21 literal plus five compiled object graph')
            for body in bodies.values():
                q=body['objects'][level]; obj=pin(q['path'],q['sha256']); symbols,sections=C.parse(obj.read_bytes())
                raw,relocs=C.function(symbols,sections,body['symbol']); candidates=C.linked_candidates(image,raw,relocs)
                need(len(candidates)==1, 'Unique whole current linked literal')
                linked.append(dict(level=level,entry=body['entry'],address=candidates[0][0],bytes=len(raw),relocation_DWORDs=len(relocs)))
            for path in inputs_link-set(worker['literal_objects']):
                new=Path(path); old=previous_bf/new.relative_to(bf)
                objects.append(dict(level=level,**object_relation(old,new)))
            control=pin(bf/'CMakeFiles/hypot-native.dir/control_runtime.cpp.obj'); symbols,sections=C.parse(control.read_bytes())
            for helper in ('mw34_hypot_store_cw','mw34_hypot_load_cw','mw34_hypot_wait'):
                raw,relocs=C.function(symbols,sections,helper)
                need(len(C.linked_candidates(image,raw,relocs))==1,'Whole actual current control helper')
            db=pin(bf/'.ninja_deps'); digest=sha(db)
            result=subprocess.run([str(ninja),'-C',str(bf),'-t','deps'],capture_output=True,creationflags=0x08000000)
            need(result.returncode==0 and sha(db)==digest,'Read-only actual compiler dependency database')
            consumed=[Path(x.strip()) for x in result.stdout.decode().splitlines() if x.startswith('    ') and Path(x.strip()).is_file()]
            need(any(x.resolve()==(current_folder/'fixture.cpp').resolve() for x in consumed) and any(x.resolve()==(current_folder/'control_runtime.cpp').resolve() for x in consumed), 'Current actual source dependency records')
            for path in consumed: pin(path)
            deps.append(dict(level=level, actual_compiler_input_paths=len(consumed), database_sha256=digest, literal_objects=21, compiled_objects=5))
        controller=pin(R/'tools/m4-hypot-native/run_fixture.py').read_text()
        need("review['files'][str(Path(build_path).resolve())]==build_sha" in controller and 'timeout=30' in controller, 'Fresh exact independent current-build admission edge')
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc()); raise
    finally:
        pin(__file__);pin(sys.executable)
        for filename,data in [('whole-coupled-BEFORE-relations.json',observations),('compiled-object-relations.json',objects),('linked-literal-relations.json',linked)]:
            path=out/filename;path.write_text(json.dumps(data,indent=2)+'\n');pin(path)
        report=dict(passed=passed,inputs_sha256=ISHA,preparation_sha256=PSHA,build_sha256=BSHA,
            parent_independent_review_sha256='5895b7658e6f406a3bef32d6d6eef231c016a4cce922865223ab4e611a961817',
            counts=dict(genuine_cases=len(observations),whole_coupled_stack_pages=len(observations),complete_other_pages_unchanged=189*len(observations),
                complete_permission_tags_unchanged=190*len(observations),complete_CPU_FX_ENV_BEFORE_bytes=580*len(observations),
                measured_initial_stack_byte_changes=3*len(observations),actual_linked_literal_functions=len(linked),whole_compiled_object_relations=len(objects)),
            levels=deps,archive_reader_opened=False,worker_launched=False,original_AFTER_seed=False,numerical_oracle=False,initializer_credit=0,
            scope='Independent additive first-writer admission only. Six complete genuine trace BEFORE stack pages are coupled, every other input page/right/register byte is conserved; actual current code/header/compiler/link closure is bound. Numeric execution/source equivalence, caller/fault/cleanup and connected initializer acceptance remain separate measured obligations.',files=PINS)
        path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(passed=passed,path=str(path),sha256=sha(path),files=len(PINS),counts=report['counts'])))

if __name__=='__main__':main(sys.argv[1])
