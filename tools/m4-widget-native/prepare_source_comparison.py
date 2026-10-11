"""Seal pure comparison tools/static source contracts without worker execution."""
from pathlib import Path
import ast,collections,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-widget-native'/name;need(not out.exists(),'Fresh pure source preparation');out.mkdir()
 path=R/'tools/m4-widget-native/compare_prefix.py';spec=importlib.util.spec_from_file_location('widget_comparison_preparation',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.pin(path);G=module.load(R/'reports/m4-font479590-original/source-preparation-r1/game_model.py','widget_comparison_literal');program,callbacks=G.source_program();module.load(R/'tools/m4-formatting-source/flag_domain.py','widget_comparison_definedness')
 c=module.read(R/'reports/m4-widget-native/preparation-r3/contracts.json');p=module.read(R/'reports/m4-widget-native/preparation-r3/report.json','69a29eddf46f6c189edc462e5f5734a96e3d98c2c1f37778a54d36c0fd62eae5');tail=module.read(R/'reports/m4-widget-original-review/registration-tail-r1/report.json','abaa48c8dd533c56cdbd48118676bf0800f0c942ce9319a537a03c4c4b4f3cb5');need(p['passed']and tail['passed'],'Physically retained component and independent source tail')
 byPC={row['pc']:row for row in c['instructions']}
 for pc,row in byPC.items():need(program[pc]==row,'Current pure literal graph exact '+hex(pc))
 for path in ('tools/m4-widget-native/run_fixture_v2.py','tools/m4-widget-native/derive_controller_v2.py','tools/m4-widget-native/component_v2.cpp','tools/m4-widget-native/borrowed_onexit_v2.inc','tools/m4-widget-native/fixture_v4.cpp'):
  module.pin(R/path)
  if path.endswith('.py'):ast.parse((R/path).read_text())
 module.pin(__file__);module.pin(sys.executable)
 for q in list(module.READS):module.pin(q)
 need(module.READS<=set(module.PINS),'Complete actually opened static source chain')
 policy=dict(source_roots=[r['root']for r in c['roots']],component_preparation_sha256=sha(R/'reports/m4-widget-native/preparation-r3/report.json'),fixture_preparation_sha256='c761842bfb644d9bf6ec943f5c8c686facb5bc7efd1c4da2fd7151e15a112eb9',fixture_build_sha256='4bd792e4cac56bfce6a635f53ff2cf5d0030e50572169e75d03bbcf977bb9e60',current_controller=str(R/'tools/m4-widget-native/run_fixture_v2.py'),current_controller_sha256=sha(R/'tools/m4-widget-native/run_fixture_v2.py'),comparison=str(R/'tools/m4-widget-native/compare_prefix.py'),comparison_sha256=sha(R/'tools/m4-widget-native/compare_prefix.py'),comparison_input='Each actual native branch own entry State3504/CPU40/FX512, phase BEFORE complete game mappings/stack/minimal TIB and actual GDI scalar/typed-handle API response rows',comparison_terminal=0x78004a36,expected_observed_prefix_operands_per_level=24625,literal_tail_operands_per_level=18,source_provider_tail_full_comparison=False,source_shutdown_execution=False,cold_or_GDI_failure_admission=False,original_result_or_memory_seed=False)
 q=out/'comparison-policy.json';q.write_text(json.dumps(policy,indent=2)+'\n');module.pin(q)
 report=dict(passed=True,scope='Prepared exact own-BEFORE widget literal prefix comparison and review-bound worker controller; no workers or source comparison executed',physical_widget_rows=len(byPC),source_prefix_roots=len(c['roots']),static_program_rows=len(program),actual_successful_static_read_dependencies=len(module.READS),all_successful_static_dependencies_pinned=True,omitted_optional_read_paths=sorted(module.OPTIONAL),native_executed=False,source_native_equality=False,registration_provider_source_comparison=False,full_root_return_source_comparison=False,initializer_credit=0,archive_reader_opened=False,files=module.PINS)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True,static_inputs=len(module.PINS))))
if __name__=='__main__':main(sys.argv[1])
