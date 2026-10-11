"""Independent light current build/source proof review; no archive payload reads."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
P={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();d=sha(p);need(h is None or d==h,'Exact independent proof input '+str(p));P[str(p)]=d;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh build/source gate review');out.mkdir(parents=True)
 abi=read(R/'reports/m4-tree-build-review/abi-r1/report.json','31f40d698f21d844bdfd83e4b582a25f1aa136c01e9c4d45927650669559f5f5')
 link=read(R/'reports/m4-tree-build-review/link-r1/report.json','046e961a629ca13e4a67ab48c087abda29e714bb5090a184cb902cf9d710eff7')
 resource=read(R/'reports/m4-tree-build-review/resource-r2/report.json','8ca1f131c87dff3144adef277e1f13fb5618d3a88697028dda0cada794f4bed6')
 equivalence=read(R/'reports/m4-tree-review/final-link-equivalence-r2/report.json','baf2c33dee1d9fb06623433a5ad9cf5cc610d8b06d31c4f1c36ae15ff44f7c3d')
 fixture=read(R/'reports/m4-tree-source/native-fixture-source-r5/report.json','feb1e72cb81526104ff64284bcfb1cb9a04ffbc5059eb84b7c3c1331b8a3c255')
 need(all(x['passed']for x in(abi,link,resource,equivalence,fixture)),'All final current bounded gates passed')
 for gate in(abi,link,resource):need(gate['bound_final_build_sha256']=='cdb5b9ca08e4e66dae276fa783bc59b5944e8435113fe9bb65a73cc53f218165','Same current broad125build')
 need(abi['packed_schema_identical_to_accepted124']and abi['unique_whole_pages']==43 and abi['selected_roots']==125 and abi['registrations']==97,'Unchanged packed schema and exact current selected/page/registration counts')
 need([x['level']for x in abi['levels']]==['O0','O2'],'Both actual AMD64 offsetof witnesses')
 for l in abi['levels']:
  v=l['values'];need(v['pointer_bytes']==8 and v['State']==3504 and v['Cpu']==40 and v['Native']==159716 and v['CPU_after']==[76,116]and v['FX_before']==[116,628]and v['fixed_pages']==17 and v['external_pages']==26,'Actual compiled host State/ABI and immutable packed slices')
 need(resource['guest_CS_bytes']==24 and resource['native_resource_bytes']==40 and resource['guest_semantic_DWORD_offsets']==[4,8,12]and resource['opaque_loaded_DWORD_offsets']==[0,16,20]and resource['seeded_state2']is False,'Exact typed guest24/native40 loaded-state scope')
 for l in resource['levels']:need(l['actual_defined_resource_methods']==15,'Only actual implemented resource methods, no obsolete tree_publish claim')
 expected=dict(whole_provider_checkpoints=200,whole_BEFORE_pages=86,whole_AFTER_pages=86,whole_source_access_records=2854,actual_generation_occurrence_joins=14,whole_owned_access_relations=344,whole_publication_relations=14,whole12B_FS_relations=28,whole_native_scratch_contexts=52,whole_native_owner_backings=14,strict_native_levels=2)
 need(fixture['counts']==expected and fixture['native_whole_stack_compared']and not fixture['candidate_AFTER_machine_seed']and not fixture['root_BEFORE_machine_seed']and fixture['reader_closed'],'Strict actual native fixture source proof with full stack and no root AFTER/BEFORE reseed')
 # Physically pin the exact executed scripts and small measured exports.
 for report in(abi,link,resource,fixture):
  for p,h in report['files'].items():
   q=Path(p)
   if q.suffix in('.py','.cpp','.hpp','.inc')or(q.parent in(R/'reports/m4-tree-build-review/abi-r1',R/'reports/m4-tree-build-review/resource-r2')and q.suffix in('.json','.txt')):pin(q,h)
 for p in('tools/m4-tree-build-review/review.py','tools/m4-tree-build-review/resource_v2.py','tools/m4-tree-build-review/resource.py','tools/m4-tree-build-review/abi_witness.cpp','tools/m4-tree-build-review/build_abi.ps1'):pin(R/p)
 body=(R/'tools/m4-tree-source/compare_native_fixture_v5.py').read_text();relations=(R/'tools/m4-tree-source/native_tree_relations_v4.py').read_text()
 for required in("record[141540:145044]","record[145044:148548]","record[76:116]","record[116:628]","Entire4096B AFTER page including whole native stack","Entire bootstrap and tree source access ledger","Entire actual native acquired owner capacity including untouched tail"):
  need(required in body,'Explicit strict full native machine/page/backing check '+required)
 need('C.bootstrap_inputs(reader,stem,index)'in body and 'B2.bootstrap(before,facts,heap,material,Observed,program,callbacks' in body and "G.begin_root(machine,0x4b7f70)"in body and "G.complete_root(machine,api=responses)"in body,'Persistent literal bootstrap then root execution before any candidate endpoint comparison')
 need('equal(bytes(self.state),actual[\'state\']'in body and 'equal(self.fx,actual[\'fx\']'in body,'Full actual API checkpoint observations do not seed model')
 need('max((f for f in source[\'FS_frames\']'in relations and 'source_access_index' in relations and "paired=0xffffffff if ctor else held[-1]"in relations and "equal(c,expected"in relations,'Repeated same-frame calls bind current source invocation and full16Q LIFO context')
 need('expected=(1,w[1],TREE,d[\'pc\']'in relations and "equal(w,expected"in relations and "whole_owned_access_relations"in relations and "whole_publication_relations"in relations,'Every full16Q owned operation/publication checked against actual current generation and literal source effect')
 pin(__file__)
 result=dict(passed=True,scope='Independent bounded source/script/compiled-witness review of final125 ABI/link/resource and strict isolated native fixture equality; no second archive reader or full125 semantic substitute',bound_final_build_sha256=equivalence['bound_final_build_sha256'],native_preparation_sha256=equivalence['native_preparation_sha256'],strict_native_fixture_sha256=sha(R/'reports/m4-tree-source/native-fixture-source-r5/report.json'),ABI_sha256=sha(R/'reports/m4-tree-build-review/abi-r1/report.json'),link_sha256=sha(R/'reports/m4-tree-build-review/link-r1/report.json'),resource_sha256=sha(R/'reports/m4-tree-build-review/resource-r2/report.json'),reviewed_gates=5,actual_ABI_levels=2,native_fixture_levels=2,resource_defined_methods_per_level=15,counts=expected,full125_semantic_evidence_required=True,capture_payload_read=False,initializer_credit=0,files=P)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
