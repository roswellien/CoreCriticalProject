"""Bind finished current locale receipts to one fresh admission request."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from paths import publish_bytes, workspace_path

RECEIPTS = {
    'recovery': ('reports/m4-crt-locale-default-recovery/recovery-r2/report.json', '500e515b769e674d63503bf8572212221c7af8ae9519b712d4ee712c512c37c3'),
    'source_contract': ('reports/m4-crt-locale-default-contract/review/source-r2/report.json', '1098249ae0c9a4403de5cd50749b6e45e2d07bd9baae07fa9f892671760b92c8'),
    'preparation': ('reports/m4-crt-locale-default/preparation-r4/report.json', '02fa0f0f22723b966e9dbe65372ecba8ea1dc5af1923f76590bf81321156d3f4'),
    'build': ('reports/m4-crt-locale-default/build-r2/build.json', 'b1cdebd498dbaa5aaa42e60bc66b2a53665346df1852ad63d1313d60d6e1dcca'),
    'author_execution': ('reports/m4-crt-locale-default/execution-r2/report.json', '49ef0521fd43eda19b36085865ce3428ae9928d2ef82c8f6399e689eda7426ee'),
    'root_model': ('reports/m4-crt-locale-default-root/observe-r3/report.json', '646bd96a0578688a569b3b80f3c1a702a15f0f93dfab05991d43b6c8da9666e3'),
    'source_audit': ('reports/m4-crt-locale-default-contract/review/audit-r1/report.json', 'c3e38a3e9373c986ef2efe32b2f166f681db720cce70dd9c6d0a9eaf036b0fef'),
    'compiled_build': ('reports/m4-crt-locale-default-contract/review/compiled-r1/flat-build.json', '523fc376b984e9b7d21b22e7953831b19569b2f737afb0860789fe5ccda3a440'),
    'compiled_native': ('reports/m4-crt-locale-default-contract/review/native-r1/report.json', '488989b1598b8b11a9db014e6013006f9d11d0d70f1ccff0c547b842dd646af2'),
    'hardware_review': ('reports/m4-crt-locale-default-contract/review/check-r3/report.json', '7fadc54a04f85c840773557ab265962a0aad24123eb0c92684f73de347a9c56d'),
}


def main(audit_path, audit_sha, directory):
    out = workspace_path(directory, reports=True)
    if out.exists() or out.parent != ROOT/'reports/m4-crt-locale-default-root':
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
        'reports/m4-crt-locale-default-recovery/recovery-r2/pins.json',
        'reports/m4-crt-locale-default-contract/review/source-r2/pins.json',
        'reports/m4-crt-locale-default/preparation-r4/pins.json',
        'reports/m4-crt-locale-default-root/observe-r3/pins.json',
        'reports/m4-crt-locale-default-contract/review/audit-r1/pins.json',
        'reports/m4-crt-locale-default-contract/review/check-r3/pins.json')]
    pins.append(identity(Path(audit_path).parent/'pins.json'))
    history = [identity(ROOT/path, digest) for path,digest in (
        ('reports/m4-crt-parser-prefix/root-acceptance-r1/report.json', 'b78c296b69dc15abf6b88d4901c8742875ca25de417497233e0687ee2704b964'),
        ('reports/m4-crt-locale-allocation-recovery/recovery-r2/report.json', '883ffaa436cf2376994fcbeb9807bb547fc3df54e3e220a87cf55cfa8c46388d'),
        ('reports/m4-crt-locale-default/failed-preparations-r1/report.json', '4ff7676e260c7be7a93f52614c6392418da2a17fb4b420cb5868eb01603ee8d9'))]
    for path in ('reports/m4-crt-locale-default/execution-r1/report.json',
                 'reports/m4-crt-locale-default-root/observe-r1/report.json',
                 'reports/m4-crt-locale-default-root/observe-r2/report.json'):
        history.append(identity(ROOT/path))
    documents = [identity(ROOT/path) for path in (
        'docs/m4-crt-locale-default-review.md', 'docs/m4-progress-locale-default.md',
        'tools/m4-crt-locale-default/README.md', 'tools/m4-crt-locale-default-root/README.md',
        'tools/m4-crt-locale-default-contract/review/README.md',
        'tools/m4-crt-locale-allocation-recovery/README.md',
        'tools/m4-crt-locale-default-root-audit/README.md')]
    stage = ROOT/'reports/m4-crt-locale-default-root/observe-stage-r3'
    config = dict(receipts=receipts, pins=pins, history=history, documents=documents,
                  observer_stage=dict(path=str(stage), sha256=sha_file(stage/'stage.json')))
    out.mkdir()
    path = out/'config.json'
    publish_bytes(path, (json.dumps(config, indent=2)+'\n').encode())
    print(json.dumps(dict(path=str(path), sha256=sha_file(path))))


if __name__ == '__main__':
    main(*sys.argv[1:])
