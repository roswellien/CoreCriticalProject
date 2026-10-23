"""Current actual compiled-input identity and unexecuted full physical reviewer recipe."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141/compiled-review-recipe-r1';out.mkdir();files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;assert files.setdefault(str(p),v)==v;return p
 build=R/'reports/m4-original141/build-r1';actual=R/'reports/m4-original141/source-preparation-r2';current=R/'reports/m4-original141/source-preparation-r3'
 b=json.loads(pin(build/'build.json','088e5dfbe970baee5e8187edbfbb5f06eafd217d2b1f5554e344ed55b836d79b').read_bytes());assert b['passed']and Path(b['preparation']).resolve()==actual and b['preparation_sha256']=='7c1acf0bb08043cf8a371a6b31d7fc3f4071771dae936a748abad66969c8cbd8'and not b['original_executed']and not b['native_executed']
 pin(actual/'report.json',b['preparation_sha256']);pin(current/'report.json','8f983d72c0a3aeabedd87cc009f7dd5704f6236d251bc66610671551161d365b')
 for p,h in b['sources'].items():pin(p,h)
 pin(b['worker'],b['worker_sha256']);pin(build/'pins.json')
 physical=[]
 for p in actual.iterdir():
  if p.is_file()and p.name not in('report.json','pins.json'):
   q=current/p.name;assert pin(p).read_bytes()==pin(q).read_bytes();physical.append(dict(actual_compile_path=str(p),current_review_path=str(q),sha256=sha(p),whole_bytes_equal=True))
 release=build/'build-x86/mw34_joint_startup124_original.dir/Release'
 objects=[]
 for p in release.rglob('*.obj'):pin(p);objects.append(str(p))
 for name in('configure.log','compile.log'):pin(build/name)
 parents=['tools/m4-138-validation-review/review_original138_observer_prelaunch_v6.py','tools/m4-138-validation-review/review_constructor_input_capture_prelaunch_v4.py','tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','tools/m4-startup138-original/mfc_transition_v1.py','tools/m4-138-validation-review/diagnose_transition_r4.py','tools/m4-138-validation-review/constructor_observer_geometry_review_v1.py','tools/m4-138-validation-review/constructor_observer_transparency_controls_v1.py']
 for p in parents:pin(R/p)
 pin(__file__)
 recipe=dict(actual_compiled_preparation=str(actual),actual_compiled_report_sha256=b['preparation_sha256'],actual_build=str(build/'build.json'),actual_worker=str(Path(b['worker'])),actual_worker_sha256=b['worker_sha256'],review_current_preparation=str(current),complete_physical_identity=physical,objects=objects,whole_ASM_objects=['reference_x86','boundaries','api_boundaries','preserve_x86','fs_observer_x86','nullfree_observer_x86','vtable_observer_x86','lockit_observer_x86','format_observer_x86','fps_observer_x86','constructor_observer_x86'],criteria=[
 'Retain original138 whole linked assembly sections and source observer C++ function proofs. Add complete constructor ASM section and every constructor/input collector C++ function from tested37 review. Typed COFF relocations must resolve to actual current PE targets, never wildcard local-symbol collisions.',
 'Prove all actual compiler CL/ASM read tlogs consume source-preparation-r2 paths with current actual build identities. Source-preparation-r3 is byte-identical review metadata lineage, never pretend it was compiled. Require Win32/x86 strict W4/WX actual compiler/link success.',
 'For all143 active source patches bind owning physical stolen bytes, compiled observer symbols/complete assembly bytes, continuations, matching CPP installer and current DLL/source-page input. Preserve overlap prohibition except declared IAT and CRT instrumentation mode transitions.',
 'Validate compiled PUSHFD ownership for every complete11 constructor observer bridge including getter after RET and inline CS24 before-copy: ordered exact guest ESP/value/write PC and source-computed partially-defined EFLAGS; reject additional bytes/wrong spans/prior mode, no endpoint masking or source AFTER seeds.',
 'Create current observer-transition declaration for MFC phase15 and followingphase16 from current compiled CRT hooks; exact whole previous4096-byte page copy + exact expected old span bytes + finite source-owned patch effects must equal full current page. Retain original138 resource/FPS/GDI/full stack and69page comparisons.',
 'At constructor phases13/14/39 temporary MFC823 IAT install and restore pin compiled current shim identity and physical named original IAT cell. Distinguish captured BEFORE originaltarget, capture AFTER shimentry, followingphase BEFORE originaltarget. Reconstruct exact whole5BB000 page, not blanket exemption.',
 'Fresh strict original141 current-own-BEFORE CRT64pages/34DWORD descriptor/CS24/schema/wholeglobal5F2000/6birth2NULL/growth/111callback/manualcleanup gates need fresh validators and synthetic adverse controls before any worker. Existing original138 count/numerical oracles remain baseline domain only.'
 ],root_independent_review_required=True,reviewer_executed=False,worker_admission_pending=True)
 p=out/'recipe.json';p.write_text(json.dumps(recipe,indent=2)+'\n');pin(p)
 report=dict(passed=True,prepared_recipe_only=True,actual_compile_source2_to_review_source3_full_byte_identity=True,physical_payloads=len(physical),actual_compiled_build_passed=True,whole_linked_observer_review_pending=True,PUSHFD_source_stack_review_pending=True,whole_CRT_IAT_transition_validator_pending=True,worker_executed=False,canonical_reader_opened=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(out/'report.json'),sha256=sha(out/'report.json'),recipe=str(p))))
if __name__=='__main__':main()
