"""Exclude receipt metadata from compiled source conservation inventory."""
from pathlib import Path
import hashlib
V7=Path(__file__).with_name('review_widget_prelaunch_v7.py')
V7_SHA='8fb0dbaa6b9316acd3e884de6e8786aa967f3e551d7cadd787dde617152ebf94'
if hashlib.sha256(V7.read_bytes()).hexdigest()!=V7_SHA:raise ValueError('Immutable reservation review')
source=V7.read_text()
for old,new in [("old_file.name=='report.json'","old_file.name in ('report.json','pins.json')"),("'reservation_size=0x10000'","'reservation_size=65536'")]:
    if source.count(old)!=1:raise ValueError('Exactly one explicit metadata/literal adjustment')
    source=source.replace(old,new,1)
anchor="        pin(V5,V5_SHA)"
if source.count(anchor)!=1:raise ValueError('One current additive code edge')
source=source.replace(anchor,anchor+'\n        pin(V7,V7_SHA)',1)
exec(compile(source,str(V7),'exec'),globals())
