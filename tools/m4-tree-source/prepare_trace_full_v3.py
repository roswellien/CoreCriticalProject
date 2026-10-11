"""Correct raw physical versus canonical named importer field orientation."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
base=ROOT/'tools/m4-tree-source/compare_trace_full_v2.py'
target=base.with_name('compare_trace_full_v3.py');assert not target.exists()
s=base.read_text()
for before,after in [
 ("if address==slot:need(value==raw,'Physical owning MFC import before named source projection');value=target", "if address==slot:need(value==target,'Physical owning MFC import before named source projection');value=raw"),
 ('0x5bb530:(0x780011be,0x1deca2)', '0x5bb530:(0x78002fe5,0x1deca2),0x5bb4bc:(0x5f401ea0,0x80000337),0x5bb670:(0x78010a6d,0x1df886),0x5bb4fc:(0x780c10f0,0x1df59c)')]:
    assert s.count(before)==1;s=s.replace(before,after)
target.write_text(s)
