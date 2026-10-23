"""Prepare a private controller-capable successor of a pinned host; never change the selected profile."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from apply_controller_input import apply


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(base, output):
    base, output = Path(base).resolve(strict=True), Path(output).resolve()
    snapshot = json.loads((base / 'source-snapshot.json').read_text())
    for name, pin in snapshot['host_source_pins'].items():
        if sha(base / 'host-source' / name) != pin:
            raise ValueError('Native base source changed: ' + name)
    if sha(base / 'build/entry_commandline.exe') != snapshot['executable_sha256']:
        raise ValueError('Native base executable changed')
    if output.exists():
        raise ValueError('Use a fresh controller build directory')
    output.mkdir(parents=True)
    for directory in ('host-source', 'build-definition'):
        shutil.copytree(base / directory, output / directory)
    for name in ('optimized-mfc-objects.txt', 'build.ps1'):
        shutil.copy2(base / name, output / name)
    apply(output / 'host-source')
    snapshot['base_executable_sha256'] = snapshot.pop('executable_sha256')
    snapshot['base_source_snapshot'] = str(base / 'source-snapshot.json')
    snapshot['controller_input_version'] = 1
    snapshot['controller_scope'] = 'Opt-in SDL3 original command and analog-input adapter; original translated objects and rendering retained. Physical hardware validation pending.'
    snapshot['host_source_pins'] = {p.relative_to(output / 'host-source').as_posix(): sha(p)
                                    for p in (output / 'host-source').rglob('*') if p.is_file()}
    (output / 'source-snapshot.pending.json').write_text(json.dumps(snapshot, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    prepare(args.base, args.output)
