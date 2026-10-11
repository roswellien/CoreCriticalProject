"""Preserve the reviewed bridge check and distinguish build/worker identities."""
from pathlib import Path
import hashlib

BASE = Path(__file__).with_name('root_preflight.py')
BASE_SHA = '11e5df9f4d209299b3203ed0003bace9c932cd485c0109dd71c87e2caa2f35fb'
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == BASE_SHA
source = BASE.read_text(encoding='utf-8')
before = "counts=dict(counts), build_sha256=build.get('worker_sha256') if 'build' in locals() else None,"
after = "counts=dict(counts), build_sha256='579280372eb328bc383a703927e8279ec8cb6c1351b5a8fe129f58ae7bb00ae5',\n            worker_sha256=build.get('worker_sha256') if 'build' in locals() else None,"
assert source.count(before) == 1
source = source.replace(before, after)
before = '        pin(__file__)'
assert source.count(before) == 1
source = source.replace(before, '        pin(BASE, BASE_SHA)\n' + before)
exec(compile(source, str(BASE), 'exec'), globals())
