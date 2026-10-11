"""Add six literal bodies for the physically observed normal hypot domain.

Unreached source rows remain deliberately absent. The lifter's missing-block
and padded-instruction bridges must deny them; this is not a cold-path proof.
"""
from pathlib import Path
import hashlib

BASE = Path(__file__).with_name('lift.py')
BASE_SHA = '9a6796888d0308e247ab611c14a763ca37a94135ae92ca7feb4c4c55f79a3adb'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
source = BASE.read_text(encoding='utf-8')


def one(before, after):
    global source
    assert source.count(before) == 1, before
    source = source.replace(before, after)


one("CRT_ENTRIES = (0x7802a122, 0x7802a15c, 0x7802d278, 0x78029241,\n"
    "               0x7802d19a, 0x7802d12c, 0x7802d103,\n"
    "               0x7802c2fa, 0x7802c2ca, 0x7802c2e1)",
    "CRT_ENTRIES = (0x7802c2aa, 0x7802cdf1, 0x7802d089, 0x7802d29b, 0x7802d303)")
one('TAIL_ENTRIES = (0x78028969, 0x78029110, 0x7802c353)',
    'TAIL_ENTRIES = (0x7802c277,)')
one("game_graphs = read(REC / 'game-graphs.json')",
    "game_graphs = read(REC / 'game-graphs.json')\n"
    "        trace_report = ROOT / 'reports/m4-hypot-original/trace-validation-r2/report.json'\n"
    "        trace = read(trace_report, 'be137c4a05a5f9d33805f5cbb9db60157bf707fb2e1298db9b90ec943686780f')\n"
    "        need(trace['passed'] and trace['reader_closed'] and not trace['source_after_seed'], 'Closed genuine source trace')\n"
    "        for path,digest in trace['files'].items():\n"
    "            if Path(path).suffix.lower() not in ('.mwb','.zip'):\n"
    "                pin(path,digest)\n"
    "        observed = read(trace_report.parent / 'actual-source-traces.json')\n"
    "        need(len(observed)==6 and all(x['event_count']==1007 for x in observed), 'Six actual complete finite traces')\n"
    "        reached = set(map(int,observed[0]['actual_reached_PC_counts']))\n"
    "        need(len(reached)==439 and all(set(map(int,x['actual_reached_PC_counts']))==reached for x in observed), 'Exact shared reached source domain')")
one("selected = [(key, g, 'game', False) for key,g in game_graphs.items()]",
    "selected = []  # Existing fifteen sealed game/provider bodies are reused separately.")
one("sqrt_rows = {r['pc']:r for r in crt_graphs[str(0x78029241)]['instructions']}",
    "sqrt_rows = {}\n"
    "        for g in crt_graphs.values():\n"
    "            for row in g['instructions']:\n"
    "                need(row['pc'] not in sqrt_rows or sqrt_rows[row['pc']]['bytes']==row['bytes'], 'Shared physical source bytes agree')\n"
    "                sqrt_rows[row['pc']] = row")
one("bridges.discard('mw34_onexit_game_fsqrt_raw80')",
    "control = module(ROOT / 'tools/m4-hypot-native/control_ir.py', 'hypot_reached_control',\n"
    "                         'f54fb4b1798023650da496457cde948cb64797ec77beab92a6a642ad15ce45fa')\n"
    "        bridges.update({'mw34_hypot_wait','mw34_hypot_store_cw','mw34_hypot_load_cw'})\n"
    "        bridges.discard('mw34_onexit_game_fsqrt_raw80')")
one("rows = graph['instructions']\n            included = [r for r in rows if r['pc'] >= entry]",
    "rows = graph['instructions']\n"
    "            omitted = [r for r in rows if r['pc'] not in reached]\n"
    "            rows = [r for r in rows if r['pc'] in reached]\n"
    "            graph = dict(graph, instructions=rows)\n"
    "            included = [r for r in rows if r['pc'] >= entry]\n"
    "            need(included and included[0]['pc']==entry, 'Actual reached native entry')")
one('strict, counts = helper.strict_fp(original)',
    'controlled, CW_transfers = control.repair(original, graph)\n'
    '            strict, counts = helper.strict_fp(controlled)')
one('direct_source_targets=calls,strict_FP=counts,',
    'direct_source_targets=calls,strict_FP=counts,CW_transfers=CW_transfers,\n'
    '                omitted_unreached_rows=omitted,cold_source_domain_admitted=False,')
one('for path in (Path(__file__), Path(sys.executable),',
    'pin(BASE, BASE_SHA)\n        for path in (Path(__file__), Path(sys.executable),')
one("scope='Hypot literal game/provider x64 COFF preparation; execution and cold branch admission remain separate'",
    "scope='Six additional literal x64 bodies restricted to genuine normal hypot source rows; no execution or cold-path credit'")
one('complete_provider_closure=False,commands=commands,files=pins,',
    "complete_provider_closure=False,actual_source_domain_report_sha256=sha(trace_report),\n"
    "            actual_shared_reached_source_PCs=sorted(reached),\n"
    "            repeated_old_bodies=0,CW_instruction_replacements_reversible=True,\n"
    "            typed_CW_runtime_implementation_verified=False,\n"
    "            commands=commands,files=pins,")
exec(compile(source, str(BASE), 'exec'), globals())
