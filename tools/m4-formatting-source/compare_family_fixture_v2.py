"""Keep failed comparison; bind literal MFC825 entry to its physical 5F401782."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('compare_family_fixture.py');s=p.read_text();a='machine.invoke_external(0x5f401770';assert s.count(a)==1;s=s.replace(a,'machine.invoke_external(0x5f401782')
s=s.replace("s=s.replace('formatter3','formatter4')","s=s.replace('formatter3','formatter4');s=s.replace('pin(__file__)\\n  for p in list(READS)',\"pin(__file__);pin(ROOT/'tools/m4-formatting-source/compare_family_fixture.py')\\n  for p in list(READS)\")")
exec(compile(s,str(p),'exec'),globals())
