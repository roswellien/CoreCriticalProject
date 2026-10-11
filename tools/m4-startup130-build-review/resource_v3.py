"""Bind the accepted resource checks to current native19/compiler input paths."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
parent = Path(__file__).with_name('resource_v2.py')
wrapper = parent.read_text()
before = 'text = parent.read_text()'
assert wrapper.count(before) == 1
wrapper = wrapper.replace(before, "text = parent.read_text()\nassert text.count('from review import') == 1\ntext = text.replace('from review import', 'from review_v3 import')")
before = "common(name);pin(__file__);pin(ROOT/'tools/m4-tree-build-review/resource_v2.py')"
assert wrapper.count(before) == 1
wrapper = wrapper.replace(before, "common(name);pin(__file__);pin(ROOT/'tools/m4-startup130-build-review/resource_v2.py');pin(ROOT/'tools/m4-tree-build-review/resource_v2.py')")
exec(compile(wrapper, str(parent), 'exec'), globals())
