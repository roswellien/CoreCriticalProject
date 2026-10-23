"""Exact immutable141 live-allocation budget correction, compile preparation only."""
from pathlib import Path
import json,hashlib,shutil,sys
R=Path(__file__).resolve().parents[2]
def main(mode):
 pins={}
 def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(str(p),h,v);pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 if mode=='service':
  parent=R/'reports/m4-startup141-runway/service-preparation-r1';out=R/'reports/m4-startup141-runway/service-preparation-r2';assert not out.exists();rec=read(parent/'report.json','6edf61e7b56bb178a6b1dbbb5a0b647af4099272cb59a80f3e277267c435aade');assert rec['passed']
  diag=read(R/'reports/m4-startup141-root/failure-diagnostic-r2/report.json','47ad6dee88681e34d263e921cd973bde9f86032c1c1616e03785ff1f7dad1a43');assert diag['passed']and diag['all_readers_closed'];row=diag['records']['sequence-0/selected/locale-summary.bin'];import struct;summary=struct.unpack('<32I',pin(row['path'],row['sha256']).read_bytes());assert summary[14]==93 and summary[16]<=200000 and summary[18]<=4096 and summary[19]<=32
  cases=[]
  for rel,h in [('constructor-original18-source-r4','48cad330f7fe559721fe10748efdf4261e92d22653ba141883065c4c9342fff6'),('constructor-native36-source-r6','e7bc628fe59f20e69a5823e2f54ad88af94d9f0dbbfea1c51d8e45807d5c4392')]:
   proof=read(R/'reports/m4-138-validation-review'/rel/'report.json',h);assert proof['passed']
   for c in proof['cases']:
    branch=c.get('branch','original');stem=R/'reports/m4-138-validation-review'/rel/f"{branch}-{c['sequence']}-{c['root']}";inp=read(stem/'input.json');result=read(stem/'source-derivation.json');births=[o for fact in inp['APIs']for o in fact.get('initial_allocations',[])];born=[o for o in result['source_complete_owners']if 'source_requested'in o];assert len(births)==len(born)==2;assert len(result['source_complete_owners'])==len(inp['owners'])+2;assert all(o['live']and o['source_requested']in(4,12)and o['actual_API_requested']==16 for o in born);assert len(inp['APIs'])==5
    cases.append(dict(branch=branch,sequence=c['sequence'],root=c['root'],genuine_HeapAlloc_births=2,logical_source_requests=[o['source_requested']for o in born],no_constructor_owner_retirements=True))
  assert len(cases)==54
  out.mkdir();relations=[]
  for file in parent.iterdir():
   if file.is_file()and file.name!='report.json':pin(file,rec['files'][str(file.resolve())]);shutil.copyfile(file,out/file.name)
  q=out/'locale_batch_operations.inc';before=q.read_text();old='live_allocations()>92';new='live_allocations()>98';assert before.count(old)==1;after=before.replace(old,new);assert after.replace(new,old)==before;q.write_text(after)
  realloc=pin(parent/'registry_api.inc').read_text();assert 'owned_allocations_.push_back'not in realloc and 'a->generation=++generation_'in realloc
  cleanup=pin(parent/'locale_batch_operations.inc').read_text();assert 'for(auto i=owned_allocations_.rbegin();i!=owned_allocations_.rend();++i)'in cleanup
  for file in parent.iterdir():
   if file.is_file()and file.name!='report.json':relations.append(dict(parent=str(file),child=str(out/file.name),parent_sha256=sha(file),child_sha256=sha(out/file.name),whole_bytes_equal=sha(file)==sha(out/file.name)))
  assert [Path(v['child']).name for v in relations if not v['whole_bytes_equal']]==['locale_batch_operations.inc']
  contract=dict(passed=True,scope='Inherited finite92 service bound plus exactly6 genuine new constructor HeapAlloc births; no blanket resource relaxation.',old_live_cap=92,new_live_cap=98,selected_new_roots=[0x4103f0,0x410440,0x459b40],new_births_per_root=2,additive_maximum=6,actual_failed_summary=list(summary),actual_failing_predicate='live_allocations()==93 >92',unchanged_caps=dict(call_depth=32,source_operands=200000,native_APIs=4096),literal54_birth_proofs=cases,HeapReAlloc_reuses_same_private_Allocation=True,reverse_cleanup_iterates_all_actual_owned_allocations=True,full141_maximum_runtime_verification_pending=True,source_AFTER_seed=False,initializer_credit=0)
  (out/'live-allocation-budget-contract.json').write_text(json.dumps(contract,indent=2));(out/'live-allocation-budget-delta.json').write_text(json.dumps(dict(file='locale_batch_operations.inc',before=old,after=new,occurrences=1,inverse_restores_entire_parent=True),indent=2))
  rec.update(native_include=str(out),native_library=str(out/'registry_library.cpp'),parent_union_preparation_sha256=sha(parent/'report.json'),scope='Compile-only exact141 live cap92to98, justified by literal54 exactly6 new root births; all other source/ownership/API/caller guards unchanged',budget_source_relations=relations,changed_files=['locale_batch_operations.inc'],native_executed=False,execution_admitted=False,initializer_credit=0)
 elif mode=='full':
  parent=R/'reports/m4-startup141-runway/preparation-r2';out=R/'reports/m4-startup141-runway/preparation-r3';assert not out.exists();rec=read(parent/'report.json','92b9ef5628be17e61070a3570d6faf8c0ff3235b1087210ed58a279e135f572c');assert rec['passed'];service=R/'reports/m4-startup141-runway/service-preparation-r2';sp=read(service/'report.json');sb=read(R/'reports/m4-startup141-runway/service-build-r2/build.json');assert sp['passed']and sb['passed']and sb['preparation_sha256']==sha(service/'report.json');out.mkdir()
  for file in parent.rglob('*'):
   if file.is_file()and file.name!='report.json':pin(file,rec['files'][str(file.resolve())]);dst=out/file.relative_to(parent);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,dst)
  q=out/'onexit_session.hpp';old=q.read_text();new=old.replace('service-preparation-r1','service-preparation-r2');assert new!=old and new.replace('service-preparation-r2','service-preparation-r1')==old;q.write_text(new)
  for f,h in sp['files'].items():pin(f,h)
  for f,h in sb['files'].items():pin(f,h)
  rec.update(native_include=str(service),native_library=str(service/'registry_library.cpp'),borrowed_service_preparation=str(service/'report.json'),borrowed_service_preparation_sha256=sha(service/'report.json'),one_canonical_union_Session_header=str(service/'session.hpp'),budget_parent_preparation=str(parent/'report.json'),budget_parent_preparation_sha256=sha(parent/'report.json'),scope='Compile-only exact141 preparation rebinding corrected canonical service live cap98; one wrapper path change, all selected source/IR/objects/FP/state/output code identical',current141_acceptance=False,native_executed=False,execution_admitted=False,initializer_credit=0)
  (out/'budget-preparation-delta.json').write_text(json.dumps(dict(file='onexit_session.hpp',before=old,after=new,inverse_restores_entire_parent=True),indent=2))
 else:raise ValueError(mode)
 for file in out.rglob('*'):
  if file.is_file():pin(file)
 pin(__file__);rec['files']=pins;q=out/'report.json';q.write_text(json.dumps(rec,indent=2));print(sha(q))
if __name__=='__main__':main(sys.argv[1])
