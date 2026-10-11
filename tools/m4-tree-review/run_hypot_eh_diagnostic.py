"""Preserve exact finite host-EH diagnostic outputs, without fault credit."""
from pathlib import Path
import hashlib, json, subprocess, sys

sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
PINS = {}

def need(ok, message):
    if not ok: raise ValueError(message)

def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()

def pin(path, expected=None):
    path = Path(path).resolve(); digest = sha(path)
    need(expected is None or expected == digest, 'Physical identity ' + str(path))
    need(str(path) not in PINS or PINS[str(path)] == digest, 'Unchanged physical identity')
    PINS[str(path)] = digest
    return path

def main(name):
    out = R / 'reports/m4-tree-review' / name
    need(not out.exists(), 'Additive output')
    build_dir = R / 'reports/m4-tree-review/hypot-EH-diagnostic-build-r1'
    build_path = pin(build_dir / 'report.json')
    build = json.loads(build_path.read_text(encoding='utf-8-sig'))
    need(build['passed'] and build['diagnostic_only'] and build['initializer_credit'] == 0, 'Successful diagnostic compilation')
    for path, digest in build['files'].items(): pin(path, digest)
    dependencies = set()
    for dep in sorted(build_dir.glob('*.d')):
        lines = pin(dep).read_text().splitlines()
        need(lines and lines[0].endswith(': \\'), 'Exact emitted dependency target')
        for line in lines[1:]:
            line = line.strip()
            if line.endswith(' \\'): line = line[:-2]
            path = line.replace('\\ ', ' ')
            need(Path(path).is_file(), 'Unambiguous compiler dependency ' + path)
            dependencies.add(str(pin(path)))
    out.mkdir()
    levels = []
    for level in ('O0', 'O2'):
        worker = pin(build_dir / ('diagnostic-'+level+'.exe'))
        result = subprocess.run([str(worker)], capture_output=True, timeout=30, creationflags=0x08000000)
        for suffix, raw in (('stdout', result.stdout), ('stderr', result.stderr)):
            target = out / (level+'.'+suffix); target.write_bytes(raw); pin(target)
        need(result.returncode == 0 and not result.stderr, 'Actual diagnostic exit/stdout')
        rows = json.loads(result.stdout)
        need(rows['diagnostic_only'] and rows['initializer_credit'] == 0 and len(rows['rows']) == 4, 'Actual four diagnostic paths')
        for row in rows['rows']:
            need(row['refused'] and row['two_State_backings_equal'] and row['operand12_equal'], 'Whole guest conservation in diagnostic')
            for side in ('before', 'after', 'immediately_restored'):
                need(len(bytes.fromhex(row[side]['FX512_hex'])) == 512 and len(bytes.fromhex(row[side]['ENV28_hex'])) == 28, 'Every whole raw diagnostic endpoint')
        actual = rows['rows'][3]
        comparisons = []
        for row in rows['rows']:
            before, after, restored = [bytes.fromhex(row[x]['ENV28_hex']) for x in ('before', 'after', 'immediately_restored')]
            comparisons.append(dict(kind=row['kind'], ENV28_before_hex=before.hex(),
                ENV28_after_hex=after.hex(), ENV28_immediately_restored_hex=restored.hex(),
                changed_after_offsets=[i for i in range(28) if before[i] != after[i]],
                changed_restore_offsets=[i for i in range(28) if before[i] != restored[i]],
                whole_after_ENV_equal_actual_denial=row['after']['ENV28_hex']==actual['after']['ENV28_hex']))
        levels.append(dict(level=level, raw_rows=rows['rows'], comparisons=comparisons))
    for path, digest in list(PINS.items()): pin(path, digest)
    pin(__file__); pin(sys.executable)
    observation = out / 'actual-observations.json'
    observation.write_text(json.dumps(levels, indent=2)+'\n'); pin(observation)
    report = dict(passed=True, diagnostic_only=True, build_path=str(build_path), build_sha256=sha(build_path),
        levels=2, actual_host_EH_paths=6, actual_kind0_denials=2,
        complete_raw_hardware_endpoints=24, full_ENV_bytes=28, full_FX_bytes=512,
        compiler_consumed_dependencies_physically_pinned=len(dependencies),
        initializer_credit=0, negative_control_acceptance_credit=0,
        source_helper_equivalence_credit=0, game_or_archive_process_opened=False,
        scope='Actual finite diagnostic observations only. Equality and restoration outcomes are retained as data, not weakened refusal predicates. '
              'The successful diagnostic status confirms capture and full guest-backing assertions; it does not assert hardware ENV preservation or baseline equivalence.',
        files=PINS)
    target = out / 'report.json'; target.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(passed=True, path=str(target), sha256=sha(target),
         dependency_count=len(dependencies), levels=[dict(level=x['level'], comparisons=x['comparisons']) for x in levels])))

if __name__ == '__main__': main(sys.argv[1])
