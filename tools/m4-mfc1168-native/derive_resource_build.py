from pathlib import Path
import hashlib
p=Path(__file__).parent;s=(p/'build_fixture_v2.py').read_text()
s=s.replace("  for level in('O0','O2'):", "  run([llvm/'clang.exe','--target=x86_64-pc-windows-msvc','-c',prep/'hardware_boundary.s','-o',out/'hardware_boundary.obj'],'hardware-compile.log');pin(out/'hardware_boundary.obj');pin(llvm/'clang-cl.exe');pin(ninja);pin(R/'tools/m4-mfc1168-native/derive_resource_build.py');pin(R/'tools/m4-mfc1168-native/build_resource_fixture.ps1')\n  for level in('O0','O2'):")
s=s.replace("f'-DMW34_OBJECTS={", "f'-DMW34_HARDWARE_OBJECT={out}/hardware_boundary.obj',f'-DMW34_OBJECTS={")
(p/'build_resource_fixture.py').write_text(s);print(hashlib.sha256((p/'build_resource_fixture.py').read_bytes()).hexdigest())
