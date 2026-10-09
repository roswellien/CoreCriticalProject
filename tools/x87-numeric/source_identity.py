"""Authored source identities for the separate numerical x87 gate."""
import hashlib
import json
from pathlib import Path
import sys


def identity(root):
    paths = []
    extensions = {'.cpp', '.hpp', '.asm', '.s', '.py', '.ps1', '.txt', '.patch'}
    for folder in ('tools/x87-numeric', 'tests/x87-numeric', 'runtime'):
        paths.extend(p for p in (root / folder).rglob('*') if p.is_file()
                     and p.suffix in extensions and '__pycache__' not in p.parts)
    paths.extend(root / name for name in ('tools/lifting/host_adapter.py', 'docs/x87-numeric-contract.md'))
    files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'source_files': files, 'source_digest': digest}


if __name__ == '__main__':
    print(json.dumps(identity(Path(sys.argv[1]).resolve()), sort_keys=True))
