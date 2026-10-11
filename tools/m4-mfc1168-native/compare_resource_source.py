"""Preserved complete literal comparator with declared BEFORE relocation input."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'compare_fixture.py';s=parent.read_text()
old="contracts=read(Path(prep['native_contracts']).parent/'contracts.json')"
assert s.count(old)==1;s=s.replace(old,"contracts=read(prep['relocated_contracts']);pin(parent)")
s=s.replace("four typed native TLS/CS/GetACP seams'", "four typed native TLS/CS/GetACP seams; five disjoint relocated BEFORE borrowed owners'")
exec(compile(s,str(parent),'exec'),globals())
