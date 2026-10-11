"""Add the Runtime image-loader include after the retained failed compile."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'build_connected_interface.py';s=parent.read_text()
s=s.replace("includes=[prep,R/'tools/m4-runtime',R/'runtime'", "includes=[prep,R/'tools/m4-runtime',R/'tools/m4-startup',R/'runtime'")
s=s.replace("for p in (Path(__file__),", "for p in (parent,R/'tools/m4-mfc1168-native/build_connected_interface_v2.ps1',Path(__file__),")
exec(compile(s,str(parent),'exec'),globals())
