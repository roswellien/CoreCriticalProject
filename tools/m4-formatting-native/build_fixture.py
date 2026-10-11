"""Fresh isolated formatting fixture compilation, retaining accepted builder."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parents[1]/'m4-tree-review/build_fixture.py';s=p.read_text();s=s.replace("R/'reports/m4-tree-review'/name","R/'reports/m4-formatting-native'/name").replace("tree/'mw34_joint_startup124.exe'","tree/'mw34_joint_startup125.exe'").replace('isolated actual Runtime-selected tree fixture','isolated actual Runtime-selected formatting3 fixture');s=s.replace('pin(__file__);','pin(__file__);pin(R/\'tools/m4-tree-review/build_fixture.py\');')
exec(compile(s,str(p),'exec'),globals())
