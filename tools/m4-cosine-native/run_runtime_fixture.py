"""Run six genuine dispatcher cases and ten real corruption controls per level."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'reports/m4-cosine-native'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(build_path, digest, name):
    out = AREA / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins, observations = {}, []
    passed = False

    def pin(path, expected=None):
        path = Path(path).resolve()
        value = sha(path)
        assert expected is None or expected == value, path
        pins[str(path)] = value
        return path

    try:
        build = json.loads(pin(build_path, digest).read_bytes())
        assert build['passed']
        prep = json.loads(pin(build['preparation'], build['preparation_sha256']).read_bytes())
        for path, expected in build['sources'].items():
            pin(path, expected)
        game = pin(ROOT / 'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
        cp = pin(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCP50.DLL', '91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')
        crt = pin(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL', '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
        mfc = pin(ROOT / 'local/mw3-staged/Shared_DLLs/MFC42.DLL', '5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8')
        pin(__file__)
        for level in ('O0', 'O2'):
            worker = pin(build['workers'][level]['path'], build['workers'][level]['sha256'])
            cases = [(i, cw, top, 0) for i, (cw, top) in enumerate(prep['cases'])]
            cases += [(6 + control - 1, 0x37f, 7, control) for control in range(1, 11)]
            for sequence, cw, top, control in cases:
                destination = out / level / f'case-{sequence}'
                destination.parent.mkdir(exist_ok=True)
                started = time.perf_counter()
                arguments = list(map(str, (worker, game, cp, crt, mfc, destination, cw, top, control)))
                run = subprocess.run(arguments, cwd=ROOT, capture_output=True, timeout=90, creationflags=0x08000000)
                prefix = out / f'{level}-case-{sequence}'
                prefix.with_suffix('.stdout').write_bytes(run.stdout)
                prefix.with_suffix('.stderr').write_bytes(run.stderr)
                transport = destination / 'transport.json'
                if transport.is_file():
                    manifest = json.loads(pin(transport).read_bytes())
                    for part in manifest['parts']:
                        pin(destination / part['bundle'], part['sha256'])
                observation = dict(level=level, sequence=sequence, CW=cw, TOP=top, control=control,
                                   control_name=prep['controls'][control - 1] if control else None,
                                   arguments=arguments, exit_code=run.returncode, seconds=time.perf_counter() - started,
                                   transport=str(transport) if transport.is_file() else None,
                                   transport_sha256=sha(transport) if transport.is_file() else None)
                observations.append(observation)
                print(json.dumps(dict(level=level, sequence=sequence, control=control, exit_code=run.returncode,
                                      stderr=run.stderr.decode(errors='replace')[:500])), flush=True)
                assert run.returncode == 0 and transport.is_file(), observation
        for path, expected in pins.items():
            assert sha(path) == expected, path
        passed = len(observations) == 32
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        report = dict(passed=passed, scope='Actual Runtime dispatcher compound execution and bounded causal probes; full source/retry analysis separate',
                      build_path=str(build_path), build_sha256=digest, observations=observations,
                      native_levels=2, intended_positive_cases=12, intended_causal_controls=20,
                      source_after_seed=False, initializer_credit=0, files=pins)
        path = out / 'report.json'
        path.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=sha(path), actual_probes=len(observations))))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3])
