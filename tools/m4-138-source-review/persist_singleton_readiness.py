"""Narrow ordinary-file singleton audit and matched version definition readiness.

Does not authenticate inherited unions, run workers, or open capture readers.
"""
from pathlib import Path
import ast, hashlib, json, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-singleton-readiness/readiness-r1';assert not out.exists();out.mkdir(parents=True)
 pins={}
 def pin(relative,expected=None):
  p=(R/relative).resolve();assert p.is_relative_to(R)
  assert p.suffix.lower()not in('.mwb','.zip','.mwi')and p.name not in('transport.json','manifest.json','bundle.json')
  h=sha(p);assert expected is None or h==expected,(p,h);pins[str(p)]=h;return p
 examined=[
 'reports/m4-hypot-native/whole-state-r3/report.json','reports/m4-hypot-native/fixture-comparison-r2/report.json',
 'reports/m4-hypot-native/fixture-refusals-r1/report.json','reports/m4-tree-review/hypot-current-review-r4/report.json',
 'reports/m4-version-source/common-controllers-preparation-r1/report.json','reports/m4-version-source/fixture-execution-r2/report.json',
 'reports/m4-version-source/original-execution-r1/failure.txt','reports/m4-version-source/original-execution-r1/original-stage/stage.json',
 'reports/m4-tree-review/version-original-prelaunch-r11/report.json','reports/m4-tree-review/version-prelaunch-r4/report.json',
 'reports/m4-loader-source/service-obligations-r1/report.json','reports/m4-loader-source/service-obligations-r1/blockers.json',
 'reports/m4-loader-source/service-obligations-r1/service-contract.json','reports/m4-loader-source/service-obligations-r1/caller-contract.json',
 'reports/m4-loader-source/service-layout-build-r1/build.json',
 'tools/m4-hypot-native/seal_reached_domain.py','tools/m4-tree-review/review_hypot_current_v5.py',
 'tools/m4-tree-review/review_hypot_current_v4.py','tools/m4-version-source/prepare_common_controllers_v1.py',
 'tools/m4-version-source/prepare_common_pair_v1.py','tools/m4-version-source/run_original_common_v1.py',
 'tools/m4-version-source/run_fixture_common_v1.py','tools/m4-version-source/compare_common_v1.py',
 'tools/m4-loader-source/prepare_obligations_v1.py','tools/m4-loader-source/build_layout_v1.py']
 for relative in examined:pin(relative)
 findings=[dict(root='0x4B5910',evidence='Independent hypot-current-review-r4 confirms 12 whole State/CPU joins, 2280 whole pages, final FSTP C1, and 16 refusal/same Runtime retry cases.',
  credit=0,next_gate='Prepare fresh genuine chronological carried-prefix integration with admitted fixture-build-r6; then fresh linked ownership/lifecycle/source/provider/paired acceptance.',avoid_repeating='Isolated numerical, finite State and refusal checks already pass.'),
 dict(root='0x4AF240',evidence='Original8/native3 common-caller workers are linked and common controllers prepared; old fixture-execution-r2 is structural only and original-execution-r1 failed.',
  credit=0,next_gate='Independently review exact original8/native3 whole-link/source/observer provenance and common recipe before sequential one original and two native workers, then sole original strict-reader comparator. Connected prefix acceptance remains separate.',
  stale_reviews='version-original-prelaunch-r11 binds original6; version-prelaunch-r4 binds native2.'),
 dict(root='0x47F760',evidence='27 bodies, 845 unique source rows, 27 dynamic calls, one switch, 504 lift files, seven assets and compile-only x86/x64 SDK layout witness exist; zero actual API calls and no linked worker.',
  credit=0,next_gate='Implement real registry32/RunDir/cwd and message loader typed ownership boundaries under service-contract; coordinate existing DirectDraw/COM backend task for its provider obligations.',
  remaining='PE32 message/dgVoodoo cannot execute in Win64; real mutable host state, DDSURFACEDESC/COM and MFC/string ownership remain unobserved.')]
 pin('tools/m4-138-source-review/persist_singleton_readiness.py')
 report=dict(passed=True,scope='Archive-free narrow scalar/entrypoint readiness audit; existing receipts physically pinned without inherited union or payload authentication',findings=findings,
  archive_reader_opened=False,worker_launched=False,verifier_launched=False,acceptance_review=False,initializer_credit=0,files=dict(pins))
 target=out/'report.json';target.write_text(json.dumps(report,indent=2)+'\n')
 pair=out.parent/'version-common-readiness-r1';assert not pair.exists();pair.mkdir()
 def read(relative,h=None):return json.loads(pin(relative,h).read_bytes())
 controller=read('reports/m4-version-source/common-controllers-preparation-r1/report.json')
 ob=read('reports/m4-version-source/original-build-r8/build.json',controller['original_build_sha256'])
 nb=read('reports/m4-version-source/fixture-build-r3/build.json',controller['native_build_sha256'])
 op=read('reports/m4-version-source/original-preparation-r8/report.json',controller['original_preparation_sha256'])
 np=read('reports/m4-version-source/fixture-preparation-r4/report.json',controller['native_preparation_sha256'])
 recipe=read('reports/m4-version-source/common-caller-preparation-r1/report.json',controller['common_caller_recipe_sha256'])
 assert all(x['passed']for x in(controller,ob,nb,op,np,recipe))
 assert ob['preparation_sha256']==controller['original_preparation_sha256']and nb['preparation_sha256']==controller['native_preparation_sha256']
 assert op['common_caller_recipe_sha256']==np['common_caller_recipe_sha256']==controller['common_caller_recipe_sha256']
 assert ob['root']==0x4af240 and ob['root_count']==1 and ob['machine']=='I386'
 workers=[dict(branch='original',path=ob['worker'],sha256=ob['worker_sha256'],machine=0x14c)]
 for level in('O0','O2'):
  w=nb['workers'][level];assert w['root']==0x4af240 and w['root_count']==1 and w['literal_bodies']==10 and w['machine']=='AMD64'
  workers.append(dict(branch=level,path=w['path'],sha256=w['sha256'],machine=0x8664))
 for w in workers:
  p=pin(Path(w['path']),w['sha256'])
  with p.open('rb')as f:
   assert f.read(2)==b'MZ';f.seek(0x3c);offset=struct.unpack('<I',f.read(4))[0];f.seek(offset);assert f.read(4)==b'PE\0\0';assert struct.unpack('<H',f.read(2))[0]==w['machine']
 for row in controller['tools']:
  tool=pin(Path(row['path']),row['sha256']);text=tool.read_text();ast.parse(text);compile(text,str(tool),'exec')
  assert controller['common_caller_recipe_sha256']in text
  if tool.name!='compare_common_v1.py':assert "admission['common_caller_recipe_sha256']"in text
  else:assert 'common_caller_validation' in text and 'sole_original_reader=True'in text
 result=dict(passed=True,scope='Independent narrow archive-free common version pair identity/definition readiness; full linked source/object/observer admission remains outstanding',
  exact_build_preparation_links=True,common_recipe_bound=True,controller_definitions_compile=True,whole_worker_file_hashes_checked=True,worker_PE_machines_checked=True,
  workers=workers,common_caller_recipe_sha256=controller['common_caller_recipe_sha256'],
  whole_linked_object_source_observer_relations_reviewed=False,worker_execution_admitted=False,reader_execution_admitted=False,source_original_equivalence=False,
  next_gates=['Review exact common caller application in original8 and native3 source, object and actual final linked worker bodies.',
   'Carry prior original6/native2 physical source/import/ASM/COFF/header/library proofs into additive original8/native3 review with unchanged-byte relations and explicit complete changed code.',
   'Emit matching independent per-worker and sole-reader admissions only when full provenance is established; then run sequential 1 original and 2 native workers and comparator.',
   'Require refusal/ownership/lifecycle and connected chronological prefix acceptance before initializer credit.'],
  inherited_files_union_verified=False,archive_reader_opened=False,worker_launched=False,initializer_credit=0,files=dict(pins))
 q=pair/'report.json';q.write_text(json.dumps(result,indent=2)+'\n')
 for p,h in pins.items():assert sha(p)==h,p
 print(json.dumps(dict(singleton_report=str(target),singleton_sha256=sha(target),version_readiness=str(q),version_sha256=sha(q),direct_physical_inputs=len(pins),worker_admission=False)))
if __name__=='__main__':main()
