"""Preserve the frozen typed repair and explicit backward sqrt fragment scope."""
from pathlib import Path
import hashlib

PREVIOUS = Path(__file__).with_name('lift_v3.py')
PREVIOUS_SHA = 'b8f235924bd6ec2fb3cec23babd0e4b94d185b10501208182ad7d50591dc8728'
assert hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() == PREVIOUS_SHA
revision = PREVIOUS.read_text(encoding='utf-8')
before = "'tools/m4-hypot-native/control_ir.py'"
assert revision.count(before) == 1
revision = revision.replace(before, "'tools/m4-hypot-native/control_ir_v2.py'")
before = "exec(compile(source, str(BASE), 'exec'), globals())"
assert revision.count(before) == 1
revision = revision.replace(before,
    "source = source.replace('pin(BASE, BASE_SHA)', 'pin(BASE, BASE_SHA)\\n        pin(PREVIOUS, PREVIOUS_SHA)\\n        pin(ROOT / \\\"tools/m4-hypot-native/control_ir.py\\\", \\\"f54fb4b1798023650da496457cde948cb64797ec77beab92a6a642ad15ce45fa\\\")')\n"+before)
exec(compile(revision, str(PREVIOUS), 'exec'), globals())
