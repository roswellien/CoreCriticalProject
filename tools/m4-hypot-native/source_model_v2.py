"""Retain the first literal model and add architectural CW normalization."""
from pathlib import Path
import hashlib
BASE=Path(__file__).with_name('source_model.py')
raw=BASE.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='179f954df6504f0d9297d671af63e89b4ae948bf0fd3cc4b50d4a982f84d8b51'
text=raw.decode()
old='self.cw = value\n'
assert text.count(old)==1
text=text.replace(old,'self.cw = (value & 0x1f3f) | 0x40\n')
exec(compile(text,str(BASE),'exec'),globals())
