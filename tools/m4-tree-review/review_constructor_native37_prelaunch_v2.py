"""Correct the path-only linker argv normalization; all admission guards remain."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_constructor_native37_prelaunch.py')
t=p.read_text()
a="str(Path(x)).resolve().as_posix().casefold()"
assert t.count(a)==1
t=t.replace(a,"Path(x).resolve().as_posix().casefold()")
a="  pin(__file__);pin(sys.executable);"
assert t.count(a)==1
t=t.replace(a,"  pin(R/'tools/m4-tree-review/review_constructor_native37_prelaunch.py');pin(__file__);pin(sys.executable);")
exec(compile(t,str(Path(__file__)),'exec'),globals())
