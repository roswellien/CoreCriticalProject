"""Freeze persistent FS allocation/publication ownership geometry."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fs-source'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 rec=json.loads(pin(BASE/'recovery-r3/report.json','17c7840c58bcdce2a82989d141f202cbb25540b6c29b4f314c06c0d1c2bf3a6b').read_bytes())
 geo=json.loads(pin(BASE/'geometry-r1/report.json','ec2a0a1fa4e7b98cdb1c27a81e465da01a27ab8e380f4a72e6af3b714a88ae24').read_bytes())
 trace=json.loads(pin(BASE/'geometry-r1/root-derivations.json').read_bytes());allocs=json.loads(pin(BASE/'geometry-r1/allocation-derivations.json').read_bytes())
 roots={r['entry']:r for r in rec['roots']};rows=[]
 for a in allocs:
  root=a['root'];objects=roots[root]['objects'];assert len(objects)==1;static_object=objects[0]['address']
  primary={0:0x4e794b,1:0x4e792e,2:0x4e7977,3:0x48f357,4:0x470cfa,5:0x4e7977,6:0x4e7977,7:0x4e7977,8:0x4e7977,9:0x4d4936}[a['index']]
  pubs=[p for p in a['publications']if p['pc']==primary];assert len(pubs)==1;p=pubs[0]
  publication=p['address'] if p['static_address'] else 0
  po=p['address_owner'];publication_owner=None if po is None else dict(root=po['root'],CALL_pc=po['CALL_pc'],offset=po['offset'])
  rows.append(dict(root=root,CALL_pc=a['CALL_pc'],requested_size=a['requested_size'],object=static_object,publication=publication,publication_PC=primary,publication_owner=publication_owner,source_allocation_index=a['index'],shared_registry_role=({0:'registry',1:'sentinel',2:'append_node',5:'append_node',6:'append_node',7:'append_node',8:'append_node'}.get(a['index'],'private_object')),source_object_is_static_context=True,primary_field_may_be_updated_by_later_root=primary==0x4e7977))
 assert len(rows)==10 and len({(r['root'],r['CALL_pc'])for r in rows})==10
 cross=[dict(root=t['root'],**w)for t in trace for w in t['prior_owner_writes']]
 assert {r['pc']for r in cross}=={0x4e7977,0x4e797d,0x4e7994}
 accesses=[]
 for t in trace:
  for pc,a,v,n,w in t['source_accesses']:
   owner=next((x for x in allocs if x['declared_pointer']<=a<a+n<=x['declared_pointer']+x['requested_size']),None)
   if owner is not None:accesses.append(dict(root=t['root'],pc=pc,write=bool(w),bytes=n,owner_root=owner['root'],owner_CALL_pc=owner['CALL_pc'],owner_offset=a-owner['declared_pointer']))
 for filename,data in (('allocation-inputs.json',rows),('shared-owner-accesses.json',accesses),('cross-root-owner-writes.json',cross)):(out/filename).write_text(json.dumps(data,indent=2)+'\n');pin(out/filename)
 pin(__file__);report=dict(passed=True,scope='Exact static and persistent positive BEFORE allocation geometry; authentic original/native API owners still required',allocation_inputs_sha256=sha(out/'allocation-inputs.json'),allocations=rows,count=10,distinct_game_allocator_CALL_sites=6,source_geometry_report_sha256=sha(BASE/'geometry-r1/report.json'),primary_publication_modes=['absolute static field','earlier acquired owner plus exact source offset'],primary_publication_not_permanent_for_shared_nodes=True,cross_root_write_PCs=[0x4e7977,0x4e797d,0x4e7994],shared_registry_field=0x60b888,per_root_page_reseed=False,AFTER_machine_seed=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),allocation_inputs_sha256=sha(out/'allocation-inputs.json'))))
if __name__=='__main__':main(sys.argv[1])
