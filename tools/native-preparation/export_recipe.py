"""Export source-free translation recipes from the selected private object lineage.

Development-only export: reports are read here, never by the player-side producer.
The recipe contains addresses, lengths, hashes and symbol/optimizer metadata, not
source bytes, LLVM IR, objects, captures or memory contents.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class Reader:
    """Consume one report component at a time rather than loading its layout ledger."""
    def __init__(self, file):
        self.file, self.buffer = file, ''
        self.decoder = json.JSONDecoder()

    def fill(self):
        text = self.file.read(65536)
        if not text:
            raise ValueError('Truncated translation report')
        self.buffer += text

    def peek(self):
        while True:
            self.buffer = self.buffer.lstrip()
            if self.buffer:
                return self.buffer[0]
            self.fill()

    def take(self, char):
        if self.peek() != char:
            raise ValueError('Unexpected translation report syntax')
        self.buffer = self.buffer[1:]

    def value(self):
        self.peek()
        while True:
            try:
                value, end = self.decoder.raw_decode(self.buffer)
                # Numbers ending at a chunk boundary need one more chunk.
                if end == len(self.buffer) and isinstance(value, (int, float)):
                    self.fill()
                    continue
                self.buffer = self.buffer[end:]
                return value
            except json.JSONDecodeError:
                if len(self.buffer) > 16 * 1024**2:
                    raise ValueError('Excessive translation report component')
                self.fill()


def components(path, section='components'):
    with path.open(encoding='utf-8-sig') as stream:
        reader = Reader(stream)
        reader.take('{')
        root_keys = set()
        while reader.peek() != '}':
            key = reader.value()
            if key in root_keys:
                raise ValueError('Duplicate report field')
            root_keys.add(key)
            reader.take(':')
            if key == section:
                reader.take('{')
                seen = set()
                while reader.peek() != '}':
                    name = reader.value()
                    if name in seen:
                        raise ValueError('Duplicate component')
                    seen.add(name)
                    reader.take(':')
                    yield name, reader.value()
                    if reader.peek() == ',':
                        reader.take(',')
                        if reader.peek() == '}':
                            raise ValueError('Trailing component separator')
                    elif reader.peek() != '}':
                        raise ValueError('Missing component separator')
                reader.take('}')
            else:
                reader.value()
            if reader.peek() == ',':
                reader.take(',')
                if reader.peek() == '}':
                    raise ValueError('Trailing report separator')
            elif reader.peek() != '}':
                raise ValueError('Missing report field separator')
        reader.take('}')
        if reader.buffer.strip() or stream.read().strip():
            raise ValueError('Trailing translation report content')


def image_for(start):
    for name, lo, hi in [('game', 0x400000, 0x600000), ('mfc42', 0x5f400000, 0x5f600000),
                         ('msvcrt', 0x78000000, 0x780c0000), ('msvcp50', 0x780c0000, 0x78200000),
                         ('ir50', 0x11000000, 0x11100000), ('mech3msg', 0x10000000, 0x10100000)]:
        if lo <= start < hi:
            return name
    raise ValueError('Unclassified original-image address: ' + hex(start))


def export(root, objects, output):
    if output.exists():
        raise ValueError('Use a fresh recipe file')
    selected = [Path(line) for line in objects.read_text().splitlines() if line.strip()]
    groups = defaultdict(dict)
    optimized = {}
    for obj in selected:
        # Optimized directories preserve the original lift partition name.
        if obj.parent.parent.name in ('merge-r7', 'merge-r8-codec'):
            source_dir = root / 'reports/m4-crt-attach' / obj.parent.name
            optimization = obj.parent.parent.name
        else:
            source_dir, optimization = obj.parent, 'plain-O2'
        name = obj.name.removesuffix('-O2.obj')
        if not re.fullmatch(r'[a-zA-Z0-9_]+', name) or name == obj.name:
            raise ValueError('Unknown selected object name')
        groups[source_dir][name] = (obj, optimization)
        if name in optimized:
            raise ValueError('Duplicate selected body name: ' + name)
        optimized[name] = None
    recipes, report_pins = {}, {}
    for directory, wanted in groups.items():
        report = directory / 'report.json'
        report_pins[str(report.relative_to(root)).replace('\\', '/')] = sha(report)
        role = directory.parent.name
        section = 'source_bodies' if role in ('m4-crt-allocation', 'm4-crt-heap-init', 'm4-crt-heap-mode', 'm4-crt-heap-version') else 'components'
        special = {}
        if role == 'm4-crt-mainargs':
            section = 'native'
            graphs = json.loads(report.read_text())['graphs']
            special = {name: dict(start=value['entry'], end=value['entry']+value['source_bytes'],
                                 entry=value['entry'], source_sha256=value['source_sha256']) for name, value in graphs.items()}
        if role in ('m4-crt-heap-init', 'm4-crt-heap-mode', 'm4-crt-heap-version'):
            labels = {
                'm4-crt-heap-init': {'provider': 'heap-initializer'},
                'm4-crt-heap-mode': {'selector': 'selector-prefix', 'probe': 'stack-probe'},
                'm4-crt-heap-version': {'branch': 'selector-conditions', 'environment': 'selector-environment-frontier',
                                        'mode1': 'selector-mode1-cold', 'epilogue': 'selector-epilogue'}}[role]
            recovery = root / 'reports' / (role + '-recovery') / 'recovery-r1/report.json'
            spans = json.loads(recovery.read_text())['spans']
            report_pins[str(recovery.relative_to(root)).replace('\\', '/')] = sha(recovery)
            for name, label in labels.items():
                if name in wanted:
                    span = spans[label]
                    special[name] = dict(start=span['start'], end=span['end_exclusive'], entry=span['start'], source_sha256=span['sha256'])
        for name, component in components(report, section):
            if name not in wanted:
                continue
            obj, optimization = wanted[name]
            component = component | special.get(name, {})
            if role == 'm4-crt-allocation':
                component = component | dict(start=component['entry'], end=component['entry'] + component['source_bytes'])
            start, end, entry = (component[k] for k in ('start', 'end', 'entry'))
            if not start <= entry < end or end - start > 1024**2:
                raise ValueError('Invalid component source bounds')
            recipes[name] = dict(image=image_for(start), start=start, end=end, entry=entry,
                                 source_sha256=component['source_sha256'],
                                 expected_object_sha256=sha(obj), optimization=optimization,
                                 coff_timestamp=struct.unpack_from('<I', obj.read_bytes(), 4)[0],
                                 lower_namespace=('mw34_' + role.removeprefix('m4-crt-').replace('-', '_') + '_')
                                     if section in ('source_bodies', 'native') else 'mw34_attach_',
                                 renames=component.get('renames', {}))
        missing = set(wanted) - set(recipes)
        if missing:
            raise ValueError('Missing selected component recipes: ' + repr(sorted(missing)))
    # Image digests are the admitted input identities, not bytes copied from reports.
    images = {
        'game': ('MECH3.EXE', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),
        'mfc42': ('native-inputs/MFC42.DLL', '5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'),
        'msvcrt': ('native-inputs/MSVCRT.DLL', '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'),
        'msvcp50': ('native-inputs/MSVCP50.DLL', '91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'),
        'ir50': ('native-inputs/Ir50_32.base11000000.dll', '9d066dbdb0b9903c2afb07284d609c7d3ed3278245040490e9805d4cd717958f'),
        'mech3msg': ('MECH3MSG.DLL', '8899fabb7e57383a9a483cb048636bcc027334b48941aa49835cdcc1c4715b8c')}
    result = dict(schema_version=1, contract='mw3-translated-bodies-v1',
                  images={k: dict(path=p, sha256=h) for k, (p, h) in images.items()},
                  components=[dict(name=n, **recipes[n]) for n in (p.name.removesuffix('-O2.obj') for p in selected)])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, separators=(',', ':')) + '\n')
    # Lineage paths belong in the local export receipt, not the portable recipe.
    output.with_suffix('.lineage.json').write_text(json.dumps(dict(objects_list_sha256=sha(objects),
        recipe_sha256=sha(output), source_reports=report_pins, components=len(recipes)), indent=2) + '\n')
    return len(recipes), output.stat().st_size


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--objects', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(export(args.root.resolve(), args.objects.resolve(), args.output.resolve()))
