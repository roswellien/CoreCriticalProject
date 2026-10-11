"""Run the frozen130 corpus with inherited strict transport and stage checks.

Only table sizes, current callback count and the resulting completion text
change from the accepted125 runner. Semantic acceptance remains separate.
"""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
parent = Path(__file__).resolve().parents[1] / 'm4-joint-startup125/run.py'
text = parent.read_text()
replacements = [
    ('selected125', 'selected130'),
    ('startup125-root', 'startup130-root'),
    ("len(prep['selected_order'])==125", "len(prep['selected_order'])==130"),
    ('(1,6,125,750,17,159716)', '(1,6,130,780,17,159716)'),
    ("records.words('selected-table.bin',125)", "records.words('selected-table.bin',130)"),
    ("records.words('registration-roots.bin',97)", "records.words('registration-roots.bin',101)"),
    ('len(set(entries))==125', 'len(set(entries))==130'),
    ('(1,125,0,0,0,0,0,0)', '(1,130,0,0,0,0,0,0)'),
    ('persistent125-root', 'persistent130-root'),
    ('pin(__file__);pin(sys.executable)',
     "pin(__file__);pin(ROOT/'tools/m4-joint-startup125/run.py');pin(sys.executable)"),
]
for before, after in replacements:
    assert before in text, before
    text = text.replace(before, after)
assert '125' not in text.replace("tools/m4-joint-startup125/run.py", '')
exec(compile(text, str(parent), 'exec'), globals())
