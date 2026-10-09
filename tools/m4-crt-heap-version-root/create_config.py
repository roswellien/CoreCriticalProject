"""Bind immutable current version-query proof and retain uncredited history."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT/'reports/m4-crt-heap-version-root'
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from paths import publish_bytes, workspace_path

FIXED = {
    'recovery': ('reports/m4-crt-heap-version-recovery/recovery-r1/report.json', '90565b98f9880fa49358c40d021967af700cc598c4f35da148469bad92372b5f'),
    'source_contract': ('reports/m4-crt-heap-version-review/source-r1/report.json', '38ecbbab533d662baa34a7079a864a2ecb0729abb4cdb3a8635ec51e83c44fa7'),
    'preparation': ('reports/m4-crt-heap-version/preparation-r2/report.json', '86a02f49d0aae999f5d766ebe207aaac520a5a5a290bdf1d564293f6e8d960ab'),
    'build': ('reports/m4-crt-heap-version/build-r3/build.json', '4ceb8fefa09bd36ba3a244295250b44ed333e36ba241e0a6a490996680bba25c'),
    'author_execution': ('reports/m4-crt-heap-version/execution-r1/report.json', '249e477b5c833748a76aaf64199c6822f0ca3aa6df00005a739f074814e5136c'),
    'root_model': ('reports/m4-crt-heap-version-root/observe-r2/report.json', '9afba8e3750f9c7b686b9666394d002aeac664399599b35985e0b604752a7b47'),
    'source_audit': ('reports/m4-crt-heap-version-review/audit-r2/report.json', 'e92d39ae9881a394b112b6fd9edb0b0214d42c078e0d872518857606378e1a20'),
    'draft_model_audit': ('reports/m4-crt-heap-version-root-audit/draft-r1/report.json', 'c749a38bcf0f5f9912c36829c1801553bd47c84dbaa42d042526c0ca527ef676'),
    'model_audit': ('reports/m4-crt-heap-version-root-audit/final-r1/report.json', '2e2febbb0ee7514a924dde9edee213f99a2348eea40896920f8381bfdfec9b13'),
    'compiled_build': ('reports/m4-crt-heap-version-review/compiled-r2/flat-build.json', 'f58b70bffe1330e98f113017a2c2e9b8fa0ad78dcc8645990ff9eb0fa5028c6c')}


def main(native_path, native_sha, hardware_path, hardware_sha, seal_path, seal_sha,
         failure_history_path, failure_history_sha, directory):
    out = workspace_path(directory, reports=True)
    if out.exists() or out.parent != BASE:
        raise ValueError('Fresh config output')
    def identity(path, digest=None):
        path = Path(path).absolute(); actual = sha_file(path)
        if digest is not None and actual != digest:
            raise ValueError('Fixed config input changed: '+str(path))
        return dict(path=str(path), sha256=actual)
    receipts = {name: identity(ROOT/path, digest) for name, (path, digest) in FIXED.items()}
    for name, path, digest in (
        ('compiled_native', native_path, native_sha),
        ('hardware_review', hardware_path, hardware_sha),
        ('independent_seal', seal_path, seal_sha)):
        receipts[name] = identity(ROOT/path, digest)
    pins = []
    for item in receipts.values():
        path = Path(item['path']).parent/'pins.json'
        if path.exists(): pins.append(identity(path))
    history = [identity(ROOT/'reports/m4-crt-heap-mode-root/root-acceptance-r1/report.json',
                        'fccb8400f1c4a5b8ee3824684d763d1a6391d9322ad28c0a5b173ef8bf483154'),
               identity(ROOT/failure_history_path, failure_history_sha),
               identity(ROOT/'reports/m4-crt-heap-version-host-review/diagnosis-r1/report.json',
                        '231ab4795a86ebda9c33eea33ae78a3aa55ed6bb0120488e6e800928879764f6')]
    # Identity-only history: never reopen broad ancestral dependency closures.
    for path in (
        'reports/m4-crt-heap-version/preparation-r1/report.json',
        'reports/m4-crt-heap-version/preparation-r1/pins.json',
        'reports/m4-crt-heap-version/build-r1/source-copy-failure.json',
        'reports/m4-crt-heap-version/build-r2/build.json',
        'reports/m4-crt-heap-version/build-r2/build-original.json',
        'reports/m4-crt-heap-version/build-r2/build-corrected-unfrozen.json',
        'reports/m4-crt-heap-version/build-r2/source-scope.json',
        'reports/m4-crt-heap-version-review/compiled-r1/flat-build.json',
        'reports/m4-crt-heap-version-review/history-r1/audit-r1-refusal.json',
        'reports/m4-crt-heap-version-review/history-r1/source-findings-before-stable-build.json',
        'reports/m4-crt-heap-version-root/draft-r1/report.json',
        'reports/m4-crt-heap-version-root/draft-stage-r1/stage.json',
        'reports/m4-crt-heap-mode/build-r1/sources/runtime/graphics/README.md'):
        history.append(identity(ROOT/path))
    for folder in ('observe-stage-r1',):
        for name in ('stage.json', 'stdout.bin', 'stderr.bin'):
            history.append(identity(BASE/folder/name))
    for name in ('stage.json', 'stdout.bin', 'stderr.bin'):
        history.append(identity(ROOT/'reports/m4-crt-heap-version-review/native-r1/run-O0'/name))
    documents = [identity(ROOT/path) for path in (
        'docs/m4-progress-heap-version.md', 'docs/m4-crt-heap-version-review.md',
        'tools/m4-crt-heap-version-root/README.md', 'tools/m4-crt-heap-version/README.md',
        'tools/m4-crt-heap-version-review/README.md', 'tools/m4-crt-heap-version-recovery/README.md',
        'tools/m4-crt-heap-version-root-audit/README.md', 'tools/m4-crt-heap-version-root-audit/README-final.md')]
    stage = BASE/'observe-stage-r2'
    fixed = identity(stage/'stage.json', 'cbdeac19fd62e215f3137ef3b8639d2186939255f527e90c2a4a254fcef48302')
    config = dict(receipts=receipts, pins=pins, history=history, documents=documents,
                  observer_stage=dict(path=str(stage), sha256=fixed['sha256']))
    out.mkdir(); path = out/'config.json'
    publish_bytes(path, (json.dumps(config, indent=2)+'\n').encode())
    print(json.dumps(dict(path=str(path), sha256=sha_file(path))))


if __name__ == '__main__': main(*sys.argv[1:])
