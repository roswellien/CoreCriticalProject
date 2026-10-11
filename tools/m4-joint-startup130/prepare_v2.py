"""Preserve the original frozen composer while pinning additive cleanup lineage."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
parent = Path(__file__).with_name('prepare.py')
text = parent.read_text()
before = '    pin(__file__)\n    report = dict('
assert text.count(before) == 1
text = text.replace(before, "    pin(__file__)\n    pin(ROOT / 'tools/m4-joint-startup130/prepare.py')\n    report = dict(")
exec(compile(text, str(parent), 'exec'), globals())
