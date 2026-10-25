"""Refresh only the two authored exhaust sources in a compatible private host."""
from pathlib import Path
import argparse
import hashlib


def apply(host):
    repo = Path(__file__).resolve().parents[2]
    sources = {
        'missile_exhaust.hpp': repo / 'runtime/graphics/missile_exhaust.hpp',
        'missile_exhaust_stage.inc': Path(__file__).parent / 'native-overrides/missile_exhaust_stage.inc',
    }
    previous = {
        'missile_exhaust.hpp': 'ad06b83af72268cefbe1d74ecc9b396a47b380e2f49808fe7398d6173b6a2c00',
        'missile_exhaust_stage.inc': 'f801ffafdf20b3c54027375fb30b75f97c0c78177876a07cf0e8bb2d6912cbd6',
    }
    pending = {}
    for name, source in sources.items():
        before = (host / name).read_text(encoding='utf-8')
        after = source.read_text(encoding='utf-8')
        if before == after:
            continue
        if hashlib.sha256(before.encode()).hexdigest() != previous[name]:
            raise ValueError(f'{name}: unknown exhaust revision; merge before updating')
        pending[host / name] = after
    for path, source in pending.items():
        path.write_text(source, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host.resolve(strict=True))
