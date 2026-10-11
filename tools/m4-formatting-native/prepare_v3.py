"""Preserve the inherited source page permission mapping in additive manifest."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_v2.py');s=p.read_text();a="exec(compile(s,str(p),'exec'),globals())";assert s.count(a)==1
s=s.replace(a,"s=s.replace(\"sorted(set(parent['source_pages'])|{0x78022000,0x78026000})\",\"parent['source_pages']|{str(0x78022000):5,str(0x78026000):5}\")\ns=s.replace(\"pin(R/'tools/m4-formatting-native/prepare.py')\",\"pin(R/'tools/m4-formatting-native/prepare.py');pin(R/'tools/m4-formatting-native/prepare_v2.py')\")\n"+a)
exec(compile(s,str(p),'exec'),globals())
