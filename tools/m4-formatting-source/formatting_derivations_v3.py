"""Join all sixteen raw FS words at their literal source commit boundaries."""
from pathlib import Path
p=Path(__file__).with_name('formatting_derivations_v2.py')
s=p.read_text()
# The inherited adapter executes the retained base literal comparer. Tighten that
# base code before execution, without changing either frozen predecessor.
a="exec(compile(s,str(p),'exec'),globals())"
assert s.count(a)==1
b="""old=\"w=matches[0];need(w[:8]==(1,w[1],frame['index'],root,point,ev['PC'],ESP-12,12)and w[8:11]==raw and w[15]==0,'Actual complete12B mixed raw predecessor/handler/scope relation')\"
new=\"w=matches[0];expected_raw=(1,w[1],frame['index'],root,point,ev['PC'],ESP-12,12,*raw,ev['source_access_index']+int(point==84),read['before_head'],frame['depth']+int(point==84),0xffffffff,0);equal(w,expected_raw,'Whole16Q raw mixed FS source ledger/head/depth/sentinel relation')\"
assert s.count(old)==1;s=s.replace(old,new)
old=\"active=[];findex=0;sourceframes=[];specs=\"
new=\"need(all(w[1]==i for i,w in enumerate(raw_frames)),'Physical raw FS row ordinals contiguous');active=[];findex=0;sourceframes=[];specs=\"
assert s.count(old)==1;s=s.replace(old,new)
exec(compile(s,str(p),'exec'),globals())"""
s=s.replace(a,b)
exec(compile(s,str(p),'exec'),globals())
