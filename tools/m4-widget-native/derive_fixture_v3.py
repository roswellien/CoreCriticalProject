"""The exact 482-object graph exceeds CreateProcess's command-line limit."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-widget-native/build_fixture.py';s=p.read_text()
s=s.replace("R/'tools/m4-widget-native/build_fixture.ps1'", "R/'tools/m4-widget-native/build_fixture_v2.ps1'")
old="worker=dst/'mw34_widget6.exe';run([clang,'--target=x86_64-pc-windows-msvc','-fms-runtime-lib=dll',*objects,*v['objects'],v['component_library'],'-o',worker,'-lbcrypt','-luser32','-lgdi32'],level+'-link');"
new="worker=dst/'mw34_widget6.exe';link_args=['--target=x86_64-pc-windows-msvc','-fms-runtime-lib=dll',*objects,*v['objects'],v['component_library'],'-o',worker,'-lbcrypt','-luser32','-lgdi32'];rsp=dst/'link.rsp';rsp.write_text('\\n'.join(subprocess.list2cmdline([str(a)])for a in link_args)+'\\n');files[str(rsp)]=sha(rsp);run([clang,'@'+str(rsp)],level+'-link');commands[-1]['expanded_response_arguments']=[str(a)for a in link_args];"
assert s.count(old)==1;s=s.replace(old,new)
p=R/'tools/m4-widget-native/build_fixture_v2.py';assert not p.exists();p.write_text(s)
p=R/'tools/m4-widget-native/build_fixture.ps1';s=p.read_text().replace("'build_fixture.py'","'build_fixture_v2.py'")
p=R/'tools/m4-widget-native/build_fixture_v2.ps1';assert not p.exists();p.write_text(s)
p=R/'tools/m4-widget-native/prepare_fixture_v2.py';s=p.read_text()
s=s.replace("'tools/m4-widget-native/build_fixture.py','tools/m4-widget-native/build_fixture.ps1'", "'tools/m4-widget-native/build_fixture.py','tools/m4-widget-native/build_fixture.ps1','tools/m4-widget-native/build_fixture_v2.py','tools/m4-widget-native/build_fixture_v2.ps1','tools/m4-widget-native/derive_fixture_v3.py'")
p=R/'tools/m4-widget-native/prepare_fixture_v3.py';assert not p.exists();p.write_text(s)
