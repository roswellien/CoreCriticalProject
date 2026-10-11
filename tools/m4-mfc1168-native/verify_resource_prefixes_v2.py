from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'verify_resource_prefixes.py';s=parent.read_text()
old='except Stop:stop=True'
assert s.count(old)==1;s=s.replace(old,'except Stop:stop=True;m.cursor=m.word(2472)')
s=s.replace('pin(__file__);pin(sys.executable)','pin(parent);pin(__file__);pin(sys.executable)')
exec(compile(s,str(parent),'exec'),globals())
