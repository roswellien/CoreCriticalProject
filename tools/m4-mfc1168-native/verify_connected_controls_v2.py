"""Exact connected-entry source reason; preserve the failed first checker."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'verify_connected_controls.py';text=parent.read_text()
old="1:'Flat32'";assert text.count(old)==1;text=text.replace(old,"1:'source segment/entry identity'")
old="12:'Flat32'";assert text.count(old)==1;text=text.replace(old,"12:'source segment/entry identity'")
text=text.replace('pin(__file__);pin(sys.executable)',"pin(p/'verify_connected_controls_v2.py');pin(parent);pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())
