"""Repair pressure observer dependency and exact three-argument writer calls."""
from pathlib import Path
H=Path(__file__).parent
def copy(name,old,changes):
 p=H/name;s=(H/old).read_text()
 for a,b in changes:assert s.count(a)>=1,(old,a);s=s.replace(a,b)
 if p.exists():assert p.read_text()==s;return
 p.write_text(s)
copy('fixture_hooks_v4.hpp','fixture_hooks_v3.hpp',[
 ('#pragma once','#pragma once\n#include "D:/Projects/MW34Recomp/tools/m4-crt-commandline-native/host_input.hpp"')])
copy('fixture_v5.inc','fixture_v4.inc',[
 ('fixture_hooks_v3.hpp','fixture_hooks_v4.hpp'),
 ('w.append(prefix+"-pressure.bin",std::as_bytes(std::span(mw34_onexit_review::pressure_rows)));',
  'w.append(prefix+"-pressure.bin",mw34_onexit_review::pressure_rows.data(),mw34_onexit_review::pressure_rows.size()*sizeof(mw34_onexit_review::pressure_rows[0]));'),
 ('w.append(id+".bin",std::as_bytes(std::span(v)));w.append(id+"-module-path.bin",std::as_bytes(std::span(a.module_path)));w.append(id+"-module-sha.bin",std::as_bytes(std::span(a.module_sha)));',
  'w.append(id+".bin",v.data(),sizeof(v));w.append(id+"-module-path.bin",a.module_path.data(),a.module_path.size()*sizeof(wchar_t));w.append(id+"-module-sha.bin",a.module_sha.data(),a.module_sha.size());')])
copy('build_controls_v6.py','build_controls_v5.py',[
 ('fixture_v4.inc','fixture_v5.inc'),('fixture_hooks_v3.hpp','fixture_hooks_v4.hpp'),
 ("for pp,h in pins.items():assert sha(pp)==h,(pp,h)",
  "pin(HERE/'prepare_controls_v5.py');pin(HERE/'prepare_controls_v6.py');pin(ROOT/'tools/m4-crt-commandline-native/host_input.hpp');pin(ROOT/'tools/m4-crt-commandline-native/provider.hpp')\n        for pp,h in pins.items():assert sha(pp)==h,(pp,h)")])
copy('build_controls_v6.ps1','build_controls_v5.ps1',[('build_controls_v5.py','build_controls_v6.py')])
print('Derived fresh dependency-corrected control build')
