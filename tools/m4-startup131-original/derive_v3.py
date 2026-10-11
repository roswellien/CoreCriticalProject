from pathlib import Path
import json,hashlib,sys
sys.dont_write_bytecode=True
T=Path(__file__).resolve().parent;R=T.parents[1]
old=R/'tools/m4-constructor-original/prerequisite_observer.hpp';h=T/'prerequisite_observer_v2.hpp'
assert not h.exists()
s=old.read_text();assert s.count('auto*owner=')==1
s=s.replace('auto*owner=','auto*allocation_occurrence=').replace('owner!=nullptr','allocation_occurrence!=nullptr').replace('owner->','allocation_occurrence->')
h.write_text(s)
base=T/'prepare_v2.py';p=T/'prepare_v3.py';assert not p.exists()
s=base.read_text();needle="R/'tools/m4-constructor-original/prerequisite_observer.hpp'";assert s.count(needle)==1
s=s.replace(needle,"T/'prerequisite_observer_v2.hpp'");p.write_text(s)
q=T/'preparation-v3-lineage.json';q.write_text(json.dumps(dict(base=str(base),base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),header_base=str(old),header_base_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),new_header=str(h),new_header_sha256=hashlib.sha256(h.read_bytes()).hexdigest(),generated=str(p),generated_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),change='Rename local owner to allocation_occurrence to preserve /W4 /WX without shadowing existing imported entry global; observation bytes and logic unchanged',failed_build='reports/m4-startup131-original/build-r1/build.json'),indent=2)+'\n')
print(p)
