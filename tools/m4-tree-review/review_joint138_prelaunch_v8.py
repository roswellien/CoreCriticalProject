"""Reattribute the same complete138 Context with finite source-owned growth guards.

Whole worker/function/target/TLS/unwind and original131 source checks remain.
This is bounded native prelaunch admission, never initializer acceptance.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
p=Path(__file__).with_name('review_joint138_prelaunch_v7.py')
scope={'__file__':str(p),'__name__':'materialize_growth_admission'}
exec(compile(p.read_text(),str(p),'exec'),scope);t=scope['t']
for a,b in [
 ('ea6c0f3713796e85042039c8af7cf36f0b9faee7035cdf511be1af000023d7ca','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a'),
 ('ddef4da1943c6285bd462158da0e7360dcbf6a3bab40efe2247d7dea6e7c985a','7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47'),
 ("folder=R/'reports/m4-joint-startup138/preparation-r3'","folder=R/'reports/m4-joint-startup138/preparation-r4'"),
 ('reports/m4-joint-startup138/build-r4/','reports/m4-joint-startup138/build-r5/'),
 ('reports/m4-joint-startup138/admission-map-r2/report.json','reports/m4-joint-startup138/admission-map-r3/report.json'),
 ('bf63bb975fb4a4e70586d7a700c152a8f244a305f0eaea9eaaf2cbf6c431fd11','e336c6a57bf1e84ec5146e9eb4c70079032df65b277b048dee79348da0300841'),
 ('reports/m4-fps-native/service-preparation-r2/session.hpp','reports/m4-fps-native/service-preparation-r3/session.hpp')]:
 assert a in t,a;t=t.replace(a,b)
anchor="  source=read(R/'reports/m4-tree-review/widget138-component-source-r2/report.json'"
at=t.index(anchor)
extra=r'''
  prior_current=read(R/'reports/m4-tree-review/joint138-prelaunch-r7/report.json','e529d4d2211945671bfd09b5af80ad2af176ea8c439b966b5eaee917cf722383')
  growth_source=read(R/'reports/m4-widget-growth-review/source-review-r1/report.json','d6f76cacd9cdeb9644b67091a5be0d884c3abce732ec6b0c9f08bd624068243c')
  growth_guard=read(R/'reports/m4-widget-growth-review/guard-review-r1/report.json','7170e349dcecf013a616cc593029354154fe38edf964148490fa2bec207fe724')
  service=read(R/'reports/m4-fps-native/service-preparation-r3/report.json','cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9')
  prior_service=read(R/'reports/m4-fps-native/service-preparation-r2/report.json','d3afbd1f20d9a286a0ae8565554845f897c4d7a051d60110bb64912fa15d77c2')
  relations=service['copied_source_relations'];assert len(relations)==72
  for row in relations:
   before=pin(row['prior_path'],row['prior_sha256']).read_bytes();after=pin(row['current_path'],row['current_sha256']).read_bytes()
   assert (before==after)==row['byte_identical']
  assert [row['name']for row in relations if not row['byte_identical']]==['session_impl.inc']
  import difflib
  oldsvc=pin(R/'reports/m4-fps-native/service-preparation-r2/session_impl.inc').read_text()
  newsvc=pin(R/'reports/m4-fps-native/service-preparation-r3/session_impl.inc').read_text()
  changes=[v for v in difflib.SequenceMatcher(None,oldsvc.splitlines(True),newsvc.splitlines(True),autojunk=False).get_opcodes()if v[0]!='equal']
  assert len(changes)==2 and all(v[0]=='replace'for v in changes)
  assert [oldsvc.splitlines(True)[a:b]for _,a,b,_,_ in changes]==[
   [line for line in oldsvc.splitlines(True)if 'Current live producer full-byte extent before literal msize'in line],
   [line for line in oldsvc.splitlines(True)if 'Actual literal msize capacity and source-owned registry publication'in line]]
  pre=''.join(newsvc.splitlines(True)[changes[0][3]:changes[0][4]])
  post=''.join(newsvc.splitlines(True)[changes[1][3]:changes[1][4]])
  for token in ('((next-begin)&3U)==0','std::uint64_t(next)<=std::uint64_t(begin)+allocation->extent','!allocation->source_freed','!allocation->cleanup_freed','oldgeneration=allocation->generation','oldacquired=allocation->acquired','binding->guest_bytes(begin,oldextent)'):
   assert token in pre,token
  for token in ('current==allocation','published_next==std::uint64_t(published)+used+4','growth_after==growth_before||growth_after==growth_before+1','size_calls==(grew?2U:1U)&&realloc_calls==unsigned(grew)','current->generation==oldgeneration','g[9]==g[8]+16','g[10]==((g[9]+15)&~15ULL)','g[15]==current->generation&&g[15]>oldgeneration','current->capacity==0','g[18]==unsigned(g[14]!=oldacquired)','inputs[0]==binding->native_apis_[last_size].outputs[0]','outputs[0]==current->initial','published==(g[18]?oldcursor:begin)','Whole actual realloc initial extent with only the literal callback append','Every preceding producer byte carried, except the one source callback append'):
   assert token in post,token
  assert 'dispatch_body'not in pre+post and 'memory().store'not in pre+post and 'expected_store'not in pre+post
  assert newsvc.count('lb::dispatch_body(0x78004a36,&s,binding.get())')==oldsvc.count('lb::dispatch_body(0x78004a36,&s,binding.get())')==1
  counts['whole_growth_service_source_relations']=72;counts['unchanged_growth_service_inputs']=71;counts['finite_growth_guard_hunks']=2
  assert p['borrowed_service_preparation_sha256']=='cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9'
  read(R/'reports/m4-joint-startup138/controller-preparation-r4/report.json','e3f38d7fba18687542bcab92594ab5d9466397c0b5802759641b39fd52de2922')
  assert pin(R/'tools/m4-joint-startup138/run_v3.py').read_bytes()==pin(R/'tools/m4-joint-startup138/run_v2.py').read_bytes()
'''
t=t[:at]+extra+t[at:]
t=t.replace("  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v6.py');","  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v7.py');pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v6.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
