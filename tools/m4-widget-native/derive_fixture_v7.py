"""Use a single current Session class in retained caller adapters."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-widget-native/fixture_v3.cpp';s=p.read_text()
old='#include "D:/Projects/MW34Recomp/reports/m4-joint-startup130/preparation-r2/native_main.cpp"'
assert s.count(old)==1;s=s.replace(old,'#include "inherited_main.cpp"')
p=R/'tools/m4-widget-native/fixture_v4.cpp';assert not p.exists();p.write_text(s)
p=R/'tools/m4-widget-native/prepare_fixture_v6.py';s=p.read_text().replace('tools/m4-widget-native/fixture_v3.cpp','tools/m4-widget-native/fixture_v4.cpp')
s=s.replace("'tools/m4-widget-native/derive_fixture_v6.py'", "'tools/m4-widget-native/derive_fixture_v6.py','tools/m4-widget-native/fixture_v3.cpp','tools/m4-widget-native/derive_fixture_v7.py'")
old="shutil.copyfile(R/'tools/m4-widget-native/fixture_v4.cpp',out/'fixture.cpp');levels={}"
new="""shutil.copyfile(R/'tools/m4-widget-native/fixture_v4.cpp',out/'fixture.cpp')
 inherited=bind('reports/m4-joint-startup130/preparation-r2/native_main.cpp');text=inherited.read_text();need(text.count('#include "onexit_session.hpp"')==1,'One exact inherited Session alias');text=text.replace('#include "onexit_session.hpp"','#include "'+(Path(services['native_include'])/'session.hpp').as_posix()+'"');(out/'inherited_main.cpp').write_text(text);levels={}\n"""
assert s.count(old)==1;s=s.replace(old,new)
p=R/'tools/m4-widget-native/prepare_fixture_v7.py';assert not p.exists();p.write_text(s)
