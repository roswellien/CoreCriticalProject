"""Source/dependency identities for the separate complete real M3 function."""
import hashlib
import json
from pathlib import Path
import sys


def identity(root):
    root = root.resolve()
    extensions = {'.cpp', '.hpp', '.asm', '.s', '.py', '.ps1', '.txt', '.ll'}
    paths = set()
    for folder in ('tools/m3-slice', 'tests/m3-slice', 'runtime'):
        paths.update(path for path in (root / folder).rglob('*') if path.is_file() and
                     path.suffix in extensions and '__pycache__' not in path.parts)
    # Bind the complete transitive runtime header trees, not only State.h.
    for folder in ('local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/Runtime',
                   'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime'):
        paths.update(path for path in (root/folder).rglob('*') if path.is_file())
    for name in ('tools/lifting/host_adapter.py', 'tools/analysis/pe.py',
                 'docs/m3-slice-contract.md', 'docs/m2-next-slice-context.md',
                 'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h',
                 'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/Runtime/State.h',
                 'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/Runtime/Types.h',
                 'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/Runtime/Intrinsics.h',
                 'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp'):
        path = root / name
        if not path.is_file():
            raise ValueError('Missing required source/context dependency: ' + name)
        paths.add(path)
    files = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(paths)}
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'source_files': files, 'source_digest': digest,
            'absolute_source_files': {str((root / name).resolve()): value for name, value in files.items()}}


if __name__ == '__main__':
    root = Path(sys.argv[1]) if len(sys.argv) == 2 else Path(__file__).resolve().parents[2]
    print(json.dumps(identity(root), sort_keys=True))
