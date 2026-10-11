"""Fresh exact observer transition adaptation with ordinary synthetic controls."""
from pathlib import Path
import ast, hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/m4-138-validation-review/transition-preparation-r1'
files={};changes=[]
def pin(p,h=None):
 p=Path(p).resolve();assert p.name not in('index.json','payload.bin','transport.json')and p.suffix.lower()not in('.mwb','.zip')and p.stat().st_size<=32*1024*1024
 with p.open('rb')as f:d=hashlib.file_digest(f,'sha256').hexdigest()
 assert h is None or d==h;files[str(p)]=d;return p
def replace(text,a,z,file):
 assert text.count(a)==1,(file,a);changes.append(dict(file=file,before=a,after=z,occurrences=1));return text.replace(a,z)
diag_path=ROOT/'reports/m4-138-validation-review/mfc-transition-r3/report.json'
diag=json.loads(pin(diag_path,'56cc2983c3448cf872e9247cb315cede98a83fa9a63c831264d9008b7ad9e834').read_text());assert diag['passed']and diag['reader_closed']and diag['whole_page_relations']==1524
patch_path=diag_path.parent/'patch-identities.json';patches=json.loads(pin(patch_path,diag['files'][str(patch_path)]).read_text())
for path in('reports/m4-startup138-original/preparation-r7/reference.cpp','reports/m4-startup138-original/preparation-r7/fs-hook-bindings.json','reports/m4-startup138-original/build-r4/original-worker.exe','reports/m4-tree-review/original138-prelaunch-r5/compiled-observers.json','reports/m4-tree-review/original138-prelaunch-r5/report.json','reports/m4-startup138-original/build-r4/build-x86/mw34_joint_startup124_original.dir/Release/fs_observer_x86.obj','reports/m4-startup138-original/build-r4/build-x86/mw34_joint_startup124_original.dir/Release/nullfree_observer_x86.obj','local/mw3-staged/Shared_DLLs/MSVCRT.DLL','tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py'):
 pin(ROOT/path,diag['files'][str(ROOT/path)])
helper_path=ROOT/'tools/m4-startup138-original/widget_phase_v2.py';validator_path=ROOT/'tools/m4-startup138-original/validate_v2.py'
helper=pin(helper_path,'9984532b5b341f174fe4b1b78b1aa55f8b62843ebc892344ce6dc95193fd8179').read_text();validator=pin(validator_path,'cf5b8e11c0450e42642595de3b702c00c67efe689aa169495ad4b68f46b691b0').read_text()
helper=replace(helper,'def __init__(self,records,contract,whole,fixed,bindings,counts,targets,fps_target):','def __init__(self,records,contract,whole,fixed,bindings,counts,targets,fps_target,transition):','widget_phase_v3.py')
helper=replace(helper,'  self.records=records;','  self.transition=transition;self.records=records;','widget_phase_v3.py')
helper=replace(helper,'self.stock={};self.previous=None','self.stock={};self.previous=None;self.previous_CRT=None','widget_phase_v3.py')
a="   if self.previous is not None and address!=0x20001000:need(self.previous[address]==a,'Actual whole chronological nonstack source page carry '+hex(address));self.counts['widget_whole_nonstack_carried_page_relations']+=1"
z="""   if self.previous is not None and address!=0x20001000:
    if phase in(13,14):self.transition.relation(self.previous[address],a,address,phase,sequence)
    else:need(self.previous[address]==a,'Actual whole chronological nonstack source page carry '+hex(address))
    self.counts['widget_whole_nonstack_carried_page_relations']+=1"""
helper=replace(helper,a,z,'widget_phase_v3.py')
a="  need(w(crt['before'][0x78037000]"
z="""  if phase in(13,14):
   need(self.previous_CRT is not None,'Actual immediately prior complete CRT endpoint')
   for address in crt['before']:
    self.transition.relation(self.previous_CRT[address],crt['before'][address],address,phase,sequence);self.counts['widget_exact_MFC_CRT_transition_page_relations']+=1
  self.previous_CRT=crt['after']
  need(w(crt['before'][0x78037000]"""
