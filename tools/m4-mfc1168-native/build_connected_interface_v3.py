"""Retain Remill's documented literal-operator deprecation as a warning."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;v2=p/'build_connected_interface_v2.py';text=v2.read_text()
text=text.replace("exec(compile(s,str(parent),'exec'),globals())", "s=s.replace(\"'/WX',opt\",\"'/WX','/clang:-Wno-error=deprecated-literal-operator',opt\")\ns=s.replace(\"for p in (parent,\",\"for p in (v2,R/'tools/m4-mfc1168-native/build_connected_interface_v3.ps1',parent,\")\nexec(compile(s,str(parent),'exec'),globals())")
exec(compile(text,str(v2),'exec'),globals())
