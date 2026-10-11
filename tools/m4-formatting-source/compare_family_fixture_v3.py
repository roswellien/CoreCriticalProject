"""Exact cleanup owner roles, distinct from equal-sized formatter allocations."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('compare_family_fixture.py');s=p.read_text()
a='machine.invoke_external(0x5f401770';assert s.count(a)==1;s=s.replace(a,'machine.invoke_external(0x5f401782')
a="if allocation['requested']not in(12,24)or allocation['guest']==responses.allocations[0]['guest']or not allocation['live']:continue";assert s.count(a)==1;s=s.replace(a,"if allocation['guest']not in{owner['guest']for owner in mixed}:continue")
s=s.replace("s=s.replace('formatter3','formatter4')","s=s.replace('formatter3','formatter4');s=s.replace(\"pin(ROOT/'tools/m4-formatting-source/compare_native_fixture_v9.py')\",\"pin(ROOT/'tools/m4-formatting-source/compare_native_fixture_v9.py');pin(ROOT/'tools/m4-formatting-source/compare_family_fixture.py')\")")
exec(compile(s,str(p),'exec'),globals())
