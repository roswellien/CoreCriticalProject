"""Compile the single138 Context with its exact sorted58-body library.

Uses the current131 compiler/ASM/writer dependency capture without execution.
"""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
parent=R/'tools/m4-joint-startup131/build_v2.py'
raw=parent.read_text();text=raw
text=text.replace("R/'reports/m4-joint-startup131'/name","R/'reports/m4-joint-startup138'/name")
text=text.replace('mw34_joint_startup131.exe','mw34_joint_startup138.exe')
text=text.replace("f'-DMW34_HARDWARE_OBJECT={hardware}',","f'-DMW34_HARDWARE_OBJECT={hardware}',f'-DMW34_WIDGET_LIBRARY={p[\"widget_libraries\"][level]}',f'-DMW34_WIDGET_INCLUDE={p[\"widget_component_include\"]}',")
text=text.replace('Full131 persistent Context compiled O0/O2 with410 reused literalobjects,101callbacks/132translations/134selectedcalls; no worker execution','Full138 single persistent Context compiled O0/O2 with410 parent +58 sorted widget literalobjects,108callbacks/139translations/141selectedcalls; no worker execution')
text=text.replace("pin(R/'tools/m4-joint-startup131/build_v2.ps1');","pin(R/'tools/m4-joint-startup131/build_v2.ps1');pin(R/'tools/m4-joint-startup138/build.py');pin(R/'tools/m4-joint-startup138/build.ps1');")
assert text!=raw and 'MW34_WIDGET_LIBRARY'in text
exec(compile(text,str(parent),'exec'),globals())
