"""Actual isolated formatter controls writer; no archive consumer."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('run_fixture.py');s=p.read_text()
s=s.replace('Actual Runtime-selected isolated O0/O2 tree smoke; preparatory owner predicate and full source/control acceptance remain separate','Actual Runtime-selected formatter3 causal controls writer; independent validation is separate')
s=s.replace('selected_roots=1','selected_roots=3, control_scenarios=14, control_attempts_per_level=28')
s=s.replace('pin(__file__)','pin(__file__);pin(R/\'tools/m4-tree-review/run_fixture.py\')')
exec(compile(s,str(p),'exec'),globals())
