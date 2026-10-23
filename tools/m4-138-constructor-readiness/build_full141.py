"""Exact namespace/constructor-link extension of existing full138 builder."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
parent=R/'tools/m4-joint-startup138/build_v2.py';source=parent.read_text()
changes=[("R/'reports/m4-joint-startup138'/name","R/'reports/m4-startup141-runway'/name"),
 ('mw34_joint_startup138.exe','mw34_joint_startup141.exe'),
 ('''f'-DMW34_WIDGET_INCLUDE={p[\\"widget_component_include\\"]}',"''','''f'-DMW34_WIDGET_INCLUDE={p[\\"widget_component_include\\"]}',f'-DMW34_CONSTRUCTOR_LIBRARY={p[\\"constructor_libraries\\"][level]}',"'''),
 ('Full138 single persistent Context compiled O0/O2 with410 parent +58 sorted widget literalobjects,108callbacks/139translations/141selectedcalls; no worker execution','Full141 single persistent Context compiled O0/O2 with410 parent+58widget+33constructor literals,111callbacks/142translations/144selectedcalls; no worker execution')]
for before,after in changes:
 assert source.count(before)==1,(before,source.count(before));source=source.replace(before,after,1)
assert 'MW34_CONSTRUCTOR_LIBRARY'in source
exec(compile(source,str(parent),'exec'),globals())
