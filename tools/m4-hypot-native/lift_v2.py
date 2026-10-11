"""Retain the declared FLDCW bridge as an unadmitted source preparation seam."""
from pathlib import Path
import hashlib

BASE = Path(__file__).with_name('lift.py')
BASE_SHA = '9a6796888d0308e247ab611c14a763ca37a94135ae92ca7feb4c4c55f79a3adb'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
source = BASE.read_text(encoding='utf-8')
before = "'__remill_async_hyper_call'}"
after = "'__remill_async_hyper_call', '__remill_fpu_set_rounding'}"
assert source.count(before) == 1
source = source.replace(before, after)
before = 'for path in (Path(__file__), Path(sys.executable),'
assert source.count(before) == 1
source = source.replace(before, 'pin(BASE, BASE_SHA)\n        ' + before)
before = 'complete_provider_closure=False,commands=commands,files=pins,'
after = "complete_provider_closure=False,CW_semantic_repairs_applied=False,\n            required_before_execution=['Source-defined FNSTCW/FLDCW preservation',\n                'Actual reached provider/FP trace', 'Raw80 and F32 exception/status contracts',\n                'Complete state/memory/provider/cleanup/fault comparison'],\n            commands=commands,files=pins,"
assert source.count(before) == 1
source = source.replace(before, after)
exec(compile(source, str(BASE), 'exec'), globals())
