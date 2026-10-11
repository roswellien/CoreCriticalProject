"""Bind the actual three typed reserve/adoption predicates in the broker."""
from pathlib import Path
import hashlib
V8=Path(__file__).with_name('review_widget_prelaunch_v8.py')
V8_SHA='9a1e03ca826fe291d60c86e3570a3e97a0ef29dadf5b78746e15a7e2eaff9ee8'
if hashlib.sha256(V8.read_bytes()).hexdigest()!=V8_SHA:raise ValueError('Immutable finite reservation source review')
program=V8.read_text()
anchor="exec(compile(source,str(V7),'exec'),globals())"
if program.count(anchor)!=1:raise ValueError('One inherited reviewer invocation')
transform=r'''
old="new_broker.count('MEM_RESERVE')>=4"
new="new_broker.count('MEM_RESERVE')==3 and 'for(const auto base:bases)validate_reserved(base);' in new_broker and 'info.AllocationProtect==PAGE_NOACCESS' in new_broker"
if source.count(old)!=1:raise ValueError('Actual three reserve/adoption checks')
source=source.replace(old,new,1)
old='        pin(V7,V7_SHA)'
if source.count(old)!=1:raise ValueError('One current immutable code edge')
source=source.replace(old,old+'\n        pin(V8,V8_SHA)',1)
exec(compile(source,str(V7),'exec'),globals())
'''
program=program.replace(anchor,transform,1)
exec(compile(program,str(V8),'exec'),globals())
