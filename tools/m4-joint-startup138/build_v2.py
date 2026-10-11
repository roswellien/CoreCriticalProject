"""Direct derivative of the frozen compiler/dependency-capturing builder."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
parent=R/'tools/m4-mfc1168-native/build_connected_fixture.py'
text=parent.read_text()
text=text.replace("R/'reports/m4-mfc1168-native'/name","R/'reports/m4-joint-startup138'/name")
text=text.replace("writer=pin(R/'reports/m4-capture-direct/build-r5/capture_direct.lib');", "writer_receipt=pin(R/'reports/m4-capture-direct/build-r4/build.json','909955901c310e5fcf5eb0713e48a20bf896d13ea335e9d8093dec25ba232e96');wr=json.loads(writer_receipt.read_bytes());assert wr['passed'];[pin(q,h)for q,h in (wr['sources']|wr['objects']).items()];")
text=text.replace("tree=out/('build-'+level);flags=", "run([llvm/'clang.exe','--target=x86_64-pc-windows-msvc','-c',prep/'connected_hardware_boundary.s','-o',out/'connected_hardware_boundary.obj'],'hardware-compile.log');hardware=pin(out/'connected_hardware_boundary.obj');writer=pin(R/('reports/m4-capture-direct/build-r4/capture_direct-'+level+'.obj'));tree=out/('build-'+level);flags=")
text=text.replace("f'-DMW34_WRITER={writer}',", "f'-DMW34_WRITER={writer}',f'-DMW34_HARDWARE_OBJECT={hardware}',f'-DMW34_WIDGET_LIBRARY={p[\"widget_libraries\"][level]}',f'-DMW34_WIDGET_INCLUDE={p[\"widget_component_include\"]}',")
text=text.replace('mw34_mfc1168_connected.exe','mw34_joint_startup138.exe')
text=text.replace("pin(__file__);pin(R/'tools/m4-mfc1168-native/build_connected_fixture.ps1');", "pin(__file__);pin(parent);pin(R/'tools/m4-mfc1168-native/build_connected_fixture.ps1');pin(R/'tools/m4-joint-startup131/build_v2.py');pin(R/'tools/m4-joint-startup138/build_v2.py');pin(R/'tools/m4-joint-startup138/build_v2.ps1');")
text=text.replace('Current130 derived connected14 prefix Context compiled O0/O2 with410 literal objects; no worker execution','Full138 single persistent Context compiled O0/O2 with410 parent +58 sorted widget literalobjects,108callbacks/139translations/141selectedcalls; no worker execution')
exec(compile(text,str(parent),'exec'),globals())
