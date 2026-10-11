from pathlib import Path
import hashlib
p=Path(__file__).parent
s=(p/'fixture.cpp').read_text().replace('#include "runtime.hpp"','#include "runtime.hpp"\n#include "admission.hpp"')
(p/'fixture_v2.cpp').write_text(s)
t=(p/'prepare_fixture.py').read_text().replace("raw(R/'tools/m4-mfc1168-native/fixture.cpp')", "raw(R/'tools/m4-mfc1168-native/fixture_v2.cpp')")
t=t.replace("for q in remill.rglob('*.h'):pin(q)", "for q in remill.rglob('*.h'):pin(q)\n  for q in(R/'tools/m4-startup/admission.hpp',R/'tools/m4-runtime/service_provider.hpp',R/'tools/m4-mfc1168-native/fixture.cpp',R/'tools/m4-mfc1168-native/prepare_fixture.py',R/'tools/m4-mfc1168-native/derive_fixture_v2.py'):pin(q)")
(p/'prepare_fixture_v2.py').write_text(t);print(hashlib.sha256((p/'prepare_fixture_v2.py').read_bytes()).hexdigest())