helper=replace(helper,a,z,'widget_phase_v3.py')
validator=replace(validator,'from widget_phase_v2 import Observer,ROOTS as WIDGET_ROOTS,PHASES as WIDGET_PHASES','from widget_phase_v3 import Observer,ROOTS as WIDGET_ROOTS,PHASES as WIDGET_PHASES\nfrom mfc_transition_v1 import Transition','validate_v3.py')
a="   widget=Observer(records,contract,whole,pages,fs_bindings,counts,widget_targets,fps_identity[1])"
z="   transition_receipt=read(pin(ROOT/'reports/m4-138-validation-review/mfc-transition-r3/report.json','"+files[str(diag_path)]+"'));need(transition_receipt['passed']and transition_receipt['reader_closed'],'Exact independent observer transition attribution');transition_path=ROOT/'reports/m4-138-validation-review/mfc-transition-r3/patch-identities.json';transition=Transition(read(pin(transition_path,'"+files[str(patch_path)]+"')))\n   for path in "+repr(tuple(path for path in files if path not in(str(diag_path),str(patch_path),str(helper_path),str(validator_path))))+":pin(path,transition_receipt['files'][path])\n   widget=Observer(records,contract,whole,pages,fs_bindings,counts,widget_targets,fps_identity[1],transition)"
validator=replace(validator,a,z,'validate_v3.py')
validator=replace(validator,"counts['widget_actual_root_phases']==42 and","counts['widget_exact_MFC_CRT_transition_page_relations']==768 and counts['widget_actual_root_phases']==42 and",'validate_v3.py')
validator=replace(validator,"(('widget-GDI-observations',widget.events)","(('exact-MFC-hook-page-transitions',transition.rows),('widget-GDI-observations',widget.events)",'validate_v3.py')
validator=replace(validator,"pin(Path(__file__).resolve().parent/'widget_phase_v2.py')","pin(Path(__file__).resolve().parent/'widget_phase_v3.py');pin(Path(__file__).resolve().parent/'mfc_transition_v1.py')",'validate_v3.py')
ast.parse(helper);ast.parse(validator)
helper_v3=helper_path.with_name('widget_phase_v3.py');validator_v3=validator_path.with_name('validate_v3.py');assert not OUT.exists()and not helper_v3.exists()and not validator_v3.exists()
helper_v3.write_text(helper);validator_v3.write_text(validator);pin(helper_v3);pin(validator_v3)
transition_path=pin(ROOT/'tools/m4-startup138-original/mfc_transition_v1.py');s=importlib.util.spec_from_file_location('synthetic_transition',transition_path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
controls=[]
for phase in(13,14):
 for page in(0x78001000,0x7802e000,0x005e1000):
  previous=bytearray(4096);expected=bytearray(previous)
  for patch in patches:
   if patch['pc']&~4095!=page:continue
   offset=patch['pc']&4095;a=bytes.fromhex(patch['original_hex'if phase==14 else'instrumented_hex']);z=bytes.fromhex(patch['instrumented_hex'if phase==14 else'original_hex']);previous[offset:offset+len(a)]=a;expected[offset:offset+len(z)]=z
  for case in('exact','extra-byte','wrong-mode','wrong-span'):
   a=bytearray(previous);z=bytearray(expected);valid=case=='exact'
   if case=='extra-byte':z[3000]^=1
   if case=='wrong-mode':
    applicable=[p for p in patches if p['pc']&~4095==page]
    if not applicable:continue
    p=applicable[0];off=p['pc']&4095;wrong=bytes.fromhex(p['instrumented_hex'if phase==14 else'original_hex']);a[off:off+len(wrong)]=wrong
   if case=='wrong-span':
    applicable=[p for p in patches if p['pc']&~4095==page]
    if not applicable:continue
    z[applicable[0]['pc']&4095]^=1
   actual=True
   try:m.Transition(patches).relation(bytes(a),bytes(z),page,phase,0)
   except ValueError:actual=False
   assert actual==valid;controls.append(dict(phase=phase,page=page,case=case,expected_valid=valid,actual_valid=actual))
pin(__file__);pin(sys.executable);OUT.mkdir(parents=True)
for name,value in(('deltas.json',changes),('controls.json',controls)):
 p=OUT/name;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
report=dict(passed=True,scope='Fresh additive observer-mode whole4096 transition validator preparation; no capture read',recommend_running_validator=True,root_admission_required=True,validator=str(validator_v3),validator_sha256=files[str(validator_v3)],helper=str(helper_v3),helper_sha256=files[str(helper_v3)],transition_helper=str(transition_path),transition_helper_sha256=files[str(transition_path)],retained_inherited_gates=True,source_nonstack_relation_count_unchanged=55896,new_complete_CRT_transition_relations=768,synthetic_controls_passed=len(controls),capture_reader_opened=False,validation_executed=False,native_executed=False,initializer_credit=0,planned_output_name='original-validation-r2',files=files)
p=OUT/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),validator_sha256=report['validator_sha256'],helper_sha256=report['helper_sha256'],controls=len(controls))))
