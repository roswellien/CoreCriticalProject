"""Independently bind the complete131 reader before any capture is opened."""
from pathlib import Path
import ast, hashlib, json, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

def main(name):
    out = ROOT / 'reports/m4-tree-review' / name
    assert not out.exists()
    out.mkdir(parents=True)
    files, counts = {}, {}
    passed = False
    def pin(path, expected=None):
        path = Path(path).resolve()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert expected is None or digest == expected, (path, expected, digest)
        assert str(path) not in files or files[str(path)] == digest
        files[str(path)] = digest
        return path
    def text(path):
        return pin(path).read_text()
    try:
        base = ROOT / 'tools/m4-joint-startup131'
        p = ROOT / 'reports/m4-joint-startup131-source'
        for version in range(1, 5):
            receipt = json.loads(pin(p / f'preparation-r{version}/report.json').read_bytes())
            assert receipt['passed']
            for path, digest in receipt['files'].items():
                pin(path, digest)
        # Reconstruct the first complete source from the accepted130 source,
        # using only static constant replacements from its frozen preparer.
        parent = text(ROOT / 'tools/m4-formatting-source/compare_provider130_v6.py')
        prep = ast.parse(text(base / 'prepare_source.py'))
        constants = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.walk(prep) if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and isinstance(n.value, ast.Constant)}
        def constant(node):
            return constants[node.id] if isinstance(node, ast.Name) else ast.literal_eval(node)
        changes = []
        for node in ast.walk(prep):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'one':
                changes.append((node.lineno, constant(node.args[0]), constant(node.args[1])))
        for _, old, new in sorted(changes):
            assert parent.count(old) == 1, old
            parent = parent.replace(old, new)
        parent = parent.replace('persistent130_sequences', 'persistent131_sequences').replace('persistent native130', 'persistent native131').replace('Every130 phase', 'Every131 phase').replace('selected130', 'selected131')
        assert parent == text(base / 'compare_provider.py')
        counts['exact_130_to_131_replacements'] = len(changes)
        for version in (2, 3, 4):
            receipt = json.loads((p / f'preparation-r{version}/report.json').read_bytes())
            for change in receipt['changes']:
                assert parent.count(change['before']) == 1
                parent = parent.replace(change['before'], change['after'])
            if version == 4:
                # This metadata addition is explicit in prepare_source_v4.
                assert parent.count('reader_closed=readers_closed,') == 1
                parent = parent.replace('reader_closed=readers_closed,', 'reader_closed=readers_closed,paired_export_readers_closed=readers_closed,')
            assert parent == text(base / f'compare_provider_v{version}.py')
        tree = ast.parse(parent)
        imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        assert 'mfc_source_v2' in parent and 'paired_exports' in parent
        assert "finally:a.close();a.entries.clear()" in parent
        assert "if ori is not None:ori.close();ori.entries.clear();ori.bundles.clear()" in parent
        assert "if len([r for r in rows if r['level']==level])==786:" in parent
        assert "[r['branch']for r in paired_exports]==['original','O0','O2']" in parent
        assert "source_and_provider_combined=True" in parent
        assert "per_phase_BEFORE_machine_seed=False,candidate_AFTER_machine_seed=False" in parent
        # Unchanged old continuity with one declared inserted root only.
        old = text(ROOT / 'tools/m4-formatting-source/continuity130.py')
        expected = old.replace("'selected-table.bin',130", "'selected-table.bin',131").replace('entry==0x4c19f0', 'entry in(0x4c19f0,0x5ae3e4)')
        assert expected == text(base / 'continuity131.py')
        mfc = text(base / 'mfc_source.py')
        assert "need('/BEFORE/' in key" in mfc
        assert 'self.literal.derive(state, fx, cpu, machine.memory' in mfc
        assert 'eq(expected,archive.data' in mfc
        assert 'candidate' not in mfc.replace('candidate phase snapshot', '')
        wrapper = text(ROOT / 'tools/m4-mfc1168-native/persistent_source_v2.py')
        assert "text.replace('index+=1;domain={}','index+=1')" in wrapper
        assert 'consumer=FC.check(m,r,domain)' in wrapper
        exporter = text(base / 'paired_exports.py')
        assert "if self.branch=='original'or selected(key)" in exporter
        assert "'Exact per-access current equality target digest '" in exporter
        assert "'Whole bounded equality target payload stable after consumer closure'" in exporter
        for folder, digest in [('preflight-r2', '42c3f4d323a769a08625fe8ca507c97a2c4150a5b1c613e7f7de55af940f5ff7'), ('preflight-r3', '1d15d96816e54073c94136577db2f3024d1fde579023808110826df16e8245ad')]:
            preflight = json.loads(pin(p / folder / 'report.json', digest).read_bytes())
            assert preflight['passed'] and preflight['capture_reader_opened'] is False
            for path, digest in preflight['files'].items():
                pin(path, digest)
        native = json.loads(pin(ROOT / 'reports/m4-joint-startup131/preparation-r1/report.json', '2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25').read_bytes())
        accepted = json.loads(pin(ROOT / 'reports/m4-joint-startup130/preparation-r2/report.json', '060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c').read_bytes())
        assert native['selected_order'][13] == {'entry': 0x5ae3e4, 'slot': 0x5e0040}
        assert native['selected_order'][:13] + native['selected_order'][14:] == accepted['selected_order']
        counts.update(unchanged_selected_order=130, inserted_literal_phase=13, current_reader_versions=4, raw_export_branches=3, reader_close_guards=2)
        pin(__file__)
        for path, digest in files.items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        report = dict(passed=passed, scope='Independent physical complete131 source-reader delta, declared loader inputs, architectural consumer checks and guaranteed canonical closure; actual equality remains execution obligation', counts=counts, files=files, capture_reader_opened=False, worker_executed=False, initializer_credit=0)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=hashlib.sha256((out / 'report.json').read_bytes()).hexdigest(), files=len(files))))

if __name__ == '__main__':
    main(sys.argv[1])
