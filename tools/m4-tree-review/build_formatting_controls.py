"""Retain the reviewed actual tree fixture builder for formatter controls."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('build_fixture.py');s=p.read_text()
s=s.replace("tree/'mw34_joint_startup124.exe'","tree/'mw34_joint_startup125.exe'").replace('isolated actual Runtime-selected tree fixture','isolated actual Runtime-selected formatter3 causal fixture')
s=s.replace('pin(__file__);','pin(__file__);pin(R/\'tools/m4-tree-review/build_fixture.py\');')
exec(compile(s,str(p),'exec'),globals())
