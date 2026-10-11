"""Independent page-split closure; retain the original prelaunch checker."""
from pathlib import Path
import hashlib
BASE = Path(__file__).with_name('review_widget_prelaunch.py')
BASE_SHA = '4fc0ac68444b2fd77a471be5e7357695d9838eb4006a9976929326012492ca9c'
if hashlib.sha256(BASE.read_bytes()).hexdigest() != BASE_SHA:
    raise ValueError('Exact immutable independent prelaunch checker')
source = BASE.read_text()
old = "'const std::array<NullHook,0>null_hooks{};'"
new = "'const std::array<NullHook,0> null_hooks{};'"
if source.count(old) != 1:
    raise ValueError('One literal whitespace correction')
source = source.replace(old, new, 1)
anchor = "        eq(len(sparse_pages), 159, 'Exact current sparse page inventory')"
addition = """
        pin(BASE, BASE_SHA)
        pin(R / 'tools/m4-widget-original/derive_prepare_v7.py')
        pin(R / 'tools/m4-widget-original/prepare_v7.py')
        page_proofs = []
        crossing_rows = []
        for row in rows:
            pc = row['pc']; expected = bytes.fromhex(row['bytes_hex'])
            actual = bytearray()
            for offset in range(len(expected)):
                address = pc + offset
                need(address & ~4095 in sparse_pages, 'Every crossed physical source page exists')
                actual.append(sparse_pages[address & ~4095][1][address & 4095])
            eq(bytes(actual), expected, 'Complete instruction retained across every actual page boundary')
            counts['source_rows_complete_sparse_byte_relations'] += 1
            if pc & ~4095 != (pc + len(expected) - 1) & ~4095:
                crossing_rows.append(dict(pc=pc, source_hex=expected.hex(), pages=[pc & ~4095, (pc+len(expected)-1) & ~4095], widths=[4096-(pc&4095),len(expected)-(4096-(pc&4095))]))
        eq(crossing_rows, [dict(pc=0x5a2ffe,source_hex='895628',pages=[0x5a2000,0x5a3000],widths=[2,1])], 'Exact physically observed crossing instruction closure')
        eq((sparse_pages[0x5a2000][1][-2:], sparse_pages[0x5a3000][1][:1]), (bytes.fromhex('8956'),bytes.fromhex('28')), 'Actual two-page 89 56 28 retained without resizing')
        counts['source_crossing_instruction_relations'] = len(crossing_rows)
        counts['exact_sparse_page_payloads'] = len(sparse_pages)
        counts['exact_sparse_pack_bytes'] = len(raw(directory / 'pages.bin'))
        (out / 'whole-page-boundary-relations.json').write_text(json.dumps(crossing_rows,indent=2)+'\\n')
        pin(out / 'whole-page-boundary-relations.json')
"""
if source.count(anchor) != 1:
    raise ValueError('One independent sparse inventory join')
source = source.replace(anchor, anchor + '\n' + addition, 1)
exec(compile(source, str(BASE), 'exec'), globals())
