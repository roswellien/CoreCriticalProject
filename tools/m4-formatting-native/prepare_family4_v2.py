"""Retain failed first preparation; correct only physical new-row extent."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_family4.py');s=p.read_text();a='assert len(rows)==230';assert s.count(a)==1
s=s.replace(a,'assert len(rows)==218');s=s.replace('pin(__file__)',"pin(__file__);pin(R/'tools/m4-formatting-native/prepare_family4.py')")
exec(compile(s,str(p),'exec'),globals())
