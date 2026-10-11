"""Same exact Context builder with explicit genuine hardware COFF input."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'build_connected_fixture_v2.py';text=parent.read_text()
# v2 assembles the frozen base dynamically, so append these bounded edits to
# the exact base source it already authenticates before invoking that source.
needle="exec(compile(text,str(parent),'exec'),globals())"
assert text.count(needle)==1
edit='''text=text.replace("writer=pin(R/", "run([llvm/'clang.exe','--target=x86_64-pc-windows-msvc','-c',prep/'connected_hardware_boundary.s','-o',out/'connected_hardware_boundary.obj'],'hardware-compile.log');hardware=pin(out/'connected_hardware_boundary.obj');writer=pin(R/",1)
text=text.replace("f'-DMW34_WRITER={writer}',", "f'-DMW34_WRITER={writer}',f'-DMW34_HARDWARE_OBJECT={hardware}',")
text=text.replace("pin(__file__);", "pin(__file__);pin(R/'tools/m4-mfc1168-native/build_connected_fixture_v3.py');pin(R/'tools/m4-mfc1168-native/build_connected_fixture_v3.ps1');",1)
'''
text=text.replace(needle,edit+needle);exec(compile(text,str(parent),'exec'),globals())
