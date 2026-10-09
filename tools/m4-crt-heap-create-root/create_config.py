"""Bind finished real heap evidence into a fresh, externally hashed admission."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from paths import publish_bytes, workspace_path

RECEIPTS = {
    'recovery': ('reports/m4-crt-heap-create-recovery/recovery-r1/report.json', '16e6d7f70c7b23747de90182e34f73471112108524d161b243db5603626a9f7c'),
    'source_contract': ('reports/m4-crt-heap-create-review/source-r1/report.json', '6a4140b0cfc704153b42b872e1907ead032c9ee9cb0e986bc0957972be9247b8'),
    'preparation': ('reports/m4-crt-heap-create/preparation-r2/report.json', 'b85a555d6d14ef97afd5547aef0b6bba96aae1597e72aed40e1d41a33562d1e9'),
    'build': ('reports/m4-crt-heap-create/build-r1/build.json', '28b96699f22ade5daaaab35fa15b63d16debbd3995eafd8e4e790bb57de7cd9e'),
    'author_execution': ('reports/m4-crt-heap-create/execution-r1/report.json', 'bbff62b849ca9c92368e83c781918cab434df2ef17a8ee6534d1fdcf53662a02'),
    'root_model': ('reports/m4-crt-heap-create-root/observe-r3/report.json', 'b0f9d688733d6c42a172dd7e9a8bce58d88033eca33c08e5724618511ee4b6c5'),
    'source_audit': ('reports/m4-crt-heap-create-review/audit-r1/report.json', '00e42495fd39f4257fc99e90da8d04e68c8bcfba1b185ca66db9be400891b912'),
    'compiled_build': ('reports/m4-crt-heap-create-review/compiled-r3/flat-build.json', 'adbdf7de9247e375d3fd424ed14b9f19c2659ceaf053a092d2adcf15278c6e2f'),
    'compiled_native': ('reports/m4-crt-heap-create-review/native-r1/report.json', '8ec6a42d377b0f823a3a76b92d588da1c7e86ca75a966c7b37f7860f1aef4294'),
    'independent_seal': ('reports/m4-crt-heap-create-review/sealed-r1/report.json', 'b908aabab06605eeb78f78df019b84d05b5883cdf9111249fa8352788f443b35'),
}


def main(audit_path, audit_sha, hardware_path, hardware_sha, error_path, error_sha, directory):
    out = workspace_path(directory, reports=True)
    if out.exists() or out.parent != ROOT/'reports/m4-crt-heap-create-root':
        raise ValueError('Fresh immediate config output')

    def identity(path, expected=None):
        path = Path(path).absolute()
        digest = sha_file(path)
        if expected is not None and digest != expected:
            raise ValueError('Fixed config input changed: '+str(path))
        return dict(path=str(path), sha256=digest)

    receipts = {name:identity(ROOT/path, digest) for name,(path,digest) in RECEIPTS.items()}
    receipts['model_audit'] = identity(audit_path, audit_sha)
    receipts['hardware_review'] = identity(hardware_path, hardware_sha)
    receipts['caller_error_review'] = identity(error_path, error_sha)
    pins = [identity(ROOT/path, digest) for path, digest in (
        ('reports/m4-crt-heap-create-recovery/recovery-r1/pins.json', '5a40f651874c644aa9e6eec9e30f094c9a6bac37e65e03b57ff518002003734f'),
        ('reports/m4-crt-heap-create-review/source-r1/pins.json', '2d30bdfb5ebe1750a5e155b999a2665ce5df380aee1393e8ad2d50794ec15adc'),
        ('reports/m4-crt-heap-create/preparation-r2/pins.json', 'da6895282c9a30dedaf01dd84dc83b059f4a59d20f77e5f1c18a3e3c1b54017a'),
        ('reports/m4-crt-heap-create-review/audit-r1/pins.json', '72e12a2f2271a986d45fdc318acc35a13c5c064420d11cd81aa78316673cc58e'),
        ('reports/m4-crt-heap-create-review/sealed-r1/pins.json', 'f8e8923301ee2102222d56ae8826f9c5da16238eebac5493210b3fda77a07f46'))]
    for report in (audit_path, hardware_path):
        pins.append(identity(Path(report).parent/'pins.json'))
    pins.append(identity(ROOT/'reports/m4-crt-heap-create-root/observe-r3/pins.json'))
    history = [identity(ROOT/'reports/m4-crt-heap-init-root/root-acceptance-r1/report.json',
                        'a9a549d0acf1e8cd3a0015b4b7cdd2d61876ded33e0c69610c37bf9bc60b001d')]
    # Retain all preparation, compile and model-check revisions as receipt
    # anchors. Their superseded physical dependency maps are not expanded.
    historical = (
        'reports/m4-crt-heap-create/preparation-r1/report.json',
        'reports/m4-crt-heap-create/preparation-r1/pins.json',
        'reports/m4-crt-heap-create-review/compiled-r1/flat-build.json',
        'reports/m4-crt-heap-create-review/compiled-r2/flat-build.json',
        'reports/m4-crt-heap-create-root/draft-stage-r1/stage.json',
        'reports/m4-crt-heap-create-root/draft-stage-r2/stage.json',
        'reports/m4-crt-heap-create-root/draft-stage-r3/stage.json',
        'reports/m4-crt-heap-create-root/draft-stage-r4/stage.json',
        'reports/m4-crt-heap-create-root/draft-r3/report.json',
        'reports/m4-crt-heap-create-root/draft-r4/report.json',
        'reports/m4-crt-heap-create-root-audit/draft-r1/report.json',
        'reports/m4-crt-heap-create-root-audit/refusal-r1/report.json',
        'reports/m4-crt-heap-create-root/observe-stage-r1/stage.json',
        'reports/m4-crt-heap-create-root/observe-stage-r2/stage.json',
        'reports/m4-crt-heap-create-root/observe-r2/report.json')
    history.extend(identity(ROOT/path) for path in historical)
    seal = json.loads((ROOT/'reports/m4-crt-heap-create-review/sealed-r1/report.json').read_bytes())
    for item in seal['checker_refusals']:
        history.append(identity(item['path'],item['sha256']))
    for folder in sorted((ROOT/'reports/m4-crt-heap-create-review').glob('check-*')):
        path = folder/'report.json'
        if path.exists() and path != Path(hardware_path).absolute():
            history.append(identity(path))
    documents = [identity(ROOT/path) for path in (
        'docs/m4-crt-heap-create-review.md', 'docs/m4-progress-heap-create.md',
        'tools/m4-crt-heap-create/README.md', 'tools/m4-crt-heap-create-root/README.md',
        'tools/m4-crt-heap-create-review/README.md', 'tools/m4-crt-heap-create-recovery/README.md',
        'tools/m4-crt-heap-create-root-audit/README.md',
        'tools/m4-crt-heap-create-root-audit/README-final.md')]
    stage = ROOT/'reports/m4-crt-heap-create-root/observe-stage-r3'
    config = dict(receipts=receipts, pins=pins, history=history, documents=documents,
                  observer_stage=dict(path=str(stage), sha256=sha_file(stage/'stage.json')))
    if config['observer_stage']['sha256'] != '336b917fba26fca4ef13f132755faaa20f4113610595ceafabbee5ad3fd3ca74':
        raise ValueError('Fixed final observer stage')
    out.mkdir()
    path = out/'config.json'
    publish_bytes(path, (json.dumps(config, indent=2)+'\n').encode())
    print(json.dumps(dict(path=str(path), sha256=sha_file(path))))


if __name__ == '__main__':
    main(*sys.argv[1:])
