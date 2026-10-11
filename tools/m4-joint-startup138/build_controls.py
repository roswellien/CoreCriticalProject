"""Compile the ordinary current Context refusal worker; no execution."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
wrapper=R/'tools/m4-joint-startup138/build_v2.py';text=wrapper.read_text();text=text.replace("text=text.replace('mw34_mfc1168_connected.exe','mw34_joint_startup138.exe')","text=text.replace('mw34_mfc1168_connected.exe','mw34_widget_context_controls.exe')")
text=text.replace("exec(compile(text,str(parent),'exec'),globals())","text=text.replace('Full138 single persistent Context compiled O0/O2 with410 parent +58 sorted widget literalobjects,108callbacks/139translations/141selectedcalls; no worker execution','Current shared138 Context eight ordinary refusal modes compiled O0/O2; after owned-font prefix, same Context retry, actual font/registry failure cleanup; no execution');text=text.replace('pin(sys.executable);os.environ',\"pin(R/'tools/m4-joint-startup138/build_controls.py');pin(R/'tools/m4-joint-startup138/build_controls.ps1');pin(sys.executable);os.environ\");exec(compile(text,str(parent),'exec'),globals())")
exec(compile(text,str(wrapper),'exec'),globals())
