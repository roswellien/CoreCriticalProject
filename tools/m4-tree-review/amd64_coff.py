"""Bounded standard AMD64 COFF reader for independent executable attribution."""
import struct


def need(value, why):
    if not value:
        raise ValueError(why)


def parse(data):
    machine, count, _, table, total, optional, _ = struct.unpack_from('<HHIIIHH', data)
    need(machine == 0x8664 and optional == 0, 'Standard AMD64 COFF, not a guessed architecture')
    strings = table + total * 18
    end = strings + struct.unpack_from('<I', data, strings)[0]
    need(end <= len(data), 'Complete bounded COFF string table')
    symbols = {}
    index = 0
    while index < total:
        name, value, section, typ, storage, aux = struct.unpack_from('<8sIhHBB', data, table + index * 18)
        if name[:4] == b'\0' * 4:
            start = strings + struct.unpack_from('<I', name, 4)[0]
            need(strings + 4 <= start < end, 'Bounded long COFF symbol')
            name = data[start:data.index(b'\0', start, end)]
        else:
            name = name.rstrip(b'\0')
        symbols[index] = dict(name=name.decode('ascii'), value=value, section=section, type=typ, storage=storage)
        index += 1 + aux
    sections = {}
    for index in range(count):
        start = 20 + index * 40
        size, raw, reloc, _, number = struct.unpack_from('<IIIIH', data, start + 16)
        flags = struct.unpack_from('<I', data, start + 36)[0]
        need(raw + size <= len(data) and reloc + number * 10 <= len(data), 'Whole bounded COFF section/relocation table')
        rows = []
        for j in range(number):
            offset, target, typ = struct.unpack_from('<IIH', data, reloc + j * 10)
            need(target in symbols, 'Every physical relocation has a symbol')
            rows.append(dict(offset=offset, symbol=symbols[target], type=typ))
        sections[index + 1] = dict(bytes=data[raw:raw + size], flags=flags, relocations=rows)
    return symbols, sections


def function(symbols, sections, name):
    definitions = [row for row in symbols.values() if row['name'] == name and row['section'] > 0]
    need(len(definitions) == 1, 'One actual defined function ' + name)
    row = definitions[0]
    section = sections[row['section']]
    need(row['type'] == 0x20 and section['flags'] & 0x20000000, 'Actual executable function symbol ' + name)
    ends = [x['value'] for x in symbols.values() if x['section'] == row['section'] and x['type'] == 0x20 and x['value'] > row['value']]
    end = min(ends, default=len(section['bytes']))
    relocations = [dict(r, offset=r['offset'] - row['value']) for r in section['relocations'] if row['value'] <= r['offset'] < end]
    return section['bytes'][row['value']:end], relocations


def linked_candidates(image, raw, relocations):
    need(raw, 'Nonempty whole function')
    ignored = {byte for row in relocations for byte in range(row['offset'], row['offset'] + 4)}
    need(all(row['type'] == 4 for row in relocations), 'Every executable relocation is exact AMD64 REL32')
    runs, start = [], None
    for index in range(len(raw) + 1):
        if index < len(raw) and index not in ignored:
            if start is None:
                start = index
        elif start is not None:
            runs.append((start, raw[start:index]))
            start = None
    anchor, needle = max(runs, key=lambda pair: len(pair[1]))
    output = []
    for section in image.sections:
        if not section['executable']:
            continue
        data = image.data[section['raw_offset']:section['raw_offset'] + section['raw_size']]
        position = 0
        while True:
            position = data.find(needle, position)
            if position < 0:
                break
            begin = position - anchor
            actual = data[begin:begin + len(raw)] if begin >= 0 else b''
            if len(actual) == len(raw) and all(a == b for i, (a, b) in enumerate(zip(actual, raw)) if i not in ignored):
                output.append((image.image_base + section['virtual_address'] + begin, actual))
            position += 1
    return output
