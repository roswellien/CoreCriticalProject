"""Seal corrected current bindings and bounded provider fact naming."""
from pathlib import Path
P=Path(__file__).resolve().parent
prior=P/'prepare_source_comparison.py';source=prior.read_text()
for old,new in [('compare_prefix.py','compare_prefix_v2.py'),('fixture-preparation-r9','fixture-preparation-r10'),('fixture-build-r9','fixture-build-r10'),('c761842bfb644d9bf6ec943f5c8c686facb5bc7efd1c4da2fd7151e15a112eb9','0dc60d24b135d33b11d336db0ccce7a37c0a07ee676d63742f3413d722861a54'),('4bd792e4cac56bfce6a635f53ff2cf5d0030e50572169e75d03bbcf977bb9e60','4c4c5210af1388dc4721c39e4b70cc7505205863bd5015d6d89bd00fb5da1f76'),('run_fixture_v2.py','run_fixture_v3.py'),('derive_controller_v2.py','derive_controller_v3.py')]:source=source.replace(old,new)
anchor='module.pin(path);G=module.load'
replacement="module.pin(path);registry=R/'tools/m4-widget-native/compare_registry_v2.py';ast.parse(registry.read_text());module.pin(registry);sys.path.insert(0,str(R/'tools/m4-onexit-review'));import provider_responses_v2 as provider_responses;provider_responses.B.contracts();G=module.load"
assert source.count(anchor)==1;source=source.replace(anchor,replacement)
source=source.replace('source_provider_tail_full_comparison=False','source_provider_tail_full_comparison_prepared=True,source_provider_tail_comparison=str(registry),source_provider_tail_comparison_sha256=sha(registry),source_provider_tail_full_comparison_executed=False')
source=source.replace('module.pin(__file__);module.pin(sys.executable)',"module.pin(prior);module.pin(P/'prepare_source_comparison_v2.py');module.pin(P/'derive_source_comparison_v3.py');module.pin(__file__);module.pin(sys.executable)")
exec(compile(source,str(prior),'exec'),globals())
