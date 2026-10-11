"""Actual bounded compiled four-root runs, unchanged canonical writer/reader."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parents[1]/'m4-tree-review/run_fixture.py';s=p.read_text();s=s.replace("R/'reports/m4-tree-review'/name","R/'reports/m4-formatting-native'/name").replace('isolated O0/O2 tree smoke','isolated O0/O2 formatting4 smoke').replace('selected_roots=1','selected_roots=4');s=s.replace('pin(__file__)',"pin(__file__);pin(R/'tools/m4-tree-review/run_fixture.py')")
exec(compile(s,str(p),'exec'),globals())
