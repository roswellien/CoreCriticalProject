"""Exercise the real recipe's early admission with pre-existing marker fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import uuid


def bind(path):
    return {'path': str(path.resolve()), 'size_bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def inventory(path):
    if not path.exists():
        return None
    return {p.relative_to(path).as_posix(): ('directory' if p.is_dir() else bind(p))
            for p in sorted(path.rglob('*'))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--powershell', type=Path, required=True)
    parser.add_argument('--recipe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise ValueError('Build-directory controls require a fresh record')
    root = args.recipe.resolve().parents[2]
    fixture_root = root / 'reports/m4-initializer' / ('directory-admission-' + uuid.uuid4().hex)
    fixture_root.mkdir()
    checks = []
    for index, target in enumerate(('partial-report', 'reference', 'O0', 'O2')):
        leaf = f'fixture-{target}-{uuid.uuid4().hex}'
        candidate = fixture_root / leaf
        builds = {label: root / 'build' / f'm4-initializer-{leaf}-{label}'
                  for label in ('reference', 'O0', 'O2')}
        observed = {'report': candidate, **builds}
        if any(path.exists() for path in observed.values()):
            raise ValueError('Fixture paths unexpectedly pre-exist')
        existing = candidate if target == 'partial-report' else builds[target]
        existing.mkdir()
        (existing / 'nested').mkdir()
        (existing / 'marker.bin').write_bytes(b'MW34 existing directory evidence\x00\xff' + bytes([index]) * 37)
        (existing / 'nested/keep.txt').write_text('Externally authored fixture; preserve exact bytes.\n', encoding='utf-8')
        before = {name: inventory(path) for name, path in observed.items()}
        command = [str(args.powershell.resolve()), '-NoProfile', '-ExecutionPolicy', 'Bypass',
                   '-File', str(args.recipe.resolve()), '-OutputDirectory', str(candidate),
                   '-Image', str(fixture_root / 'intentionally-absent-private-image.exe')]
        run = subprocess.run(command, capture_output=True, timeout=60, cwd=root)
        log = fixture_root / f'{target}.log'
        log.write_bytes(run.stdout + run.stderr)
        diagnostic = ('M4 report output already exists; use an entirely fresh OutputDirectory'
                      if target == 'partial-report' else
                      'M4 derived build directory already exists: ' + target)
        # PowerShell 7 wraps long diagnostics for display; normalize whitespace.
        rendered = ' '.join((run.stdout + run.stderr).decode(errors='replace').split())
        if run.returncode == 0 or diagnostic not in rendered:
            raise ValueError('Real recipe missed intended early admission: ' + target)
        after = {name: inventory(path) for name, path in observed.items()}
        if before != after:
            raise ValueError('Rejected recipe mutated fixture or created an output: ' + target)
        checks.append({'target': target, 'command': command, 'exit_code': run.returncode,
                       'intended_diagnostic': diagnostic,
                       'observed_paths': {name: str(path) for name, path in observed.items()},
                       'before': before, 'after': after, 'log': bind(log)})
    record = {'schema_version': 1, 'passed': True, 'controls': len(checks),
              'scope': 'Actual PowerShell recipe; existing partial report and all three derived build dirs rejected before source/private-input work or writes',
              'recipe': bind(args.recipe.resolve()), 'powershell': bind(args.powershell.resolve()),
              'fixture_root': str(fixture_root), 'checks': checks}
    output.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print('Actual build-directory preservation controls:', len(checks))


if __name__ == '__main__':
    main()
