"""Correct the PE helper's documented offset/backing-end result interpretation."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-fs-control-audit/audit_v4.py';s=p.read_text()
a="offset,size=game.rva_range(ins['pc']-game.image_base,ins['width']);need(game.read(offset,size)"
b="offset,backing_end=game.rva_range(ins['pc']-game.image_base,ins['width']);need(offset+ins['width']<=backing_end and game.read(offset,ins['width'])"
assert s.count(a)==1;s=s.replace(a,b);t=p.with_name('audit_v5.py');assert not t.exists();t.write_text(s)
