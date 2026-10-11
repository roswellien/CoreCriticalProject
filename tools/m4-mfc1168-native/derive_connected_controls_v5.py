"""Mutate two readonly IAT cells before entering the actual Runtime callback.

The original protection is restored. All twelve refusal, poison, retry and
cleanup predicates remain identical to the diagnostic worker.
"""
from pathlib import Path
import hashlib
p=Path(__file__).parent
source=p/'connected_controls_v4.inc'
assert hashlib.sha256(source.read_bytes()).hexdigest()=='2b8931061e2289c489bddaed7454032d2a3b1ee4a8f5b295469d91c136aabcfe'
text=source.read_text()
for old,new in [
 ('case 3:scalar(0x5f498330,0);break;', 'case 3:r.memory().protect({0x5f498000},mw34::Permissions::read|mw34::Permissions::write);scalar(0x5f498330,0);r.memory().protect({0x5f498000},mw34::Permissions::read);break;'),
 ('case 9:scalar(0x7802e0c8,0);break;', 'case 9:r.memory().protect({0x7802e000},mw34::Permissions::read|mw34::Permissions::write);scalar(0x7802e0c8,0);r.memory().protect({0x7802e000},mw34::Permissions::read);break;')]:
 assert text.count(old)==1;text=text.replace(old,new)
target=p/'connected_controls_v5.inc';assert not target.exists();target.write_text(text)
print(hashlib.sha256(target.read_bytes()).hexdigest())
