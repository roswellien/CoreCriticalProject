"""Correct the explicit free GDI witness template name; map1 stays frozen."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
base = R/'tools/m4-joint-startup138/controls_admission_map.py'
source = base.read_text()
old = "'mw34::m4_widget_native::Component::Impl::observe_gdi_identity'"
assert source.count(old) == 1
source = source.replace(old, "'mw34::m4_widget_native::observe_gdi_identity'")
source = source.replace('pin(__file__); pin(sys.executable)', 'pin(__file__); pin(base); pin(sys.executable)')
exec(compile(source, str(base), 'exec'), globals())
