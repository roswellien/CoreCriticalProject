"""Prove presentation diagnostics cannot be accepted as scene replay input."""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('diagnostic', type=Path)
    parser.add_argument('accepted_scene', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('capture_verifier', Path(__file__).with_name('verify_capture.py'))
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    accepted = verifier.verify(args.accepted_scene)
    rows = [json.loads(x) for x in (args.diagnostic / 'capture.jsonl').read_text().splitlines()]
    rejected = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for name, header in (
            ('actual_diagnostic', rows[0]),
            ('forged_scene_scope_with_incomplete_coverage', dict(rows[0], scope='one_BeginScene_EndScene_interval')),
            ('presentation_scope_with_false_completeness_claim', dict(rows[0], command_coverage_complete=True)),
        ):
            (directory / 'capture.jsonl').write_text('\n'.join(json.dumps(r) for r in [header, *rows[1:]]))
            try:
                verifier.verify(directory)
            except ValueError as error:
                if 'diagnostic only' not in str(error):
                    raise ValueError(f'{name} rejected for an unrelated reason: {error}') from error
                rejected.append(name)
            else:
                raise ValueError(f'{name} incorrectly accepted')
    report = {'accepted_prior_scene_draws': accepted['draws'], 'rejected_controls': rejected,
              'scope': 'Scene acceptance gate only; no live gameplay or full-frame replay claim'}
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
