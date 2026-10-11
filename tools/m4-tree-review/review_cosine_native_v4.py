"""Independent light review of the compound FCOS native candidate and proof.

No archive or native result payload is opened. This reviews actual source,
strict IR deltas, input packs, compiled math/literal bodies and final links.
"""
import collections
import importlib.util
import json
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import review_connected125_v2 as C
import amd64_coff as A


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, C.pin(path))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main(name):
    out = ROOT / 'reports/m4-tree-review' / name
    C.need(not out.exists(), 'Fresh independent compound-FCOS review')
    out.mkdir(parents=True)
    counts, linked = collections.Counter(), []
    passed = False
    try:
        C.pin(__file__); C.pin(A.__file__); C.pin(C.__file__)
        area = ROOT / 'reports/m4-cosine-native'
        lift = C.read(area / 'guest-lift-r1/report.json', '3c39f79575c1aab5176520c0a9c86ed79659db5f3454a32b94154edb4f4bdf2b')
        host = C.read(area / 'host-candidate-r1/report.json', '52fbe84a286e333d7c095be292088b922138eaabb661cf41d364bfab7c0ffb9e')
        prep = C.read(area / 'fixture-preparation-r1/report.json', '6e10d1bc883ab6fcd8597962f75e4c8660d028c637578ca39553bff034672643')
        build = C.read(area / 'fixture-build-r1/report.json', '91c873f5e740c7ac87ae501f234b87b2815093e88e9a752262ae372dcdfeb6a1')
        comparison = C.read(area / 'fixture-comparison-r3/report.json', 'f65f414b929c9cedec5d34b6376b9e771a710a98f79e667550c28a143b950955')
        C.need(all(x['passed'] for x in (lift, host, prep, build, comparison)), 'All current candidate and actual six-case producer gates passed')
        C.need(host['full_state_bytes'] == 3504 and host['all_layouts_equal'] and host['strict_dynamic_rounding'] and
               host['normal_raw80_pointer_ABI'] and not host['AF_semantic_equality_claimed'], 'Strict raw80/State layout and explicit undefined AF domain')
        C.need(not prep['source_after_seed'] and not build['source_after_seed'] and
               comparison['original_AFTER_used_only_for_comparison'] and not comparison['host_cos_expected_output_used'] and
               not comparison['full_State_source_comparison'] and not comparison['provider_lifetime_controls'], 'Exact current bounded candidate/proof scope')
        for report in (lift, host, prep, build, comparison):
            for path, digest in report['files'].items():
                p = Path(path)
                if p.suffix.lower() in ('.py', '.cpp', '.hpp', '.h', '.ll', '.obj', '.exe', '.ninja') or p.name == 'CMakeLists.txt':
                    # Executable toolchain identity is already sealed by producers.
                    # This review physically rehashes actual workers and bounded consumed sources/objects.
                    if p.stat().st_size <= 64 * 1024 * 1024:
                        C.pin(p, digest)
        guest = C.pin(lift['guest_IR'], lift['guest_IR_sha256']).read_text()
        strict = C.pin(area / 'host-candidate-r1/4b64f0.strict-input.ll', host['files'][str(area / 'host-candidate-r1/4b64f0.strict-input.ll')]).read_text()
        # Inverse exact local transformations prove that no other source IR was changed.
        declarations = ('declare float @llvm.experimental.constrained.fptrunc.f32.f80(x86_fp80, metadata, metadata)',
                        'declare x86_fp80 @llvm.experimental.constrained.fpext.f80.f64(double, metadata)',
                        'declare void @mw34_actual_fcos_status_raw80(ptr, ptr, ptr)',
                        'declare i32 @mw34_fp_store_exception_test(ptr, i32)')
        original = strict
        for declaration in declarations:
            C.need(original.count('\n' + declaration + '\n') == 1, 'Only one exact added bridge/intrinsic declaration')
            original = original.replace('\n' + declaration + '\n', '')
        original, n = re.subn(r'^(  %\d+) = call float @llvm.experimental.constrained.fptrunc.f32.f80\(x86_fp80 (%\d+), metadata !"round.dynamic", metadata !"fpexcept.strict"\)$', r'\1 = fptrunc x86_fp80 \2 to float', original, flags=re.M)
        C.need(n == 3, 'Three strict dynamically rounded F32 source stores'); counts['strict_F32_store_sites'] = n
        original, n = re.subn(r'^(  %\d+) = call x86_fp80 @llvm.experimental.constrained.fpext.f80.f64\(double (%\d+), metadata !"fpexcept.strict"\)$', r'\1 = fpext double \2 to x86_fp80', original, flags=re.M)
        C.need(n == 3, 'Three strict F64 source loads'); counts['strict_F64_load_sites'] = n
        for index, (result, value) in enumerate((('117', '82'), ('421', '386'), ('650', '615'))):
            transport = (f'  %mw.cos.{index}.input = alloca x86_fp80, align 16\n  %mw.cos.{index}.output = alloca x86_fp80, align 16\n'
                         f'  store x86_fp80 %{value}, ptr %mw.cos.{index}.input, align 16\n'
                         f'  call void @mw34_actual_fcos_status_raw80(ptr %state, ptr %mw.cos.{index}.input, ptr %mw.cos.{index}.output)\n'
                         f'  %{result} = load x86_fp80, ptr %mw.cos.{index}.output, align 16')
            C.need(original.count(transport) == 1, 'Exact typed ten-byte cosine transport from live source value')
            original = original.replace(transport, f'  %{result} = call x86_fp80 @cosl(x86_fp80 noundef %{value}) #5')
        for index, (value, pointer) in enumerate((('115', '116'), ('258', '259'), ('419', '420'), ('487', '488'), ('648', '649'), ('716', '717'))):
            C.need(f'  %{pointer} = getelementptr inbounds nuw i8, ptr %state, i32 2753' in guest, 'Only actual source sticky DE field')
            repair = f'  %mw.de.{index}.prior = load i8, ptr %{pointer}, align 1\n  %mw.de.{index}.sticky = or i8 %{value}, %mw.de.{index}.prior\n  store i8 %mw.de.{index}.sticky, ptr %{pointer}, align 1'
            C.need(original.count(repair) == 1, 'Exact six source sticky exception repairs')
            original = original.replace(repair, f'  store i8 %{value}, ptr %{pointer}, align 1')
        for result in ('261', '490', '719'):
            old = f'  %{result} = call i32 @mw34_fp_store_exception_test(ptr %state, i32 127)'
            C.need(original.count(old) == 1, 'Exactly one hardware C1 capture per source FSTP')
            original = original.replace(old, f'  %{result} = call i32 @__remill_fpu_exception_test(i32 noundef 127) #5')
        original = original.replace('ptr noalias %memory) strictfp {', 'ptr noalias %memory) {')
        declaration = next(line for line in guest.splitlines(True) if line.startswith('declare dso_local x86_fp80 @cosl('))
        position = original.index('declare dso_local i32 @__remill_fpu_exception_test')
        position = position
        original = original[:position - 1] + declaration + '\n' + original[position:]
        if original != guest:
            import difflib
            print(''.join(difflib.unified_diff(guest.splitlines(True), original.splitlines(True))))
        C.need(original == guest, 'Inverse exact strict adaptation restores entire genuine guest IR byte-for-byte')
        counts['exact_raw80_cosine_sites'] = 3; counts['exact_sticky_DE_sites'] = 6
        host_ir = C.pin(host['host_IR'], host['host_IR_sha256']).read_text()
        C.need('@cosl' not in host_ir and 'ptrtoint' not in host_ir and 'inttoptr' not in host_ir and
               'define dso_local zeroext i8 @__remill_undefined_8()' in host_ir and
               'undefined_AF_representative:\n  ret i8 0' in host_ir, 'No host cosine, integer host-pointer conversion or defined AF equality')
        prepdir = area / 'fixture-preparation-r1'
        native = C.pin(prepdir / 'native.cpp', prep['files'][str(prepdir / 'native.cpp')]).read_text()
        raw80 = C.pin(prepdir / 'raw80.cpp', prep['files'][str(prepdir / 'raw80.cpp')]).read_text()
        store = C.pin(prepdir / 'store_test.cpp', prep['files'][str(prepdir / 'store_test.cpp')]).read_text()
        C.need('fldt %2\\n\\tfcos\\n\\tfnstsw %0\\n\\tfstpt %1' in raw80 and
               'state->sw.c2=(status>>10)&1' in raw80 and 'state->sw.c1=(status>>9)&1' in store and
               '__remill_fpu_exception_test(mask)' in store, 'Actual raw80 FCOS C2 and actual narrowed FSTP C1; no prediction')
        for text in ('sequence<6', '3480', 'sequence*580', 'std::memcpy(&s.x87,input+40,512)',
                     'std::memcmp(&initial_cpu,input,40)==0', 'sizeof(Result)==361836', 'sizeof(State)==3504',
                     'event_count!=14', 'reads!=4', 'writes!=10', 'clears!=6', 'tests!=6', 'primitives!=3',
                     'positions[]{1,10,12}', 'positions[]{1,8,10,10,12,12}', 'mask!=127',
                     'memory.protect', 'owner!=std::this_thread::get_id()', 'root.entry', 'pc!=sentinel',
                     's.gpr.rsp.dword!=frame+4'):
            C.need(text in native, 'Finite worker source guard ' + text)
        PE = module(ROOT / 'tools/analysis/pe.py', 'native_cosine_review_PE')
        for level in ('O0', 'O2'):
            tree = area / 'fixture-build-r1' / ('build-' + level)
            graph = C.pin(tree / 'build.ninja', build['files'][str(tree / 'build.ninja')]).read_text()
            linkline = next(line for line in graph.splitlines() if line.startswith('build mw34_compound_cosine.exe:'))
            C.need(linkline.count('.obj') == 5 and ('4b64f0-' + level + '.obj') in linkline and
                   all(x in linkline for x in ('native.cpp.obj', 'raw80.cpp.obj', 'store_test.cpp.obj', 'guest_memory.cpp.obj')),
                   'Exactly the five genuine consumed actual AMD64 link inputs')
            worker = build['workers'][level]
            image = PE.PEImage(C.pin(worker['path'], worker['sha256']).read_bytes())
            C.need(image.machine == 0x8664, 'Actual final worker is AMD64')
            bodies = []
            for obj, name in ((Path(worker['literal_object']), 'sub_4b64f0'),
                              (tree / 'CMakeFiles/mw34_compound_cosine.dir/raw80.cpp.obj', 'mw34_actual_fcos_status_raw80'),
                              (tree / 'CMakeFiles/mw34_compound_cosine.dir/store_test.cpp.obj', 'mw34_fp_store_exception_test')):
                data = C.pin(obj, build['files'][str(obj)]).read_bytes()
                symbols, sections = A.parse(data)
                raw, relocations = A.function(symbols, sections, name)
                matches = A.linked_candidates(image, raw, relocations)
                C.need(len(matches) == 1, 'One whole actual final-linked literal/math body ' + name)
                address, actual = matches[0]
                rows = []
                for relocation in relocations:
                    offset = relocation['offset']; target = address + offset + 4 + struct.unpack_from('<i', actual, offset)[0]
                    symbol = relocation['symbol']; addend = struct.unpack_from('<i', raw, offset)[0]
                    rows.append(dict(offset=offset, symbol=symbol['name'], actual_target=target, addend=addend))
                    if symbol['section'] > 0 and symbol['type'] != 0x20:
                        section = sections[symbol['section']]
                        expected = section['bytes'][symbol['value'] + addend:]
                        physical, _ = image.rva_range(target - image.image_base, len(expected))
                        C.need(expected and image.data[physical:physical + len(expected)] == expected, 'Every complete actual linked constant byte')
                        counts['linked_full_constant_relations'] += 1
                bodies.append(dict(name=name, address=address, bytes=len(raw), COFF_sha256=C.PINS[str(obj.resolve())], relocations=rows))
                counts['whole_final_linked_function_bytes'] += len(raw); counts['whole_final_linked_functions'] += 1
                counts['actual_REL32_bindings'] += len(relocations)
                if name == 'mw34_actual_fcos_status_raw80':
                    C.need(raw.count(b'\xd9\xff') == 1 and (b'\xb5\x0a\0\0') in raw, 'Final compiled hardware FCOS plus source C2 offset2741')
                if name == 'mw34_fp_store_exception_test':
                    C.need(b'\xb3\x0a\0\0' in raw, 'Final compiled source C1 offset2739')
            targets = {row['name']:row['address'] for row in bodies}
            for body in bodies:
                for row in body['relocations']:
                    if row['symbol'] in targets:
                        C.need(row['actual_target'] == targets[row['symbol']] + row['addend'], 'Every exact final source-to-math actual target')
                        counts['literal_to_actual_math_target_relations'] += 1
            linked.append(dict(level=level, actual_linked_inputs=5, bodies=bodies))
            counts['actual_consumed_link_objects'] += 5
        expected_counts = dict(complete_CPU_endpoint_relations=24, raw80_register_relations=192,
                               FX512_architectural_relations=24, complete_ENV28_relations=24,
                               whole_43page_endpoint_relations=1032, actual_original_native_F32_pairs=36,
                               native_root_phases=12, literal_access_order_rows=168,
                               actual_architectural_host_FX_and_whole_ENV_pairs=12)
        C.need(comparison['counts'] == expected_counts, 'Exact producing current six-case original/native observations')
        observation_path = area / 'fixture-comparison-r3/observations.json'
        observations = C.read(observation_path, comparison['files'][str(observation_path)])
        C.need(len(observations) == 12 and {(r['level'],r['sequence']) for r in observations} == {(l,s) for l in ('O0','O2') for s in range(6)}, 'Every actual compared six-case level')
        for row in observations:
            C.need(len(row['outputs']) == 3 and [x['address'] for x in row['outputs']] == [0x5e8880,0x5e8884,0x5e8888] and
                   all(x['offset'] >= 416 for x in row['host_FX_raw_differences']) and
                   row['whole_host_FX512_equality_claimed'] is False and row['XOR_AF_semantic_equality_claimed'] is False and
                   row['full_State_source_comparison'] is False, 'Retain actual output bits/reserved host diffs with exact architectural scope')
        counts['independently_bound_actual_comparison_cases'] = 12
        passed = True
    finally:
        artifact = out / 'linked-attribution.json'; artifact.write_text(json.dumps(linked, indent=2) + '\n'); C.pin(artifact)
        report = dict(passed=passed, scope='Independent exact IR/source/AMD64 compiled-final-link and compact six-case comparison scope review; no payload reread',
                      counts=dict(counts), actual_comparison_sha256='f65f414b929c9cedec5d34b6376b9e771a710a98f79e667550c28a143b950955',
                      capture_archives_opened=0, native_result_payloads_opened=0, source_AFTER_seed=False,
                      host_cos_expected_output_used=False, whole_host_FX512_equality_claimed=False,
                      full_State_source_equivalence=False, controls_accepted=False, generic_FCOS_claim=False, initializer_credit=0, files=C.PINS)
        target = out / 'report.json'; target.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=C.hashlib.sha256(target.read_bytes()).hexdigest(), counts=dict(counts))))


if __name__ == '__main__':
    main(sys.argv[1])
