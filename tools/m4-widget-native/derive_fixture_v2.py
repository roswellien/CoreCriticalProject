"""Retain the first failed compile; use the runtime's physical admission identity."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'tools/m4-widget-native/fixture.cpp'
s=p.read_text();assert s.count('r.image_metadata().sha256')==1
s=s.replace('#include "widget_bindings.hpp"','#include "widget_bindings.hpp"\n#include "admission.hpp"')
s=s.replace('r.image_metadata().sha256','m4::admitted_image_hash')
out=R/'tools/m4-widget-native/fixture_v2.cpp';assert not out.exists();out.write_text(s)
p=R/'tools/m4-widget-native/prepare_fixture.py';s=p.read_text()
s=s.replace('tools/m4-widget-native/fixture.cpp','tools/m4-widget-native/fixture_v2.cpp')
s=s.replace("for p in ['tools/m4-widget-native/fixture_v2.cpp',", "for p in ['tools/m4-widget-native/fixture.cpp','tools/m4-widget-native/derive_fixture_v2.py','tools/m4-widget-native/fixture_v2.cpp',")
out=R/'tools/m4-widget-native/prepare_fixture_v2.py';assert not out.exists();out.write_text(s)
