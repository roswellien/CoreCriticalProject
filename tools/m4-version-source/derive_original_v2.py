"""Preserve original compile failure; remove two strict MSVC shadow warnings."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
p=P/'original_observer_v1.hpp';s=p.read_text();a=s.index('static void version_owner(');b=s.index('\nextern "C" void version_observe',a);part=s[a:b]
for x,y in [('*owner{}','*allocation_owner{}'),('owner=&version_allocations','allocation_owner=&version_allocations'),('require(owner,','require(allocation_owner,'),('(*owner)','(*allocation_owner)')]:
 assert x in part;part=part.replace(x,y)
s=s[:a]+part+s[b:];q=P/'original_observer_v2.hpp';assert not q.exists();q.write_text(s)
p=P/'prepare_original_v1.py';s=p.read_text();s=once(s,"T/'original_observer_v1.hpp'","T/'original_observer_v2.hpp'")
a='for(unsigned i=0;i<3;++i)if(version_IATs[i]<=pc&&pc<version_IATs[i]+4){require(actual[byte]==reinterpret_cast<const unsigned char*>(&version_targets[i])[pc-version_IATs[i]]'
b=a.replace('unsigned i=','unsigned version_i=').replace('i<3','version_i<3').replace('++i','++version_i').replace('[i]','[version_i]')
s=once(s,a,b)
s=once(s,"  for p in [T/'prepare_original_v1.py'","  pin(T/'derive_original_v2.py');pin(R/'reports/m4-version-source/original-preparation-r1/report.json','3306f5c18b5d53180ab6ab9d6ebbbb9279ccf6ff53b0e58277a774df41bd04d8');pin(R/'reports/m4-version-source/original-build-r1/build.json','bd6c971bf1f4c490164982a0e76859fedaafbf18a57177777bced3973caadfce');pin(T/'original_observer_v1.hpp','"+sha(P/'original_observer_v1.hpp')+"')\n  for p in [T/'prepare_original_v2.py',T/'prepare_original_v1.py'")
q=P/'prepare_original_v2.py';assert not q.exists();q.write_text(s);print(json.dumps(dict(recipe=str(q),sha256=sha(q),original_executed=False)))
