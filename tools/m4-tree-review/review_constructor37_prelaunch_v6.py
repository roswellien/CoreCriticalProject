"""Admit the current protocol-size repair with explicit MASM object attribution.

The C++ capture object has multiple executable sections and is not a MASM
observer. All ten actual assembly observers are linked as whole sections.
"""
from pathlib import Path
import hashlib, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
parent5 = R/'tools/m4-tree-review/review_constructor37_prelaunch_v5.py'
assert hashlib.sha256(parent5.read_bytes()).hexdigest() == 'd80411304cdc44a0dd0b43f98583448f22f75b03407c7b119f7b80c27b1f4dd3'
wrapper = parent5.read_text()
old = "exec(compile(text,str(parent),'exec'),globals())"
new = '''
for before,after in {
 '75651d2e01281c8bfea102bdf4d8b32649eeff379789afadc1d2079fd6f1d507':'01045f8b1325be4133b49a9af650d0d9506acd04a999db6ce9dcd6848b921781',
 'bcf2cc5e4c9e197cf99374a47f136fa88db2e6e48fe558bc8ba565628aeeb054':'62bb642690f68e0841d7691c1d01a5b308332d184039fa3955be05a29621fc6c',
 'chronological-preparation-r4':'chronological-preparation-r5',
 'chronological-build-r2':'chronological-build-r3',
 "for obj in sorted(release.glob('*.obj')):":"for obj in [release/(leaf+'.obj') for leaf in ('reference_x86','boundaries','api_boundaries','preserve_x86','fs_observer_x86','nullfree_observer_x86','vtable_observer_x86','lockit_observer_x86','format_observer_x86','constructor_observer_x86')]:",
 'pin(parent);pin(R/':'pin(parent5);pin(parent);pin(R/',
}.items():
 assert before in text, before
 text = text.replace(before,after)
exec(compile(text,str(parent),'exec'),globals())
'''
assert wrapper.count(old) == 1
wrapper = wrapper.replace(old,new)
exec(compile(wrapper,str(parent5),'exec'),globals())
