"""Bind retained mixed MFC witness filename to the declared observer schema."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('compare_family_witnesses.py');s=p.read_text();a="records=rows(a,stem+'mfc-call-records.bin',32)if stem+'mfc-call-records.bin'in a.entries else rows(a,stem+'mfc-call-frames.bin',32)";assert s.count(a)==1;s=s.replace(a,"records=rows(a,stem+'mfc-allocation-witnesses.bin',32)")
s=s.replace("exec(compile(s,str(p),'exec'),globals())","s=s.replace('pin(__file__);',\"pin(__file__);pin(ROOT/'tools/m4-formatting-source/compare_family_witnesses.py');\");exec(compile(s,str(p),'exec'),globals())")
exec(compile(s,str(p),'exec'),globals())
