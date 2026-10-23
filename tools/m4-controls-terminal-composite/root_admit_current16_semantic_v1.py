"""ROOT finite current16 policy admission; durable raw union remains separate."""
from pathlib import Path
import hashlib,importlib.util,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;assert pins.setdefault(str(p),v)==v;return p
 code=pin(R/'tools/m4-controls-terminal-composite/current16_semantic_v2.py','9b9f5d35c8eb0fac2fe16ca118dd8f48330e832b3a440ce927644365b31f735a')
 checker=pin(R/'tools/m4-joint-startup138/check_context_controls_v4.py','5a6b673cad65db1b0c64329c57f5525df0634d70f39165712707dee8151b006e')
 header=pin(R/'tools/m4-138-controls-review/readiness.py');spec=importlib.util.spec_from_file_location('ROOT_bounded_executed_header',header);reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
 semantic=pin(R/'reports/m4-joint-startup138/context-controls-verification-r1/report.json','88e0a18bc8b32fb70c3fd460c828c44127613662fd4467cf3385ae78b56861cb');H=reader.header(semantic)
 fullraw=pin(R/'reports/m4-138-controls-review/full-raw-inventory-review-r1/report.json','2a0086d81039912923fb6f9ed294ea851098ae7e5078fc96faf5f0c246b63035');F=json.loads(fullraw.read_bytes())
 assert F['passed'] is True and F['all_bounded_readers_closed'] is True and F['raw_export_readers_closed'] is True and F['proof_inventory']['sqlite_closed_before_hash'] is True
 assert F['counts']['whole_export_targets_authenticated']==10691866 and F['counts']['final_integrity_files_rehashed']==10697242
 inventory=F['proof_inventory'];assert F['files'][inventory['path']]==inventory['sha256'];db=pin(inventory['path'],inventory['sha256']);assert db.stat().st_size==inventory['bytes'] and inventory['physical_rows']==10697242
 sources={
 'reports/m4-joint-startup138/context-controls-verification-r1/actual-Context-causes.json':'05aa8414254e6605d57f8c8cdd23dbead21980415fd5db2e7a3799172759082b',
 'reports/m4-138-controls-review/raw-witnesses-r1/report.json':'e6d81728fe07075576e1b3d9cbde174f1829bcf008de0989d51573d3f1b074c0',
 'reports/m4-138-controls-review/gdi-owners-r1/report.json':'31f295d7128be8c0cef31bd8c9358f74055b8d3d736476881a858fde51f58c15',
 'reports/m4-138-controls-review/equivalence-r1/report.json':'e46f3f2a8ad63ac3ed6f229cfbcbaecc2238a42758d0195b0684a97a53c4f0cf',
 'reports/m4-138-controls-review/current-link-join-r1/report.json':'a1f3aa8e0203af187b2d8cdbcc315792c0eb330c40c9ec67ebf2f1ade0d4e87f',
 'reports/m4-controls-terminal-composite/root-role-rawroot-controls-r1/report.json':'1f145dea07b5f0eb57039600f88f532488ce191fb534489ad0992cb4c052ed99'}
 for path,h in sources.items():pin(R/path,h)
 for path in ('tools/m4-joint-startup138/controls_main.cpp','tools/m4-runtime/runtime.cpp','runtime/memory/guest_memory.cpp','reports/m4-fps-native/connected-component-preparation-r4/component.cpp','reports/m4-fps-native/connected-component-preparation-r4/contracts.json','reports/m4-fps-native/connected-component-preparation-r4/literals.hpp','tools/m4-widget-growth-review/gdi_identity.py'):pin(R/path)
 # Exact source semantics scope: committed writes use observed operands; own
 # read payloads, fault mutation, denied writes, live generations and manual
 # native DeleteObject predicates are independently checked finite relations.
 text=checker.read_text();assert 'else:store(faultmap,address,value.to_bytes' in text and "eq(w[:5],f[:5]" in text and "eq(new,old[:6]+(0,)" in text
 assert H['passed'] is True and H['counts']['exact_causal_source_operand_prefix_rows']==966 and H['counts']['actual_owned_font_cleanup_calls']==240
 pin(__file__)
 for p,h in pins.items():assert sha(p)==h
 out=R/'reports/m4-controls-terminal-composite/root-current16-policy-admission-r1';assert not out.exists();out.mkdir();q=out/'report.json'
 q.write_text(json.dumps(dict(passed=True,current16_source_policy_admitted=True,executed_checker4_semantic_sha256=sha(semantic),executed_checker4_semantic_header=H,current16_fullraw_report=str(fullraw),current16_fullraw_sha256=sha(fullraw),manual_cleanup_finite_policy_reviewed=True,final_named_owner_entry64_scope_reviewed=True,committed_source_write_values_independently_instruction_evaluated=False,whole_fault_memory_fully_source_predicted=False,whole_current138_positive_semantic_equivalence_claim=False,raw_inventory_expanded=False,accepted_function_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
