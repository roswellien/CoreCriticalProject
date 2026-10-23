"""Immutable constructorNULL union observer preparation; ROOT independently admits."""
from pathlib import Path
import ast,json,hashlib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-141-consumer-review/container-union-preparation-r1';dest=R/'reports/m4-startup141-source/preparation-r9';dest.mkdir();files={}
 def pin(p,expected=None):
  p=Path(p).resolve();h=sha(p);assert expected is None or h==expected;files[str(p)]=h;return p
 def inverse(child,parent,delta,count):
  text=pin(child).read_text();rows=json.loads(pin(delta).read_bytes());assert len(rows)==count
  for d in reversed(rows):assert text.count(d['new'])==d['count'];text=text.replace(d['new'],d['old'])
  assert text==pin(parent).read_text();ast.parse(Path(child).read_text())
 model=R/'tools/m4-native141-source/container_events141_v1.py';observer=R/'tools/m4-native141-source/final_observer141_v12.py'
 inverse(model,R/'tools/m4-vtable-review/event_model.py',out/'model-deltas.json',4)
 inverse(observer,R/'tools/m4-native141-source/final_observer141_v11.py',out/'observer-deltas.json',5)
 parent=R/'reports/m4-startup141-source/preparation-r8';pin(parent/'report.json','01a6415bf94b2860d4986bfb2eeff160c23586c81cf37451cd53605173e2e58d')
 driver=pin(parent/'compare_provider141.py');t=driver.read_text();a='final_observer141_v11.py';b='final_observer141_v12.py';assert t.count(a)==1;t=t.replace(a,b);assert t.replace(b,a)==driver.read_text();ast.parse(t)
 p=dest/'compare_provider141.py';p.write_text(t);pin(p)
 p=dest/'paired_exports.py';p.write_bytes(pin(parent/'paired_exports.py').read_bytes());pin(p)
 edits=json.loads(pin(parent/'driver-deltas.json').read_bytes());assert len(edits)==28;matches=[d for d in edits if a in d['new']];assert len(matches)==1;matches[0]['new']=matches[0]['new'].replace(a,b)
 reverse=t
 for d in reversed(edits):assert reverse.count(d['new'])==d['count'];reverse=reverse.replace(d['new'],d['old'])
 assert reverse==pin(R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py').read_text()
 p=dest/'driver-deltas.json';p.write_text(json.dumps(edits,indent=2)+'\n');pin(p)
 pin(R/'reports/m4-141-consumer-review/container-union-controls-r1/report.json','0abe2f2c5ce4281b55dab415565fab7aca6ac4ad78c8ab0768c3e474f13a7d9b');pin(R/'tools/m4-141-consumer-review/container_union_controls_v1.py')
 pin(R/'reports/m4-startup141-source/combined-source-provider-r5/report.json','bb69cea46ef7bd55861695c9d4f4fc4a133ba158f8dd95bcf834cf4141230f55');pin(R/'reports/m4-startup141-source/combined-source-provider-r5/Constructor-carried-source-derivations.json')
 pin(R/'reports/m4-141-consumer-review/root-container-diagnostic-r1/report.json','3c9b0d11b66e6a2d200a6a6347bc5a47ccdac8a7499ff7f4bc29d4f0d6fea374')
 for n in('rows.json','container-nullfree-witnesses.bin','container-borrowed-witnesses.bin','container-import-ledger.bin','container-vector-stores.bin'):pin(R/'reports/m4-141-consumer-review/root-container-diagnostic-r1'/n)
 for n in('container_operations.inc','session_impl.inc','vtable_operations.inc'):
  p=R/'reports/m4-startup141-runway/service-preparation-r2'/n
  if p.exists():pin(p)
 pin(R/'tools/m4-vtable-review/vtable_model.py');pin(R/'tools/m4-native141-source/constructor_journal141_v2.py');pin(R/'tools/m4-native141-source/mfc_chronology141_v2.py');pin(__file__)
 findings=dict(NULL_native_domain='Two constructor calls inherit Binding registry_root=0 from actual borrowed provider scope; model retains exact separate logical roots4103f0/410440',whole_NULL_witnesses=7,inherited_NULL_witnesses=5,constructor_NULL_witnesses=2,whole_import_rows=17,whole_borrowed_witnesses=3,whole_vector_stores=17,provider_access_indices='Unchanged len(m.accesses) during exact Association provider callback, including shared CALL write and every borrowed source operand. No constant offset or captured row index feeds source.',vtable_scope='VtableEvents.event returns for roots outside recovered six owning call roots. All three new constructor roots are excluded; genuine constructor getters independently compared in component outputs. Existing6 calls/full32Q, stores/full16Q and all probes unchanged.',remaining_runtime_gates='Whole current source execution all12 cases; selected and cleaned container7/null owner/API/generation/FS conservation, complete imports17, borrowed3/vector17 and vtable6 full probes; no result inferred from controls.')
 report=dict(passed=True,prepared_only=True,source_only=True,model_deltas=4,observer_deltas=5,driver_binding_deltas=1,composed_driver_deltas=28,exact_inverse=True,controls=101,findings=findings,entrypoint=str(dest/'compare_provider141.py'),observer=str(observer),helper=str(model),pre_audit_helper_pin=True,no_constant_shift=True,AFTER_seed=False,canonical_reader_opened=False,consumer_executed=False,ROOT_independent_admission_required=True,admitted=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 (dest/'report.json').write_text(json.dumps({**report,'container_union_preparation':str(out/'report.json'),'container_union_preparation_sha256':sha(out/'report.json')},indent=2)+'\n')
 print(json.dumps(dict(review=str(out/'report.json'),review_sha256=sha(out/'report.json'),preparation=str(dest/'report.json'),preparation_sha256=sha(dest/'report.json'))))
if __name__=='__main__':main()
