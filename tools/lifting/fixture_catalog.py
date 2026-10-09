"""Reviewed authored machine-code identities; never accepts arbitrary guest code."""
import argparse
from pathlib import Path

FIXTURES = {
    'add': bytes.fromhex('8b44240403442408c3'),
    'branch': bytes.fromhex('8b4424043b4424087d078b442408b111c366b93322c3'),
    'memory': bytes.fromhex('8b4424048b4c2408030889088b500489500889c8c20800'),
    'shift': bytes.fromhex('8b442404c1e0052b442408c3'),
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', choices=FIXTURES, required=True)
    parser.add_argument('--check-file', type=Path, required=True)
    args = parser.parse_args()
    if args.check_file.read_bytes() != FIXTURES[args.name]:
        raise SystemExit('Assembled bytes differ from reviewed fixture identity')
    print(FIXTURES[args.name].hex())
