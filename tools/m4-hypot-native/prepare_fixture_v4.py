"""Bind the same native code to the entire genuine trace BEFORE stack page."""
from pathlib import Path
import hashlib

CURRENT = Path(__file__).resolve()
CURRENT_SHA = hashlib.sha256(CURRENT.read_bytes()).hexdigest()
V3 = CURRENT.with_name('prepare_fixture_v3.py')
V3_SHA = '21970db46ce432e3536a8d5df8fc9427a2ed5fb8f035c8291a8aa600174ef96e'
assert hashlib.sha256(V3.read_bytes()).hexdigest() == V3_SHA
generator = V3.read_text()
for old, new in [
    ("'inputs-r4/report.json'", "'inputs-r5/report.json'"),
    ('2e06405a753a7cd1ec4fec34f85ea4af0cce5040c250d39b0c5ee3990bea5c8a',
     'd91a51b3884ef8940fbf18eda2e9301b62077720eb3d9f00b467bd54fd1a9af4')]:
    assert generator.count(old) == 1
    generator = generator.replace(old, new)
anchor = '        pin(PREVIOUS,PREVIOUS_SHA);'
assert generator.count(anchor) == 1
generator = generator.replace(anchor,
    '        pin(V3,V3_SHA);pin(CURRENT,CURRENT_SHA);pin(ROOT/\'tools/m4-hypot-native/couple_trace_before.py\');' + anchor.strip())
exec(compile(generator, str(V3), 'exec'), globals())
