from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'prepare_connected_fixture.py';text=parent.read_text()
a="v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p"
b="v=sha(p);assert h is None or h==v,(p,h,v);assert p.is_relative_to(out)or str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p"
assert text.count(a)==1;text=text.replace(a,b)
text=text.replace("for p in (Path(__file__),Path(sys.executable),", "pin(parent)\n  for p in (Path(__file__),Path(sys.executable),")
exec(compile(text,str(parent),'exec'),globals())
