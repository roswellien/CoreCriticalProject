"""Physical first-writer admission of the six registered widget routes."""
from pathlib import Path
import collections, hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]

def main(name):
    out = R / 'reports/m4-tree-review' / name
    assert not out.exists()
    out.mkdir(parents=True)
    files, counts, links = {}, collections.Counter(), []
    passed = False
    def pin(path, digest=None):
        path = Path(path).resolve()
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest is None or digest == h, (path, digest, h)
        assert str(path) not in files or files[str(path)] == h
        files[str(path)] = h
        return path
    def receipt(path, digest):
        d = json.loads(pin(path, digest).read_bytes())
        assert d['passed']
        for p, h in d['files'].items():
            pin(p, h)
        return d
    def load(path, name):
        spec = importlib.util.spec_from_file_location(name, pin(path))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    try:
        base = R / 'reports/m4-widget-native'
        ph = 'c761842bfb644d9bf6ec943f5c8c686facb5bc7efd1c4da2fd7151e15a112eb9'
        bh = '4bd792e4cac56bfce6a635f53ff2cf5d0030e50572169e75d03bbcf977bb9e60'
        prep = receipt(base / 'fixture-preparation-r9/report.json', ph)
        build = receipt(base / 'fixture-build-r9/build.json', bh)
        comp = receipt(base / 'preparation-r3/report.json', '69a29eddf46f6c189edc462e5f5734a96e3d98c2c1f37778a54d36c0fd62eae5')
        cb = receipt(base / 'build-r5/build.json', '9c053306dbf44a3a65ac1945dd4c2b0949ef064842004e05bf2e6cc29a22fada')
        service = receipt(base / 'service-preparation-r2/report.json', 'd10b800a817dd3fc684f276d5df19154748b2b0735137d062d9bff05376a1fca')
        tail = receipt(R / 'reports/m4-widget-original-review/registration-tail-r1/report.json', 'abaa48c8dd533c56cdbd48118676bf0800f0c942ce9319a537a03c4c4b4f3cb5')
        assert build['preparation_sha256'] == ph
        assert prep['source_roots'] == [0x40e250, 0x40ef50, 0x5a3c30, 0x5a3ff0, 0x5a66f0, 0x479590]
        assert comp['literal_bodies'] == 51 and comp['causal_operands'] == 24643
        assert comp['literal_epilogue_read_operands'] == 18
        assert not prep['original_CPU_or_GDI_seeds'] and not prep['AFTER_machine_seed'] and not prep['per_root_State_or_page_seed']
        for row in comp['namespace_relations']:
            a = pin(row['original_IR'], row['original_sha256']).read_bytes()
            b = pin(row['component_IR'], row['component_sha256']).read_bytes()
            assert a.replace(b'mw34_onexit_game_', b'mw34_widget_game_') == b
            counts['whole_exact_literal_IR_namespaces'] += 1
        add = pin(R / 'tools/m4-widget-native/borrowed_onexit_v2.inc', '49a00a44308944c37a2bd60822df3d74ec779bdf56d820c9ad369b9c0af90a14').read_text()
        for row in service['source_relations']:
            a, b = pin(row['parent'], row['parent_sha256']).read_text(), pin(row['child'], row['child_sha256']).read_text()
            leaf = Path(row['child']).name
            if leaf == 'session.hpp':
                a = a.replace(' void finish();void dump(Sink,void*)const;', ' void borrow_widget_onexit(State&,unsigned root,unsigned frame,unsigned return_pc);\n void finish();void dump(Sink,void*)const;')
            elif leaf == 'session_impl.inc':
                a = a.replace(' void finish(){', add + '\n void finish(){')
                a = a.replace('void Session::bootstrap(){', 'void Session::borrow_widget_onexit(State&s,unsigned root,unsigned frame,unsigned ret){impl_->borrow_widget_onexit(s,root,frame,ret);}\nvoid Session::bootstrap(){')
            assert a == b, leaf
            counts['whole_parent_service_source_relations'] += 1
        component = pin(base / 'preparation-r3/component.cpp').read_text()
        for guard in ['current==this&&GetCurrentThreadId()==thread', 'pc==e.pc&&a==expected&&width==e.width&&writing==e.writing', 'same', 'value==pc+literal::instruction(pc)->size', 'a==s.gpr.rsp.dword-4', 'operand_cursor==root->operand_count']:
            if guard != 'same':
                assert guard in component
        assert 'mw34_widget_native_api(providers[index],args.data(),&rec.hardware)' in component
        assert 'mw34_widget_hardware_call(&task,&hardware)' in component
        assert 't.owner->failed=true;t.exception=std::current_exception()' in component
        assert 'lb::dispatch_body(0x78004a36,&s,binding.get())' in add
        assert 'frame+24==r.cpu().esp' in add and 'next+4' in add
        fixture = pin(base / 'fixture-preparation-r9/fixture.cpp').read_text()
        assert 'Runtime::from_admitted_image(game' in fixture and 'registry.bootstrap();' in fixture
        assert 'registry.finish();' in fixture and 'component.cleanup_fonts(hardware)' in fixture
        inherited = pin(base / 'fixture-preparation-r9/inherited_main.cpp').read_text()
        old = pin(R / 'reports/m4-joint-startup130/preparation-r2/native_main.cpp').read_text()
        # Only include-path disambiguation is allowed in the inherited adapters.
        normalize = lambda t: re.sub(r'#include "[^"]*(session\.hpp)"', '#include "session.hpp"', t)
        assert normalize(inherited) == normalize(old)
        C = load(R / 'tools/m4-tree-review/amd64_coff.py', 'widget6_actual_coff')
        PE = load(R / 'tools/analysis/pe.py', 'widget6_actual_pe')
        N = load(R / 'tools/m4-tree-review/review_hypot_c1_controls_prelaunch_v2.py', 'widget6_actual_image')
        for level in ('O0', 'O2'):
            image = PE.PEImage(pin(build['workers'][level]['path'], build['workers'][level]['sha256']).read_bytes())
            assert image.machine == 0x8664
            leveldir = base / 'fixture-build-r9' / level
            objects = [leveldir / 'fixture.obj', leveldir / 'registry.obj', *map(Path, cb['levels'][level]['objects'])]
            parsed = {str(p): C.parse(pin(p).read_bytes()) for p in objects}
            definitions = {}
            for p in objects:
                sy, se = parsed[str(p)]
                for s in sy.values():
                    n = s['name']
                    if s['section'] <= 0 or s['type'] != 32:
                        continue
                    selected = (n == 'main' or n.startswith(('?initialize_current_caller@', '?whole_current_game@', '?borrow_widget_onexit@')) or '@AcceptedServices@' in n or (p.name == 'component.obj' and (n.startswith('mw34_widget_') or '@Impl@Component@m4_widget_native@mw34@@' in n and not n.startswith(('??$', '?dtor$', '?catch$', '?size@', '?data@')) or '@Component@m4_widget_native@mw34@@' in n and n.startswith(('?execute@', '?cleanup_fonts@', '?entry_', '??0Component', '??1Component')) or '@literal@m4_widget_native@mw34@@' in n)) or n.startswith('mw34_widget_game_') and n.endswith('_body'))
                    if selected:
                        raw, rels = C.function(sy, se, n)
                        assert n not in definitions
                        definitions[n] = (p, raw, rels, se)
            # Exact assembly labels are known to be type0 in this assembler.
            ap = next(p for p in objects if p.name == 'native_api.obj')
            sy, se = parsed[str(ap)]
            for s in sy.values():
                if s['name'] in ('mw34_widget_native_api', 'mw34_widget_hardware_call'):
                    assert s['type'] == 0 and s['section'] == 1
                    s['type'] = 32
            for n in ('mw34_widget_native_api', 'mw34_widget_hardware_call'):
                raw, rels = C.function(sy, se, n)
                definitions[n] = (ap, raw, rels, se)
            assert len(definitions['mw34_widget_native_api'][1]) == 211 and not definitions['mw34_widget_native_api'][2]
            assert len(definitions['mw34_widget_hardware_call'][1]) == 85
            candidate_sets = {}
            for n, (p, raw, rels, se) in definitions.items():
                assert all(4 <= r['type'] <= 9 or r['type'] == 11 and r['symbol']['section'] > 0 for r in rels), (n, [(r['type'], r['symbol']['name']) for r in rels if not 4 <= r['type'] <= 9])
                for r in rels:
                    if r['type'] == 11:
                        s = r['symbol']
                        assert s['name'].startswith(('?current@?A0x87B81194@m4_widget_native@', '?session_owner@?A0x948FD806@m4_onexit@', '?authority@?A0x948FD806@', '?owner@m4_', '?binding@m4_', '?admitted_binding@m4_'))
                        assert se[s['section']]['bytes'][s['value']:s['value'] + 8] == bytes(8)
                matches = C.linked_candidates(image, raw, [dict(r, type=4) for r in rels])
                assert matches, (level, n, len(raw))
                candidate_sets[n] = matches
            # A relocation target must be a whole physically matching function,
            # including aliases that share identical emitted machine bytes.
            for n, (p, raw, rels, se) in definitions.items():
                matches = candidate_sets[n]
                for r in rels:
                    target_name = r['symbol']['name']
                    if 4 <= r['type'] <= 9 and target_name in candidate_sets:
                        targets = {a for a, _ in candidate_sets[target_name]}
                        matches = [(a, b) for a, b in matches if a + r['offset'] + 4 + r['type'] - 4 + struct.unpack_from('<i', b, r['offset'])[0] in targets]
                        assert matches, (level, n, target_name)
                        counts['exact_linked_function_target_relations'] += 1
                for a, b in matches:
                    for r in rels:
                        if r['type'] != 11:
                            continue
                        s = r['symbol']
                        v = struct.unpack_from('<i', b, r['offset'])[0] - struct.unpack_from('<i', raw, r['offset'])[0] - s['value']
                        d = N.directories(image)[9]
                        start, end, _, _, zero, _ = struct.unpack('<4Q2I', N.image_bytes(image, image.image_base + d[0], 40))
                        assert v >= 0 and v + s['value'] + 8 <= end - start + zero
                        assert N.image_bytes(image, start + v + s['value'], 8) == bytes(8)
                        counts['actual_initialized_TLS_cells'] += 1
                links.append(dict(level=level, object=str(p), symbol=n, whole_bytes=len(raw), relocation_DWORDs=len(rels), whole_linked_candidates=[a for a, _ in matches], source_sha256=hashlib.sha256(raw).hexdigest()))
                counts['whole_compiled_functions'] += 1
            literal = [n for n in definitions if re.fullmatch('mw34_widget_game_[0-9a-f]+_body', n)]
            assert len(literal) == 51
            for root in prep['source_roots']:
                assert any(n.startswith('?entry_%x@' % root) for n in definitions)
            boundary = definitions['mw34_widget_hardware_call']
            assert [(r['offset'], r['type'], r['symbol']['name']) for r in boundary[2]] == [(25, 4, 'mw34_widget_invoke_guarded')]
            pdata = se[5]['bytes']
            assert pdata == struct.pack('<6I', 0, 211, 0, 211, 296, 12)
            ex = N.directories(image)[3]
            entries = list(struct.iter_unpack('<3I', N.image_bytes(image, image.image_base + ex[0], ex[1])))
            for n, length, uw_start, uw_size in [('mw34_widget_native_api', 211, 0, 12), ('mw34_widget_hardware_call', 85, 12, 8)]:
                assert len(candidate_sets[n]) == 1
                a = candidate_sets[n][0][0]
                actual = [e for e in entries if image.image_base + e[0] == a]
                assert len(actual) == 1 and image.image_base + actual[0][1] == a + length
                assert N.image_bytes(image, image.image_base + actual[0][2], uw_size) == se[4]['bytes'][uw_start:uw_start + uw_size]
                counts['whole_ASM_unwind_relations'] += 1
            linkcommand = [c for c in build['commands'] if c.get('expanded_response_arguments') and str(leveldir) in ' '.join(c['argv'])]
            assert len(linkcommand) == 1 and linkcommand[0]['exit_code'] == 0
            args = linkcommand[0]['expanded_response_arguments']
            assert all(str(p).casefold() in {v.casefold() for v in args} for p in prep['levels'][level]['objects'])
            assert prep['levels'][level]['component_library'].casefold() in {v.casefold() for v in args}
            assert prep['levels'][level]['fixed_objects'] == 427
            counts['bound_accepted_COFFER_inputs'] += 427
        runner = pin(R / 'tools/m4-widget-native/run_fixture_v2.py', '8de110b271ce8fe7210ca24f7ea5846346ffa5cd2871ad2f1cc92b0f827d1936').read_text()
        assert runner.index("for q,h in list(pins.items())") < runner.index('  passed=True')
        pin(__file__)
        for path, h in files.items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == h
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        (out / 'physical-links.json').write_text(json.dumps(links, indent=2) + '\n')
        pin(out / 'physical-links.json')
        report = dict(passed=passed, build_sha256='4bd792e4cac56bfce6a635f53ff2cf5d0030e50572169e75d03bbcf977bb9e60', preparation_sha256='c761842bfb644d9bf6ec943f5c8c686facb5bc7efd1c4da2fd7151e15a112eb9', scope='Independent physical six-widget first-writer admission; own input, actual accepted borrowed onexit, whole linked AMD64 functions, causal guards and exact API/caller assembly; source/native and connected136 acceptance remain separate', counts=dict(counts), files=files, worker_executed=False, capture_reader_opened=False, initializer_credit=0)
        f = out / 'report.json'
        f.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=hashlib.sha256(f.read_bytes()).hexdigest(), counts=dict(counts), files=len(files))))

if __name__ == '__main__':
    main(sys.argv[1])
