"""Prepare a private install-capable successor without changing the selected host.

This is development build preparation, not user-file generation or a release
packager. Existing translated objects stay local and are not copied into output.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

from apply_installed_support_paths import apply


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def prepare(base, output, readability=None, common_base=None, readability_manifest=None):
    base, output = Path(base).resolve(strict=True), Path(output).resolve()
    snapshot = json.loads((base / 'source-snapshot.json').read_text())
    for name, pin in snapshot['host_source_pins'].items():
        if sha(base / 'host-source' / name) != pin:
            raise ValueError('Selected host source changed: ' + name)
    if sha(base / 'build/entry_commandline.exe') != snapshot['executable_sha256']:
        raise ValueError('Selected native executable changed')
    if output.exists():
        raise ValueError('Use a fresh private native build directory')
    output.mkdir(parents=True)
    for directory in ('host-source', 'build-definition'):
        shutil.copytree(base / directory, output / directory)
    for name in ('optimized-mfc-objects.txt', 'build.ps1'):
        shutil.copy2(base / name, output / name)
    apply(output / 'host-source/main_v2.inc')
    readable_files = {}
    if readability is not None:
        if common_base is None or readability_manifest is None:
            raise ValueError('Readability merge requires its common base and compiled-file manifest')
        readable_files = json.loads(Path(readability_manifest).read_text())
        for name, entry in readable_files.items():
            # Formatting from an older host is safe only where both branches
            # still have the exact same pre-cleanup file. Never overwrite a
            # feature change with the formatting donor's older implementation.
            if (base / 'host-source' / name).read_bytes() != (Path(common_base) / 'host-source' / name).read_bytes():
                raise ValueError('Readability merge needs a manual feature conflict review: ' + name)
            donor = Path(readability) / 'host-source' / name
            if sha(donor) != entry['compiled_sha256']:
                raise ValueError('Readability donor changed after compilation: ' + name)
            shutil.copy2(donor, output / 'host-source' / name)
    changed = []
    for name, pin in snapshot['host_source_pins'].items():
        actual = sha(output / 'host-source' / name)
        if actual != pin:
            changed.append(name)
        snapshot['host_source_pins'][name] = actual
    if set(changed) != {'main_v2.inc', *readable_files}:
        raise ValueError('Unexpected installed provider source changes: ' + repr(changed))
    snapshot['previous_executable_sha256'] = snapshot.pop('executable_sha256')
    snapshot['base_source_snapshot'] = str(base / 'source-snapshot.json')
    snapshot['original_support_versions'] = [1]
    snapshot['installed_support_scope'] = 'Explicit user support paths; required bindings reject absent images. Source pins outside this boundary and any declared readability merge, plus all translated objects, are unchanged. Private build only.'
    if readable_files:
        snapshot['readability_merge'] = {
            'donor': str(Path(readability).resolve()),
            'common_base': str(Path(common_base).resolve()),
            'compiled_files_manifest_sha256': sha(readability_manifest),
            'merged_files': sorted(readable_files),
            'contract': 'All donor pre-cleanup files byte-identical to current feature branch; current feature changes outside these files retained.'}
    (output / 'source-snapshot.pending.json').write_text(json.dumps(snapshot, indent=2) + '\n')
    return len(snapshot['host_source_pins']), len((output / 'optimized-mfc-objects.txt').read_text().splitlines())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--readability', type=Path)
    parser.add_argument('--common-base', type=Path)
    parser.add_argument('--readability-manifest', type=Path)
    args = parser.parse_args()
    print(prepare(args.base, args.output, args.readability, args.common_base, args.readability_manifest))
