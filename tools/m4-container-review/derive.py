"""Prepare additive persistent116 review tools from sealed accepted109 sources."""
from pathlib import Path
import ast,difflib,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-container-review'/name;need(not out.exists(),'Fresh observer preparation');out.mkdir(parents=True);pins={};generated={};diffs={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Frozen source '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable physical source');pins[str(p)]=v;return p
 def replace(s,a,b):need(s.count(a)==1,'Single exact derivative anchor '+a);return s.replace(a,b,1)
 def output(filename,s,old):
  ast.parse(s);p=HERE/filename;need(not p.exists(),'Fresh generated observer');p.write_text(s);generated[str(p.resolve())]=sha(p)
  d=out/(filename+'.diff');d.write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='accepted-parent',tofile=filename)));pin(d);diffs[filename]=str(d)
  copy=out/'sources'/filename;copy.parent.mkdir(exist_ok=True);copy.write_bytes(p.read_bytes());pin(copy);pin(p)
 parent=pin(ROOT/'reports/m4-joint-startup109-root/acceptance-r1/report.json','697765f750209d9bee79541b973494dca89692f4ec630057d282cbbb450266e0');need(json.loads(parent.read_bytes())['passed'],'Accepted109 parent')
 interface=pin(ROOT/'reports/m4-container-source/allocation-interface-r1/report.json','89a6a4b581bedd7a1b98ccfad1344ba35f6c50a011964230aecaa1f7295e95ec');value=json.loads(interface.read_bytes());need(value['passed'],'Physical literal BEFORE-derived source interface')
 for p,h in value['files'].items():pin(p,h)
 base=ROOT/'tools/m4-fs-provider-review';oldproof=json.loads(pin(ROOT/'reports/m4-fs-provider-review/source-r1/report.json','f151ee977a744a3d19a39c24ad16d0e957565ffb1fdd713865a41b77e94b3fe0').read_bytes())
 # Reuse the exact complete comparison helper without changing its code.
 equality=pin(base/'exact_equal.py','7d7c7fddfe2c051a02bddf7230e2fc5a73f4e0a972aa227c8310de1d7f3c6b97');need(not(HERE/'exact_equal.py').exists(),'Fresh equality module');(HERE/'exact_equal.py').write_bytes(equality.read_bytes());pin(HERE/'exact_equal.py')
 p=pin(ROOT/'tools/m4-strings-review/final_observer_v2.py',oldproof['files'][str(ROOT/'tools/m4-strings-review/final_observer_v2.py')]);old=p.read_text();s=old
 s=replace(s,"self.input_specs=json.loads(pin(ROOT/'reports/m4-strings-review/interface-r2/instruction-contracts.json').read_bytes())['inputs']","self.input_specs=json.loads(pin(ROOT/'reports/m4-strings-review/interface-r2/instruction-contracts.json').read_bytes())['inputs']+json.loads(pin(ROOT/'reports/m4-container-source/allocation-interface-r1/string-inputs.json').read_bytes())")
 s=replace(s,"len(actual)==len(self.strings)==16,'Exactly16 actual source calls, null descriptor root has no fabricated call'","len(actual)==len(self.strings)==19,'Exactly19 literal duplicate calls; accepted null descriptor root has no fabricated call'")
 output('string_observer116.py',s,old)
 p=pin(base/'final_observer109_v3.py','798257718db67e92e563bbc0d236b0f57e5029698788dd6443c028455fe29130');old=p.read_text();s=old
 s=replace(s,"S=load('accepted71_provider_observation',ROOT/'tools/m4-strings-review/final_observer_v2.py')","S=load('container116_provider_observation',ROOT/'tools/m4-container-review/string_observer116.py')")
 s=replace(s,'need=S.need;S.equal=equal','need=S.need;S.equal=equal\nfrom event_model import ContainerEvents')
 s=replace(s,"  self.specs+=self.fs_specs","  self.specs+=self.fs_specs\n  interface=ROOT/'reports/m4-container-source/allocation-interface-r1'\n  self.new_allocation_specs=json.loads(self.pin(interface/'allocation-inputs.json').read_bytes());self.specs+=self.new_allocation_specs\n  borrowed=json.loads(self.pin(interface/'borrowed-constructor-inputs.json').read_bytes());zero_frees=json.loads(self.pin(interface/'nullfree-inputs.json').read_bytes());vectors=json.loads(self.pin(interface/'vector-endpoints.json').read_bytes());stores=[]\n  for row in vectors:\n   for pc,address,kind in((row['publication_PC'],row['publication'],1),(row['end_PC'],row['end_address'],2),(row['capacity_PC'],row['capacity_address'],3)):\n    stores.append(dict(root=row['root'],pc=pc,address=address,kind=kind,CALL_pc=row['CALL_pc']))\n   for i,item in enumerate(row['additional_empty_pointer_fields']):stores.append(dict(root=row['root'],pc=item['PC'],address=item['address'],kind=4+i,CALL_pc=row['CALL_pc']))\n  self.container_tail_projections=0;self.container=ContainerEvents(self,borrowed,zero_frees,stores)")
 s=replace(s," def mfc_event(self,m,event,data):"," def mfc_event(self,m,event,data):\n  if self.container.event(m,event,data):return")
 s=replace(s,"  COUNTS['MFC_import_records']+=len(self.mfc_imports);COUNTS['MFC_literal_store_records']+=len(self.mfc_stores)","  COUNTS['MFC_import_records']+=len(self.mfc_imports);COUNTS['MFC_literal_store_records']+=len(self.mfc_stores)\n  for key,value in self.container.dump(m,stage).items():COUNTS[key]+=value")
 for a,b in(("len(actual)==len(self.mfc)==45","len(actual)==len(self.mfc)==50"),("len(allocations)==len(responses.allocations)==62","len(allocations)==len(responses.allocations)==70"),("for a in responses.allocations)==45","for a in responses.allocations)==50"),("for a in responses.allocations)==16","for a in responses.allocations)==19"),("registry-replay-{81+n}","registry-replay-{88+n}"),("complete109_provider_sequences","complete116_provider_sequences"),("selected_registration_closures']+=81","selected_registration_closures']+=88"),("actual_MFC_allocations']+=45","actual_MFC_allocations']+=50"),("actual_duplicate_allocations']+=16","actual_duplicate_allocations']+=19"),("actual_source_frees']+=62","actual_source_frees']+=70"),("actual_MFC_source_frees']+=45","actual_MFC_source_frees']+=50"),("actual_MFC_allocations=45","actual_MFC_allocations=50")):
  need(a in s,'Required literal derivative field '+a);s=s.replace(a,b)
 s=s.replace('Exact45 source allocation calls across38 MFC initializer roots','Exact50 genuine source allocation calls across43 MFC initializer roots').replace('One real producer,16 strings and45 actual MFC private owners','One real producer,19 strings and50 actual MFC private owners')
 s=replace(s,"  ROWS.append(dict(level=self.level", "  COUNTS['declared_container_thunk_frame_entry_projections']+=self.container_tail_projections\n  COUNTS['actual_normal_null_frees']+=5;COUNTS['actual_borrowed_constructors']+=3;COUNTS['source_unchanged_acquired_vector_extents']+=5\n  ROWS.append(dict(level=self.level")
 output('final_observer116.py',s,old)
 p=pin(base/'observe109_v3.py','1a8f9c00b07cf7f661b5438606a871c78f936686e7fd7242f109c9ac9e0d405a');old=p.read_text();s=old
 s=s.replace('import final_observer109_v3 as V','import final_observer116 as V').replace("with_name('final_observer109_v3.py')","with_name('final_observer116.py')").replace("ROOT/'tools/m4-fs-source/game_model.py'","ROOT/'tools/m4-container-source/game_model.py'")
 s=replace(s,'0x731000,0x5f498000)','0x731000,0x5f498000,0x736000,0x5f4cc000)')
 s=replace(s,'def main(native_report,name):','def main(native_report,original_report,name):')
 s=replace(s,"out=ROOT/'reports/m4-fs-provider-review'/name","out=ROOT/'reports/m4-container-review'/name")
 s=replace(s,"  op=pin(ROOT/'reports/m4-fs-source/original-validation-r1/report.json','a419e9a7819ba38077621efdda6da5440c0f00042c6c492d7dc672ebeab632b4');ori=D.DirectSet(json.loads(op.read_bytes())['original_capture'],pin)","  op=pin(original_report);original_receipt=json.loads(op.read_bytes());need(original_receipt['passed'],'Fresh full116 original execution proof');ori=D.DirectSet(original_receipt['original_capture'],pin)")
 s=replace(s,"+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes());roots=", "+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/container-roots.json').read_bytes());roots=")
 s=replace(s,"order=json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json').read_bytes())['selected_order'];need(len(order)==109,'Exact full109 source order')","order=json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/instruction-contracts.json').read_bytes())['selected_order'];need(len(order)==116,'Exact full116 source order')")
 s=replace(s,"   if p==0x5f498000:return", "   if p==0x5f4cc000:\n    mfc=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes());return mfc.read(mfc.rva_range(p-mfc.image_base,4096)[0],4096)\n   if p==0x5f498000:return")
 s=replace(s,"      if page not in before['memory']:before['memory'][page]=initial_page(page)","      if page==0x5f4cc000:\n       physical=initial_page(page)\n       if page in before['memory']:equal(before['memory'][page],physical,'Declared native complete raw physical MFC data BEFORE input')\n       before['memory'][page]=physical\n      elif page not in before['memory']:before['memory'][page]=initial_page(page)")
 s=s.replace('o[145636:288996]','o[153828:305380]').replace('o[2276:145636]','o[2276:153828]')
 s=s.replace('len(expected_callbacks)==81','len(expected_callbacks)==88').replace('All81 actual callback registrations','All88 actual callback registrations').replace('persistent109_sequences','persistent116_sequences').replace('complete109_provider_sequences','complete116_provider_sequences').replace('All12 complete independent provider sequences','All12 complete independent116 provider sequences').replace('native109','native116').replace('selected109','selected116').replace('entire35pages','entire37pages')
 s=replace(s,"  pin(Path(__file__).with_name('exact_equal.py'))", "  pin(Path(__file__).with_name('exact_equal.py'));pin(Path(__file__).with_name('event_model.py'));pin(Path(__file__).with_name('string_observer116.py'));pin(ROOT/'tools/m4-fs-source/game_model.py')")
 s=replace(s,"main(Path(sys.argv[1]).resolve(),sys.argv[2])","main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),sys.argv[3])")
 output('observe116.py',s,old)
 pin(HERE/'event_model.py');pin(__file__);r=dict(passed=True,scope='Additive frozen observer tool preparation only; no execution or initializer credit. Exact whole byte comparison helper unchanged; one bootstrap plus literal source carries and finite typed API facts; genuine first source msize capacity prediction preserved.',selected_roots=116,source_pages=37,expected_callback_registrations=88,expected_MFC_owners=50,expected_strdup_owners=19,expected_live_owners=70,normal_null_frees=5,borrowed_constructors=3,vector_field_stores=17,generated=generated,diffs=diffs,API_response_injection=False,candidate_AFTER_machine_seed=False,initializer_credit=0,files=pins,physical_closure=verify_manifest(pins))
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
