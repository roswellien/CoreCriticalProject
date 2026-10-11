"""Run the isolated additive controls, retaining any genuine candidate fault."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
source=Path(__file__).resolve().parents[1]/'m4-vtable-controls/capture.py'
s=source.read_text(encoding='utf-8')
s=s.replace("BASE=ROOT/'reports/m4-vtable-controls'","BASE=ROOT/'reports/m4-lockit-review'")
exec(compile(s,str(source),'exec'),globals())
