"""Freeze exact reached-PC guards and specify their bridge-boundary scope."""
from pathlib import Path
import hashlib
BASE=Path(__file__).with_name('prepare_fixture.py')
SHA='9311e374f4624fefafd9762efe2988efff30defc66c7104858c14c2d72a1d1b3'
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==SHA
text=BASE.read_text()
before="ROOT/'tools/m4-hypot-native/fixture.cpp'"
assert text.count(before)==1
text=text.replace(before,"ROOT/'tools/m4-hypot-native/fixture_v2.cpp'")
before="        prefix=['#pragma once','#include <array>',"
assert text.count(before)==1
text=text.replace(before,"        observed=json.loads(pin(trace/'actual-source-traces.json').read_bytes())\n        reached=sorted(map(int,observed[0]['actual_reached_PC_counts']))\n        assert len(reached)==439 and all(sorted(map(int,t['actual_reached_PC_counts']))==reached for t in observed)\n"+before)
before="            'inline constexpr const char *root_sha="
assert text.count(before)==1
text=text.replace(before,"            'inline bool reached_PC(unsigned pc){switch(pc){'+''.join('case '+str(p)+'U:' for p in reached)+'return true;default:return false;}}',\n"+before)
before='        pin(__file__);pin(sys.executable)'
assert text.count(before)==1
text=text.replace(before,"        pin(BASE,SHA);pin(ROOT/'tools/m4-hypot-native/derive_fixture_v2.py')\n"+before)
before="            unknown_cold_domain_denied=True,undefined_flags="
assert text.count(before)==1
text=text.replace(before,"            unknown_callbacks_and_fragments_denied=True,reached_source_PC_guard='Every native bridge; not an every-instruction observer',\n            existing_unreached_decoded_PCs=233,cold_source_execution_equivalence_claimed=False,undefined_flags=")
exec(compile(text,str(BASE),'exec'),globals())
