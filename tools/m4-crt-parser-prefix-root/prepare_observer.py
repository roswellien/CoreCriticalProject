"""Add a BEFORE-only parser oracle to the frozen complete carry observer."""
import hashlib
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
HERE = Path(__file__).absolute().parent


def change(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Exact observer derivative site: ' + old[:100])
    return text.replace(old, new)


def main():
    ancestor = ROOT / 'tools/m4-crt-commandline-carry-root/observe.py'
    if hashlib.sha256(ancestor.read_bytes()).hexdigest() != '76a1bbef4cc8f4e343495a4bf0209d051c547af5781c8d045bb6084c4e07e225':
        raise ValueError('Frozen complete carry observer identity')
    out = HERE / 'observe.py'
    if out.exists():
        raise FileExistsError(out)
    s = ancestor.read_text(encoding='utf-8')
    s = change(s, 'from model import expected',
               'from model import expected\nfrom parser import predict as parser_predict, source_material as parser_source, SOURCE_SHA')
    s = change(s, "    if owned is not None:\n", "    result['parser-source.bin'] = values[f'page-{0x7800b000}.bin'][0xc48:0xdfc]\n"
               "    F.require(hashlib.sha256(result['parser-source.bin']).hexdigest() == SOURCE_SHA,\n"
               "              'Exact full 436-byte original parser remains unpatched')\n    if owned is not None:\n")
    s = change(s, 'def positive(row, entry, phases, program, index, worker, host_bytes, argv, attack):',
               'def positive(row, entry, phases, program, parser_program, index, worker, host_bytes, argv, attack):')
    s = change(s, '    commandline_identity(row, host_bytes)',
               "    F.require(host_bytes[0] == 0x44, 'Exact measured D-leading native parser domain')\n    commandline_identity(row, host_bytes)")
    s = change(s, "    final = OLD.stage(consumed['state'], consumed['fx'], consumed['cpu'], consumed['memory'])\n"
               "    phases['commandline-parser-before'] = final",
               "    parser_before = OLD.stage(consumed['state'], consumed['fx'], consumed['cpu'], consumed['memory'])\n"
               "    phases['commandline-parser-before'] = parser_before\n"
               "    parser_holder = type('ExpectedParserMachine', (), dict(state=consumed['state'],\n"
               "        mem=consumed['memory'], fx=consumed['fx'], runtime_cpu=consumed['cpu']))()\n"
               "    parsed = parser_predict(parser_holder, parser_program, host_bytes)\n"
               "    phases.update(parsed['phases'])\n"
               "    final = OLD.stage(parsed['state'], parsed['fx'], parsed['cpu'], parsed['memory'])")
    s = change(s, "tag.startswith(('mainargs-', 'filename-', 'commandline-'))", "tag.startswith(('mainargs-', 'filename-', 'commandline-', 'parser-'))")
    s = change(s, "attack and tag.startswith(('commandline-', 'filename-'))", "attack and tag.startswith(('commandline-', 'filename-', 'parser-'))")
    s = change(s, "job[11], job[18], job[19] = len(routes), 0x7800bbf7, 0x7800bc48", "job[11], job[18], job[19] = len(routes), parsed['stop_PC'], parsed['stop_address']")
    s = change(s, "(0, 0x7800bbf7, 0x7800bc48),\n              'Typed stop at actual parser CALL, after real stack stores'",
               "(0, parsed['stop_PC'], parsed['stop_address']),\n              'Typed refusal before actual uninitialized locale-table read'")
    s = change(s, "'Required actual command-line parser remains unresolved',\n              'Required dependency reason retained'",
               "'Required initialized CRT lead-byte table remains unresolved',\n              'Required locale dependency reason retained'")
    s = change(s, "'Required actual command-line parser remains unresolved',\n              'Command-line first parser-boundary reason retained'",
               "'',\n              'Completed command-line producer and consumer retain no fabricated fault'")
    s = change(s, "struct.unpack_from('<3I', actual_job, 20) == (0, 0x7800bbf7, 0x7800bc48)",
               "struct.unpack_from('<3I', actual_job, 20) == (0, parsed['stop_PC'], parsed['stop_address'])")
    s = change(s, "job[9:23] == (8, 0, 0x7800bbf7, 0x7800bc48,\n                           1, 0, 1, 1, 1, 1, 1, 1, 1, 1)",
               "job[9:23] == (8, 0, 0, 0,\n                           1, 0, 1, 1, 1, 1, 1, 1, 1, 0)")
    addition = """    F.require(len(parsed['accesses']) == 16 and len(parsed['PCs']) == 23 and
              not parsed['locale_read_completed'], 'Complete source prefix before denied table access')
    parser_accesses = b''.join(struct.pack('<5I', *v) for v in parsed['accesses'])
    F.require((row / 'parser-accesses.bin').read_bytes() == parser_accesses + bytes(640 - len(parser_accesses)),
              'Entire parser PUSH, argument, count and immutable-input access ledger')
    F.require(F.words((row / 'parser-undefined.bin').read_bytes(), 8) ==
              (0x7800bc66, 0x7800bcd7, 0, 0, 0, 0, 0, 0),
              'Exact two TEST undefined-AF representative sites')
    parser_events = [(1, 0x7800bbf7, 0x7800bc48, 0x7800bbfc),
                     (2, 0x7800bc48, 0x2000182c, 0x7800bbfc),
                     (3, parsed['stop_PC'], parsed['stop_address'], 0x44)]
    parser_events_bytes = b''.join(struct.pack('<4I', *v) for v in parser_events)
    F.require((row / 'parser-events.bin').read_bytes() == parser_events_bytes + bytes(128 - len(parser_events_bytes)),
              'Entire source-qualified parser route and uninitialized locale refusal ledger')
    F.require(F.words((row / 'parser-job.bin').read_bytes(), 20) ==
              (0, 0x2000182c, 0x20001860, 16, 3, 2, 4, 0, parsed['stop_PC'],
               parsed['stop_address'], 1, 0, 1, 1, 0x7800bc48, 0x7800bbf7,
               0x7800bbfc, 0x7800bce6, 0x780379e1, 436),
              'Exact normal parser immutable frame, lifecycle, source and first-fault metadata')
    F.require((row / 'parser-reason.txt').read_text().strip() ==
              'Required initialized CRT lead-byte table remains unresolved', 'Typed parser first dependency reason')
"""
    s = change(s, '    return dict(index=index, control=0, producer_source_bytes=11,', addition +
               '    return dict(index=index, control=0, producer_source_bytes=11,')
    s = change(s, 'parser_body_executed=False, State3504_FX512=True, checkpoints=len(phases))',
               "parser_body_executed=True, parser_source_instructions=len(parsed['PCs']),\n"
               "                parser_memory_accesses=16, locale_read_completed=False, parser_RET_executed=False,\n"
               "                State3504_FX512=True, checkpoints=len(phases))")
    s = s.replace("ROOT / 'reports/m4-crt-commandline-carry'", "ROOT / 'reports/m4-crt-parser-prefix'")
    s = change(s, "        wp, pp, gp = M.R.source_material()", "        parser_program, parser_command = parser_source(out)\n        wp, pp, gp = M.R.source_material()")
    s = change(s, "rows.append(dict(level=level, **positive(row, entry, phases, argv, index,",
               "rows.append(dict(level=level, **positive(row, entry, phases, argv, parser_program, index,")
    s = change(s, "source_writer_and_consumer_executed=passed, parser_body_executed=False,",
               "source_writer_and_consumer_executed=passed, parser_body_executed=passed,\n"
               "            parser_source_bytes=436, source_identity_bytes=1587, locale_read_completed=False,\n"
               "            parser_RET_executed=False, parser_sizing_complete=False,")
    out.write_text(s, encoding='utf-8')
    print('Fresh complete observer written; ancestor bytes unchanged')


if __name__ == '__main__':
    main()
