"""Bind fresh header-dependent compilation to r9 and unchanged guest adapters."""
import hashlib,json,sys
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(root):
    root=root.resolve();files={}
    parents=(root/'reports/m4-initializer-chain/runtime-preflight-3/build.json',root/'reports/m4-integer-startup/batch-r2/build.json')
    for record in parents:
        build=json.loads(record.read_text(encoding='utf-8-sig'))
        for name,digest in build['source_files'].items():
            path=Path(name)
            # Both historical component gates used an older Runtime. Only
            # these two directly compiled Runtime files are replaced by r9.
            if path.parent==root/'tools/m4-runtime' and path.name in ('runtime.hpp','runtime.cpp'):continue
            if sha(path)!=digest:raise ValueError('Frozen guest component source changed: '+name)
            files[path.relative_to(root).as_posix()]=digest
    runtime_path=root/'reports/m4-runtime/context-r9/build.json'
    if sha(runtime_path)!='12bd0f42d7fba2cc8b9f7cc4d6b9db795c98e196ae305ac23dbd7fe38b21abf5':raise ValueError('r9 Runtime build identity changed')
    runtime=json.loads(runtime_path.read_text(encoding='utf-8-sig'))
    for name,digest in runtime['source_files'].items():
        path=Path(name)
        if sha(path)!=digest:raise ValueError('Accepted r9 Runtime source changed: '+name)
        files[path.relative_to(root).as_posix()]=digest
    for path in Path(__file__).parent.rglob('*'):
        if path.is_file() and path.suffix in {'.cpp','.hpp','.txt','.py','.ps1'} and '__pycache__' not in path.parts:files[path.relative_to(root).as_posix()]=sha(path)
    doc=root/'docs/m4-integer-integration-r9-contract.md';files[doc.relative_to(root).as_posix()]=sha(doc)
    files=dict(sorted(files.items()));digest=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'source_digest':digest,'source_files':files,'absolute_source_files':{str(root/name):d for name,d in files.items()}}
if __name__=='__main__':print(json.dumps(identity(Path(sys.argv[1])),sort_keys=True))
