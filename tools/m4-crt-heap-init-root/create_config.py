"""Bind finished heap prefix evidence into a fresh fixed admission request."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from paths import publish_bytes, workspace_path

RECEIPTS = {
    'recovery': ('reports/m4-crt-heap-init-recovery/recovery-r1/report.json', '4706dd8c297247de56da28566f4c3e2b4891c68cc8db8deb28dc604608b5498b'),
    'source_contract': ('reports/m4-crt-heap-init-review/source-r3/report.json', '343a2d0ac63905943acf26be08a0fc5144d5ccb2e7ab52ded2aba4c560acbb44'),
    'preparation': ('reports/m4-crt-heap-init/preparation-r2/report.json', 'ef86361916eece8b4bfba1893341a403fcd3a6a02af272fde907ccb2bd2667fc'),
    'build': ('reports/m4-crt-heap-init/build-r1/build.json', 'b319a82d8c9d61d4db269de520684b1b7e9caa6e7636a125bdaa63cbf8d15104'),
    'author_execution': ('reports/m4-crt-heap-init/execution-r1/report.json', '96ea6a3d870d6aebf48abda4a07a08eb7ae597551030951b3b3e6732b6b5208c'),
    'root_model': ('reports/m4-crt-heap-init-root/observe-r2/report.json', '13ceb1f01ab04c490257bd34066f423ebe312d3180478184a6630d4a79194962'),
    'source_audit': ('reports/m4-crt-heap-init-review/audit-r1/report.json', 'a0c6d4a57ec99b62984b9a2fa312e164fc989f4a20f0398bf4e0dde773d09fc2'),
    'compiled_build': ('reports/m4-crt-heap-init-review/compiled-r3/flat-build.json', 'f98e36ac032344f29ad64f562b68aca3c1179385f9dfe88147071137b107e0ce'),
    'compiled_native': ('reports/m4-crt-heap-init-review/native-r1/report.json', 'b89650f3e66bdcc3eae98de4904a7b60b528c422210e322f4b8176f027363638'),
    'hardware_review': ('reports/m4-crt-heap-init-review/check-r1/report.json', '6dd0fb0c68c61726d3d73500ed13c1e0abb2678ad034b687983bf09d33301cf6'),
}


def main(audit_path, audit_sha, directory):
    out = workspace_path(directory, reports=True)
    if out.exists() or out.parent != ROOT/'reports/m4-crt-heap-init-root':
        raise ValueError('Fresh immediate config output')

    def identity(path, expected=None):
        path = Path(path).absolute()
        digest = sha_file(path)
        if expected is not None and digest != expected:
            raise ValueError('Fixed config input changed: '+str(path))
        return dict(path=str(path), sha256=digest)

    receipts = {name:identity(ROOT/path, digest) for name,(path,digest) in RECEIPTS.items()}
    receipts['model_audit'] = identity(audit_path, audit_sha)
    pins = [identity(ROOT/path) for path in (
        'reports/m4-crt-heap-init-recovery/recovery-r1/pins.json',
        'reports/m4-crt-heap-init-review/source-r3/pins.json',
        'reports/m4-crt-heap-init/preparation-r2/pins.json',
        'reports/m4-crt-heap-init-root/observe-r2/pins.json',
        'reports/m4-crt-heap-init-review/audit-r1/pins.json',
        'reports/m4-crt-heap-init-review/check-r1/pins.json')]
    pins.append(identity(Path(audit_path).parent/'pins.json'))
    history = [identity(ROOT/path, digest) for path,digest in (
        ('reports/m4-crt-locale-default-root/root-acceptance-r2/report.json', '211a866900b2274aad08c5ac710e0b69c93c34e279a7bfe3745b837541edf65e'),
        ('reports/m4-crt-locale-allocation-recovery/recovery-r2/report.json', '883ffaa436cf2376994fcbeb9807bb547fc3df54e3e220a87cf55cfa8c46388d'),
        ('reports/m4-crt-heap-init-review/compiled-r1/flat-build.json', 'd69140d517877e245efd6c37642e0d07090c20eec91635c733ec97cb5ea9e3f6'),
        ('reports/m4-crt-heap-init-review/compiled-r2/flat-build.json', 'e52355f202df7148a401fab2858f66e4fb17025c67e8e0452d85532d37785221'),
        ('reports/m4-crt-heap-init/preparation-r1/composition.cpp', 'd950b9196878edac175510142e05382a5ab5107ff303c7da2623789efbf31d11'),
        ('reports/m4-crt-heap-init-review/source-r1/report.json', 'df1e4026cb4eb4f4be153db16a69342617a6253afb9b069a1cacfdc3f9406749'),
        ('reports/m4-crt-heap-init-review/source-r2/report.json', 'df1e4026cb4eb4f4be153db16a69342617a6253afb9b069a1cacfdc3f9406749'),
        ('reports/m4-crt-heap-init-root-audit/draft-r2/report.json', '4ad58ea3b7da5a33ebdb76b5023fe983a64ea26822fc6ac5b0e89fb9979e9c0b'))]
    for path in ('reports/m4-crt-heap-init-root/observe-r1/report.json',
                 'reports/m4-crt-heap-init-root/observe-stage-r1/stage.json'):
        history.append(identity(ROOT/path))
    documents = [identity(ROOT/path) for path in (
        'docs/m4-crt-heap-init-review.md', 'docs/m4-progress-heap-init.md',
        'tools/m4-crt-heap-init/README.md', 'tools/m4-crt-heap-init-root/README.md',
        'tools/m4-crt-heap-init-review/README.md', 'tools/m4-crt-heap-init-recovery/README.md',
        'tools/m4-crt-heap-init-root-audit/README.md')]
    stage = ROOT/'reports/m4-crt-heap-init-root/observe-stage-r2'
    config = dict(receipts=receipts, pins=pins, history=history, documents=documents,
                  observer_stage=dict(path=str(stage), sha256=sha_file(stage/'stage.json')))
    out.mkdir()
    path = out/'config.json'
    publish_bytes(path, (json.dumps(config, indent=2)+'\n').encode())
    print(json.dumps(dict(path=str(path), sha256=sha_file(path))))


if __name__ == '__main__':
    main(*sys.argv[1:])
