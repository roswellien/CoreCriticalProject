"""Seal current52 source comparers; literal source tables stay fixed."""
from pathlib import Path
P=Path(__file__).resolve().parent;generator=P/'prepare_source_comparison_v4.py';s=generator.read_text()
changes=[('compare_prefix_v3.py','compare_prefix_v4.py'),('compare_registry_v3.py','compare_registry_v4.py'),('fixture-preparation-r12','fixture-preparation-r16'),('fixture-build-r11','fixture-build-r13'),('209b73cd3d16280ca4173ec3f0ac0186681b4415a2b8b81c79aa46a634e96abb','58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401'),('004b2a21b58d1ac10d3b96a8726e092b8ada0fac2855f8ef358b16cea0f087bb','036d33c85494a29c358a4d7e2016606bbdb9290316be52ac2ae32b07f96a3d98'),('run_fixture_v4.py','run_fixture_v5.py'),('derive_controller_v4.py','derive_bindings52_v1.py')]
for a,b in changes:s=s.replace(a,b)
a="module.pin(P/'derive_source_comparison_v4.py');module.pin(prior);module.pin(__file__)"
b="module.pin(P/'derive_source_comparison_v4.py');module.pin(P/'derive_bindings52_v1.py');module.pin(P/'prepare_source_comparison_v4.py');module.pin(prior);module.pin(__file__)"
assert s.count(a)==1
exec(compile(s.replace(a,b),str(generator),'exec'),globals())
