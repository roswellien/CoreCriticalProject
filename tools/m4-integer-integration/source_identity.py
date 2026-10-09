"""Bind freshly compiled adapters to the complete frozen component sources."""
import hashlib,json,sys
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(root):
    root=root.resolve();chain=json.loads((root/'reports/m4-initializer-chain/runtime-preflight-3/build.json').read_text(encoding='utf-8-sig'));batch=json.loads((root/'reports/m4-integer-startup/batch-r2/build.json').read_text(encoding='utf-8-sig'));files={}
    for name,digest in chain['source_files'].items():
        path=Path(name)
        # The new shared host deliberately recompiles against r7, never
        # reinterprets or links the historical r4 C++ adapter executable.
        if path.name in ('runtime.hpp','runtime.cpp') and path.parent==root/'tools/m4-runtime':continue
        if sha(path)!=digest:raise ValueError('Frozen chain source changed: '+name)
        files[path.relative_to(root).as_posix()]=digest
    for name,digest in batch['source_files'].items():
        path=Path(name)
        if sha(path)!=digest:raise ValueError('Frozen batch/r7 source changed: '+name)
        files[path.relative_to(root).as_posix()]=digest
    for path in (root/'tools/m4-integer-integration').rglob('*'):
        if path.is_file() and path.suffix in {'.cpp','.hpp','.txt','.py','.ps1'} and '__pycache__' not in path.parts:files[path.relative_to(root).as_posix()]=sha(path)
    doc=root/'docs/m4-integer-integration-contract.md';files[doc.relative_to(root).as_posix()]=sha(doc)
    files=dict(sorted(files.items()));digest=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'source_digest':digest,'source_files':files,'absolute_source_files':{str(root/name):d for name,d in files.items()}}
if __name__=='__main__':print(json.dumps(identity(Path(sys.argv[1])),sort_keys=True))
