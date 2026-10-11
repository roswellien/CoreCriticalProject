from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
T=Path(__file__).resolve().parent;base=T/'prepare_v3.py';p=T/'prepare_v4.py'
assert not p.exists()
s=base.read_text()
old=" ref=one(ref,'    out.finish();std::cout<<','    connected_writer=nullptr;out.finish();std::cout<<');(out/'reference.cpp').write_text(ref)"
new=""" ref=one(ref,'if(binding.root>entries[phase])continue;','if(std::find(entries.begin(),entries.begin()+phase+1,binding.root)==entries.begin()+phase+1)continue;')
 ref=one(ref,'if(binding.entry>entries[phase])continue;','if(std::find(entries.begin(),entries.begin()+phase+1,binding.entry)==entries.begin()+phase+1)continue;')
 ref=one(ref,'    out.finish();std::cout<<','    connected_writer=nullptr;out.finish();std::cout<<');(out/'reference.cpp').write_text(ref)"""
assert s.count(old)==1;s=s.replace(old,new)
old="contracts=dict(selected_order=selected,source_frame=";assert s.count(old)==1
s=s.replace(old,"contracts=dict(selected_order=selected,live_old_owner_export_condition='Exact carried selected-order prefix membership; never root-address numeric ordering',source_frame=")
p.write_text(s)
q=T/'preparation-v4-lineage.json';q.write_text(json.dumps(dict(base=str(base),base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),generated=str(p),generated_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),changes=['MFC and string existing-owner export predicates use actual selected-order prefix membership, because newly inserted high-address MFC root is at phase13 before all future owners. Guest execution and allocations unchanged.'],candidate_writer_executed=False),indent=2)+'\n')
print(p)
