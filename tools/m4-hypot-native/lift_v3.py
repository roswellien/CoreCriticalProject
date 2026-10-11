"""Add exact typed wait/CW boundaries to the frozen physical hypot lifts."""
from pathlib import Path
import hashlib

BASE = Path(__file__).with_name('lift.py')
BASE_SHA = '9a6796888d0308e247ab611c14a763ca37a94135ae92ca7feb4c4c55f79a3adb'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
source = BASE.read_text(encoding='utf-8')

def one(before,after):
    global source
    assert source.count(before)==1
    source=source.replace(before,after)

one("bridges.discard('mw34_onexit_game_fsqrt_raw80')", "control = module(ROOT / 'tools/m4-hypot-native/control_ir.py', 'hypot_native_control_repair')\n        bridges.update({'mw34_hypot_wait','mw34_hypot_store_cw','mw34_hypot_load_cw'})\n        bridges.discard('mw34_onexit_game_fsqrt_raw80')")
one('strict, counts = helper.strict_fp(original)',
    'controlled, CW_transfers = control.repair(original, graph)\n            strict, counts = helper.strict_fp(controlled)')
one('direct_source_targets=calls,strict_FP=counts,',
    'direct_source_targets=calls,strict_FP=counts,CW_transfers=CW_transfers,')
one('for path in (Path(__file__), Path(sys.executable),',
    'pin(BASE, BASE_SHA)\n        for path in (Path(__file__), Path(sys.executable),')
one('complete_provider_closure=False,commands=commands,files=pins,',
    "complete_provider_closure=False,CW_instruction_replacements_reversible=True,\n            typed_CW_runtime_implementation_verified=False,\n            required_before_execution=['Actual reached provider/FP trace',\n                'Occupied-stack CW preservation and complete typed context',\n                'Raw80 and F32 exception/status contracts',\n                'Complete state/memory/provider/cleanup/fault comparison'],\n            commands=commands,files=pins,")
exec(compile(source, str(BASE), 'exec'), globals())
