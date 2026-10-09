"""Authored source identities for the separate x87 live-stack/state gate."""
import hashlib
import json
from pathlib import Path
import sys


def identity(root):
    paths = []
    extensions = {'.cpp', '.hpp', '.asm', '.s', '.py', '.ps1', '.txt', '.patch', '.ll'}
    for folder in ('tools/x87-state', 'tests/x87-state', 'runtime'):
        paths.extend(p for p in (root / folder).rglob('*') if p.is_file()
                     and p.suffix in extensions and '__pycache__' not in p.parts)
    paths.extend(root / name for name in ('tools/lifting/host_adapter.py',
                 'tools/x87-range/compare_range.py', 'tools/x87-store-c1/compare_store_c1.py', 'docs/x87-state-contract.md'))
    files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'source_files': files, 'source_digest': digest}


if __name__ == '__main__':
    print(json.dumps(identity(Path(sys.argv[1]).resolve()), sort_keys=True))
