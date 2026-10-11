"""Retain literal provider dependencies through the frozen caller definitions."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-widget-native/fixture_v2.cpp';s=p.read_text()
prefix='''// Retain the actual frozen source adapters required by the 427 linked COFFs.
// This renamed inherited main is never called by the six-root fixture.
#define main mw34_widget_unused_inherited_main
#define need mw34_widget_unused_inherited_need
#include "D:/Projects/MW34Recomp/reports/m4-joint-startup130/preparation-r2/native_main.cpp"
#undef need
#undef main
'''
p=R/'tools/m4-widget-native/fixture_v3.cpp';assert not p.exists();p.write_text(prefix+s)
p=R/'tools/m4-widget-native/build_fixture_v3.py';s=p.read_text()
s=s.replace("clang=LLVM/'clang++.exe'", "clang=LLVM/'clang++.exe';link=LLVM/'lld-link.exe'")
s=s.replace("for p in [clang,", "for p in [clang,link,").replace("R/'tools/m4-widget-native/build_fixture_v3.ps1'", "R/'tools/m4-widget-native/build_fixture_v4.ps1'")
old="link_args=['--target=x86_64-pc-windows-msvc','-fms-runtime-lib=dll',*objects,*v['objects'],v['component_library'],'-o',worker,'-lbcrypt','-luser32','-lgdi32']"
new="link_args=['/subsystem:console','/defaultlib:msvcrt','/defaultlib:oldnames',*objects,*v['objects'],v['component_library'],'/out:'+str(worker),'bcrypt.lib','user32.lib','gdi32.lib']"
assert s.count(old)==1;s=s.replace(old,new).replace("run([clang,'@'+str(rsp)],level+'-link')", "run([link,'@'+str(rsp)],level+'-link')")
p=R/'tools/m4-widget-native/build_fixture_v4.py';assert not p.exists();p.write_text(s)
p=R/'tools/m4-widget-native/build_fixture_v3.ps1';s=p.read_text().replace("'build_fixture_v3.py'","'build_fixture_v4.py'")
p=R/'tools/m4-widget-native/build_fixture_v4.ps1';assert not p.exists();p.write_text(s)
p=R/'tools/m4-widget-native/prepare_fixture_v4.py';s=p.read_text().replace('tools/m4-widget-native/fixture_v2.cpp','tools/m4-widget-native/fixture_v3.cpp')
s=s.replace("'tools/m4-widget-native/derive_fixture_v4.py'", "'tools/m4-widget-native/derive_fixture_v4.py','tools/m4-widget-native/fixture_v2.cpp','tools/m4-widget-native/build_fixture_v4.py','tools/m4-widget-native/build_fixture_v4.ps1','tools/m4-widget-native/derive_fixture_v5.py','reports/m4-joint-startup130/preparation-r2/native_main.cpp'")
p=R/'tools/m4-widget-native/prepare_fixture_v5.py';assert not p.exists();p.write_text(s)
