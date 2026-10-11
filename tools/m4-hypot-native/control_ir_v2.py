"""Keep the backward sqrt CW target in its separately compiled fragment."""
from pathlib import Path
import hashlib
import importlib.util

BASE = Path(__file__).with_name('control_ir.py')
BASE_SHA = 'f54fb4b1798023650da496457cde948cb64797ec77beab92a6a642ad15ce45fa'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
spec = importlib.util.spec_from_file_location('hypot_control_base', BASE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def repair(text, graph):
    deferred = []
    if graph['entry'] == 0x78029241:
        # sqrt reaches this source only through its backward shared tail. The
        # main lifted body ends that edge at a declared machine frontier; the
        # exact CW target is separately compiled at its real PC.
        rows = [r for r in graph['instructions'] if r['pc'] == 0x7802c353]
        assert len(rows) == 1 and rows[0]['mnemonic'] == 'fldcw'
        graph = dict(graph, instructions=[r for r in graph['instructions'] if r['pc'] != 0x7802c353])
        deferred = [dict(instruction='fldcw', physical_PC=rows[0]['pc'],
            physical_bytes=rows[0]['bytes'], deferred_local_CW_lowering=True,
            separate_literal_entry=0x7802c353,
            actual_dispatch_and_execution_verified=False)]
    candidate, records = base.repair(text, graph)
    return candidate, records + deferred
