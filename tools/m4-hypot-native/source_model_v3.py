"""Derive lazy FXSW serialization and literal final rounding-bit mapping."""
from pathlib import Path
import hashlib
BASE=Path(__file__).with_name('source_model.py')
raw=BASE.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='179f954df6504f0d9297d671af63e89b4ae948bf0fd3cc4b50d4a982f84d8b51'
text=raw.decode()
changes=[
 ('self.cw = value\n','self.cw = (value & 0x1f3f) | 0x40\n'),
 ('self.last_fp = None','self.last_serialized_sw = struct.unpack_from(\'<H\', self.state, 2770)[0]\n            self.last_fp = None'),
 ("self.reg('ax', seam['value'])","self.reg('ax', seam['value'])\n                self.last_serialized_sw = seam['value']"),
 ("(before_sw & ~0x3800) | (observed_sw & 0x3800)","(self.last_serialized_sw & ~0x3800) | (observed_sw & 0x3800)"),
]
for old,new in changes:
    assert text.count(old)==1
    text=text.replace(old,new)
exec(compile(text,str(BASE),'exec'),globals())
