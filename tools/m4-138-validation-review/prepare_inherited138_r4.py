"""Fresh tree/old4 adapters retaining full page relations and finite suffix proof."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2];files={};changes=[]
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip')and p.name not in('index.json','payload.bin','transport.json')
 with p.open('rb')as f:d=hashlib.file_digest(f,'sha256').hexdigest()
 assert h is None or h==d;files[str(p)]=d;return p
for namespace in('inherited-source-preparation-r2','inherited-source-preparation-r3'):
 p=pin(R/'reports/m4-startup138-original'/namespace/'report.json');q=json.loads(p.read_text());assert q['passed']
 for p,h in q['files'].items():pin(p,h)
helper=pin(R/'tools/m4-startup138-original/registry_suffix_v1.py');transition=pin(R/'tools/m4-startup138-original/mfc_transition_v1.py')
diag=pin(R/'reports/m4-138-validation-review/mfc-transition-r3/report.json','56cc2983c3448cf872e9247cb315cede98a83fa9a63c831264d9008b7ad9e834');d=json.loads(diag.read_text());assert d['passed']and d['reader_closed']
patches=pin(diag.parent/'patch-identities.json',d['files'][str(diag.parent/'patch-identities.json')])
# Bind literal store source PCs to physical immutable CRT instructions.
sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
crt=PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
contracts=json.loads(pin(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json').read_text())
program={r['pc']:r for r in contracts['instructions']}
physical=[]
for pc in(0x78004a67,0x78004a69):
 row=program[pc];assert row['mnemonic']==('mov'if pc==0x78004a67 else'add');raw=bytes.fromhex(row.get('raw_bytes',row.get('bytes_hex',row.get('raw',''))));assert raw
 off,_=crt.rva_range(pc-crt.image_base,len(raw));assert crt.data[off:off+len(raw)]==raw;physical.append(row)
def derive(name,target_name,replacements):
 parent=R/'tools/m4-startup138-original'/name;original=pin(parent).read_text();text=original;ops=[]
 for a,z in replacements:
  assert text.count(a)==1,(name,a);i=text.index(a);text=text[:i]+z+text[i+len(a):];ops.append(dict(offset=i,before=a,after=z))
 inverse=text
 for op in reversed(ops):
  i=op['offset'];assert inverse[i:i+len(op['after'])]==op['after'];inverse=inverse[:i]+op['before']+inverse[i+len(op['after']):]
 assert inverse==original;ast.parse(text);target=parent.with_name(target_name);assert not target.exists();target.write_text(text);pin(target);changes.append(dict(parent=str(parent),target=str(target),exact_inverse_restores_parent=True,operations=ops))
derive('tree_source_r2.py','tree_source_r4.py',[
 ("        for page in pages:\n            if page==0x20001000:continue\n            equal(machine.bytes(page,4096),bytes(actual_after[page]),'Whole actual original nonstack page '+hex(page));counts['whole_original_nonstack_pages']+=1", "        suffix=load('tree_registry_suffix',ROOT/'tools/m4-startup138-original/registry_suffix_v1.py');registry_suffix=suffix.prove(reader,sequence,tree_phase,machine,0x4b7fa0,phase,API);result['separate_registry_suffix']=registry_suffix\n        for page in pages:\n            if page==0x20001000:continue\n            equal(suffix.page(machine.bytes(page,4096),page,registry_suffix),bytes(actual_after[page]),'Whole actual original nonstack page plus independently proven registry suffix '+hex(page));counts['whole_original_nonstack_pages']+=1")])
extra=""" extra_pages=p['extra_whole_source_pages'];need(len(extra_pages)==26 and len(set(pages+extra_pages))==69 and {0x5cd000,0x5e3000,0x5e9000}<=set(extra_pages),'All26 complete physical additional source pages, retaining inherited three')"""
extra_z=extra+"\n suffix=own(ROOT/'tools/m4-startup138-original/registry_suffix_v1.py','old4_registry_suffix');transition_module=own(ROOT/'tools/m4-startup138-original/mfc_transition_v1.py','old4_hook_transition');transition_receipt=read(ROOT/'reports/m4-138-validation-review/mfc-transition-r3/report.json','"+files[str(diag)]+"');need(transition_receipt['passed']and transition_receipt['reader_closed'],'Exact independent whole hook-mode transitions');transitions=transition_module.Transition(read(ROOT/'reports/m4-138-validation-review/mfc-transition-r3/patch-identities.json','"+files[str(patches)]+"'))"
derive('old4_source_r2.py','old4_source_r4.py',[
 (extra,extra_z),
 ("    if previous_extra:equal(before_extra[a],previous_extra[a],'Complete original external source page carry')", "    if previous_extra:\n     if phase in(13,14):transitions.relation(previous_extra[a],before_extra[a],a,phase,seq)\n     else:equal(before_extra[a],previous_extra[a],'Complete original external source page carry')"),
 ("    for page in pages+extra_pages:\n     if page==0x20001000:continue\n     equal(machine.bytes(page,4096),after[page],'Entire original source prefix nonstack page '+hex(page));counts['whole_original_prefix_page_relations']+=1", "    registry_suffix=suffix.prove(reader,seq,phase,machine,callback,b,api)\n    for page in pages+extra_pages:\n     if page==0x20001000:continue\n     equal(suffix.page(machine.bytes(page,4096),page,registry_suffix),after[page],'Entire original source prefix nonstack page plus independently proven registry suffix '+hex(page));counts['whole_original_prefix_page_relations']+=1")])
derive('current_inherited_source_v2_r3.py','current_inherited_source_v2_r4.py',[('tree_source_r2.py','tree_source_r4.py'),('old4_source_r2.py','old4_source_r4.py'),('inherited-source-preparation-r3','inherited-source-preparation-r4')])
pin(__file__);pin(sys.executable);out=R/'reports/m4-startup138-original/inherited-source-preparation-r4';assert not out.exists();out.mkdir()
for name,value in(('deltas.json',changes),('physical-registry-store-rows.json',physical)):
 p=out/name;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
report=dict(passed=True,scope='Tree/old4 full69 source page equality plus finite independently derived literal registry suffix; old4 exact MFC observer-mode chronology',capture_reader_opened=False,source_comparison_executed=False,exact_inverse_restores_parents=True,no_page_mask=True,no_AFTER_seed=True,full_registration_provider_CPU_claim=False,initializer_credit=0,files=files)
p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())))
