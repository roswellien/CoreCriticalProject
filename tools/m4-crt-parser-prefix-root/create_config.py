"""Fix the current named receipts and document digests for final admission."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from paths import publish_bytes

RECEIPTS = {
    'preparation': 'm4-crt-parser-prefix/preparation-r3/report.json',
    'build': 'm4-crt-parser-prefix/build-r2/build.json',
    'root_execution': 'm4-crt-parser-prefix/root-execution-r1/report.json',
    'root_model': 'm4-crt-parser-prefix/root-observer-r1/report.json',
    'source_audit': 'm4-crt-parser-prefix/source-contract-r2/report.json',
    'model_audit': 'm4-crt-parser-prefix/independent-root-model-audit-r1/report.json',
    'compiled_build': 'm4-crt-parser-prefix/independent-compiled-r5/build.json',
    'compiled_review': 'm4-crt-parser-prefix/independent-compiled-r5-review/report.json',
    'hardware_review': 'm4-crt-parser-prefix/independent-compiled-r5-hardware/report.json',
    'bundle_preparation': 'm4-review-bundles/preparation-r1/report.json',
    'bundle_review': 'm4-review-bundles/review-r1/report.json',
    'bundle_root_check': 'm4-review-bundles/root-check-r1/report.json'}
PINS = ['m4-crt-parser-prefix/preparation-r3/pins.json',
        'm4-crt-parser-prefix/source-contract-r2/pins.json',
        'm4-crt-parser-prefix/independent-root-model-audit-r1/pins.json',
        'm4-review-bundles/review-r1/pins.json',
        'm4-review-bundles/root-check-r1/pins.json']
HISTORY = ['m4-crt-commandline-carry/root-acceptance-r1/report.json',
           'm4-crt-parser-prefix/preparation-r2/report.json',
           'm4-crt-parser-prefix/preparation-r2/pins.json',
           'm4-crt-parser-prefix/build-r1/build.json',
           'm4-crt-parser-prefix/execution-r1/report.json',
           'm4-crt-parser-prefix/source-contract-r1/report.json',
           'm4-crt-parser-prefix/root-model-preview-r1/report.json',
           'm4-crt-parser-prefix/independent-compiled-r1/flat-build.json',
           'm4-crt-parser-prefix/independent-compiled-r2/flat-build.json',
           'm4-crt-parser-prefix/independent-compiled-r3/flat-build.json',
           'm4-crt-parser-prefix/independent-compiled-r4/build.json']
DOCS = ['docs/m4-crt-parser-prefix-review.md', 'docs/m4-progress-parser-prefix.md',
        'docs/m4-review-bundles-results.md', 'tools/m4-crt-parser-prefix-root/README.md',
        'tools/m4-crt-parser-prefix-review/README.md', 'tools/m4-review-bundles/README.md']


def identity(path):
    path = Path(path).absolute()
    return dict(path=str(path), sha256=sha_file(path))


def main():
    output = ROOT/'reports/m4-crt-parser-prefix/admission.json'
    if output.exists():
        raise FileExistsError(output)
    config = dict(receipts={n:identity(ROOT/'reports'/p) for n,p in RECEIPTS.items()},
                  pins=[identity(ROOT/'reports'/p) for p in PINS],
                  history=[identity(ROOT/'reports'/p) for p in HISTORY],
                  documents=[identity(ROOT/p) for p in DOCS],
                  observer_stage=dict(path=str(ROOT/'reports/m4-crt-parser-prefix/root-observer-stage-r1'),
                    sha256='a8b78cdad19c3ab61debcf4971f9439b8cddd5adc6e411bb197a1fedc111b8d6'))
    publish_bytes(output, (json.dumps(config, indent=2)+'\n').encode())
    print(json.dumps(identity(output)))


if __name__ == '__main__':
    main()
