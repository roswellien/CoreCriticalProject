"""Identity of authored sources used by the isolated x87 control experiment."""
import hashlib
import json
from pathlib import Path
import sys


def identity(root):
    paths = []
    for folder in ('tools/x87-probe', 'tests/x87', 'runtime'):
        paths.extend(path for path in (root / folder).rglob('*')
                     if path.is_file() and path.suffix in ('.cpp', '.hpp', '.asm', '.s', '.py', '.ps1', '.txt')
                     and '__pycache__' not in path.parts)
    paths.extend(root / name for name in ('tools/lifting/host_adapter.py', 'docs/x87-control-contract.md'))
    files = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(paths)}
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'source_files': files, 'source_digest': digest}


if __name__ == '__main__':
    print(json.dumps(identity(Path(sys.argv[1]).resolve()), sort_keys=True))
