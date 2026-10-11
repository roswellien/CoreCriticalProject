from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[2]
old=ROOT/'tools/m4-container-source/loader_identity.py';new=ROOT/'tools/m4-container-source/loader_identity_v2.py'
assert not new.exists()
s=old.read_text().replace("read_text(encoding='utf-8-sig')","read_text(encoding='utf-16')")
compile(s,str(new),'exec');new.write_text(s)
print(hashlib.sha256(new.read_bytes()).hexdigest())
