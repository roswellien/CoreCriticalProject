"""Add exact two-branch loaded-input carry, preserving the earlier failures."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
source = Path(__file__).with_name('paired_v3.py').read_text()
old = "  need(len(loaded_cp_IAT)==len(loaded_cp_RW)==4096 and words(loaded_cp_RW,0x658)[0]==2,'Authentic complete initialized CP input pages')"
extra = '''
  loaded_input_gate_path=ROOT/'reports/m4-tree-review/loaded-input-page-r2/report.json'
  loaded_input_gate=json.loads(pin(loaded_input_gate_path,'1da680a0f5d1751af3c35e81d3008abbe769331676800c00176d2f4fe3ace4e5').read_bytes())
  need(loaded_input_gate['passed'] and loaded_input_gate['counts']==dict(whole_bootstrap_input_pages=2,explicit_loaded_input_difference_bytes=71,explicit_loaded_input_difference_DWORDs=25,native_literal_state2_operand_joins=408,original_literal_state2_operand_joins=204,native_API_disjoint_CS24_joins=408),'Exact independently reviewed finite loaded-input and disjoint source/API domain')
  loaded_cp_native_RW=pin(loaded_input_gate['whole_native_input_page'],loaded_input_gate['whole_native_input_page_sha256']).read_bytes()
  equal(loaded_cp_RW,pin(loaded_input_gate['whole_original_input_page'],loaded_input_gate['whole_original_input_page_sha256']).read_bytes(),'Actual original transport bootstrap equals entire independently reviewed physical input')
  domain_path=loaded_input_gate_path.parent/'input-domain.json';loaded_input_domain=json.loads(pin(domain_path,loaded_input_gate['files'][str(domain_path.resolve())]).read_bytes())
  loaded_input_differences=delta(loaded_cp_RW,loaded_cp_native_RW)
  equal(loaded_input_differences,loaded_input_domain['differences'],'Complete actual71-byte input difference list; no page wildcard')
  need(len(loaded_cp_native_RW)==4096 and words(loaded_cp_native_RW,0x658)[0]==2 and loaded_cp_native_RW[0x640:0x658]==loaded_cp_RW[0x640:0x658],'Whole native genuine bootstrap page and identical reached CS24/state2 fields')
  loaded_input_relation_sha=sha(loaded_input_gate_path)
'''
assert source.count(old) == 1
source = source.replace(old, old + extra)
old = "        equal(original,loaded_cp_RW,'Whole original balanced root checkpoint restores genuine loaded CS24/page');equal(actual,loaded_cp_RW,'Whole native balanced root checkpoint preserves identical genuine loaded opaque page input');counts['Lockit_whole_loaded_RW_page_relations']+=1"
new = "        equal(original,loaded_cp_RW,'Whole original balanced root checkpoint carries its genuine complete bootstrap page');equal(actual,loaded_cp_native_RW,'Whole native balanced root checkpoint carries its genuine complete bootstrap page');equal(differences,loaded_input_differences,'Every exact input difference byte/value retained at every endpoint');declared.update(r['offset']for r in loaded_input_differences);counts['Lockit_whole_loaded_RW_page_relations']+=1;counts['whole_exact_loaded_input_endpoint_relations']+=1"
assert source.count(old) == 1
source = source.replace(old, new)
old = "len(provider_page_rows)==9000,'Complete full124 paired coverage and allnewroot bounded contracts')"
new = "len(provider_page_rows)==9000 and counts['whole_exact_loaded_input_endpoint_relations']==3000,'Complete full125 paired coverage and allnewroot bounded contracts')"
assert source.count(old) == 1
source = source.replace(old, new)
old = "Lockit_opaque_loaded_bytes_masked=False,Lockit_exact_original_API_observer_targets="
new = "Lockit_opaque_loaded_bytes_masked=False,loaded_input_relation_report_sha256=locals().get('loaded_input_relation_sha'),loaded_input_difference_bytes=71,loaded_input_difference_DWORDs=25,loaded_input_opaque_pointer_targets_proven=False,loaded_input_native_DllMain_credit=False,Lockit_exact_original_API_observer_targets="
assert source.count(old) == 1
source = source.replace(old, new)
output = Path(__file__).with_name('paired_v4.py')
assert not output.exists()
output.write_text(source)
