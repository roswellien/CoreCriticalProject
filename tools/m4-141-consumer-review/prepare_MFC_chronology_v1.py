"""Seal immutable source-only MFC chronological union derivative; ROOT admission required."""
from pathlib import Path
import ast,json,hashlib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-141-consumer-review/MFC-chronology-preparation-r1';dest=R/'reports/m4-startup141-source/preparation-r7';dest.mkdir()
 files={}
 def pin(p,expected=None):
  p=Path(p).resolve();digest=sha(p);assert expected is None or digest==expected;files[str(p)]=digest;return p
 observer=pin(R/'tools/m4-native141-source/final_observer141_v10.py');old=pin(R/'tools/m4-native141-source/final_observer141_v9.py');helper=pin(R/'tools/m4-native141-source/mfc_chronology141_v1.py')
 delta=pin(out/'observer-deltas.json');deltas=json.loads(delta.read_bytes());assert len(deltas)==6
 reverse=observer.read_text()
 for d in reversed(deltas):assert reverse.count(d['new'])==d['count'];reverse=reverse.replace(d['new'],d['old'])
 assert reverse==old.read_text();ast.parse(observer.read_text());ast.parse(helper.read_text())
 parent=R/'reports/m4-startup141-source/preparation-r6';pin(parent/'report.json','08f2ea8a1940bfd20c4b3036a834fccd1b4330093d35751499607089a6e2058c')
 driver=pin(parent/'compare_provider141.py');text=driver.read_text();a='final_observer141_v9.py';b='final_observer141_v10.py';assert text.count(a)==1;text=text.replace(a,b);assert text.replace(b,a)==driver.read_text();ast.parse(text)
 p=dest/'compare_provider141.py';p.write_text(text);pin(p)
 p=dest/'paired_exports.py';p.write_bytes(pin(parent/'paired_exports.py').read_bytes());pin(p)
 composed=json.loads(pin(parent/'driver-deltas.json').read_bytes());assert len(composed)==28
 matches=[d for d in composed if a in d['new']];assert len(matches)==1;matches[0]['new']=matches[0]['new'].replace(a,b)
 reverse=text
 for d in reversed(composed):assert reverse.count(d['new'])==d['count'];reverse=reverse.replace(d['new'],d['old'])
 assert reverse==pin(R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py').read_text()
 p=dest/'driver-deltas.json';p.write_text(json.dumps(composed,indent=2)+'\n');pin(p)
 pin(R/'reports/m4-141-consumer-review/MFC-chronology-controls-r2/report.json','b04e3c6daf117cc2c2d01b26829f4865ad17535f8ea73e5bfe4b83d243a4ccf9');pin(R/'tools/m4-141-consumer-review/MFC_chronology_controls_v2.py')
 pin(R/'reports/m4-startup141-source/combined-source-provider-r3/report.json','dbdab5b591938247c13c0b42c0f2568e61dd29d821709a0f440210d91d777c93')
 for name in('Formatting-source-derivations.json','Constructor-carried-source-derivations.json','failure.txt'):pin(R/'reports/m4-startup141-source/combined-source-provider-r3'/name)
 for name in('mfc_operations.inc','fs_operations.inc','session_impl.inc','container_operations.inc','constructor-FS-contracts.json'):pin(R/'reports/m4-startup141-runway/service-preparation-r2'/name)
 pin(R/'tools/m4-formatting-source/formatting_derivations.py');pin(R/'tools/m4-tree-source/final_observer125_v2.py');pin(R/'reports/m4-native141-source/observer-preparation-r5/final_observer141_parent.py');pin(R/'reports/m4-native141-source/observer-preparation-r5/final_observer141_parent_v2.py')
 pin(R/'reports/m4-startup141-root/validation-r1/report.json','00406b1d901fe996e0d15f9281048ff6222d6bae5ceaf1d3e721b5d0f271d610');pin(__file__)
 report=dict(passed=True,prepared_only=True,source_only=True,immediate_observer_deltas=6,immediate_driver_deltas=1,composed_source6_driver_deltas=28,exact_inverse=True,inherited_MFC_domain=68,constructor_MFC_domain=6,chronological_MFC_union=74,source_ordinal_producer='One actual source positive ordinal823 JMP appends same source record; every raw823 import uses current source count before entry. NULL825 never appends.',constructor_witness_fields='Whole32Q source entry frame/root0/ECX; actual malloc+handler raw reads; exact CALL EBX frame; actual malloc owner acquired/generation/extent; actual823 RET; genuine825 named free/frame/RET. No captured row feeds source fields.',full_compare='All74 complete32Q+all chronological8Q imports/stores, retained requested bytes/publication assertions, unchanged container and vtable dump checks; no filtering/masking.',formatting_compare_unchanged=True,no_constant_shift=True,AFTER_seed=False,entrypoint=str(dest/'compare_provider141.py'),observer=str(observer),helper=str(helper),pre_audit_helper_pin=True,reviewer_authored_driver=True,ROOT_independent_admission_required=True,admitted=False,canonical_reader_opened=False,consumer_executed=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 (dest/'report.json').write_text(json.dumps({**report,'MFC_chronology_preparation':str(out/'report.json'),'MFC_chronology_preparation_sha256':sha(out/'report.json')},indent=2)+'\n')
 print(json.dumps(dict(review=str(out/'report.json'),review_sha256=sha(out/'report.json'),preparation=str(dest/'report.json'),preparation_sha256=sha(dest/'report.json'))))
if __name__=='__main__':main()
