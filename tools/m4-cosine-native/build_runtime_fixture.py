"""Reuse the frozen builder for a fresh compound Runtime fixture link."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
parent = Path(__file__).resolve().parents[1] / 'm4-tree-review/build_fixture.py'
text = parent.read_text()
text = text.replace("R/'reports/m4-tree-review'/name", "R/'reports/m4-cosine-native'/name")
text = text.replace("tree/'mw34_joint_startup124.exe'", "tree/'mw34_joint_startup125.exe'")
text = text.replace('isolated actual Runtime-selected tree fixture', 'isolated actual Runtime-selected compound cosine fixture')
text = text.replace('pin(__file__);', "pin(__file__);pin(R/'tools/m4-tree-review/build_fixture.py');")
exec(compile(text, str(parent), 'exec'), globals())
