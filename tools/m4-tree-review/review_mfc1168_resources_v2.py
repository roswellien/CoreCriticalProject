"""Preserve raw path conservation and compare canonical Windows owner identity."""
from pathlib import Path
import hashlib
BASE = Path(__file__).with_name('review_mfc1168_resources.py')
SHA = '358bd5060d6ebccb33a5cce3a60a9720c6e45d1722c33094aa5db0f7f845e1be'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == SHA
source = BASE.read_text()
before = "eq(raw(directory / 'before-path.txt').decode(), proof['actual_owner'], 'Actual physical owner path')"
after = "eq(Path(raw(directory / 'before-path.txt').decode()).resolve(), Path(proof['actual_owner']).resolve(), 'Actual canonical physical owner path; raw before/after paths conserved separately')"
assert source.count(before) == 1
source = source.replace(before, after)
before = '        pin(__file__)\n'
assert source.count(before) == 1
source = source.replace(before, '        pin(BASE, SHA)\n' + before)
exec(compile(source, str(BASE), 'exec'), globals())
