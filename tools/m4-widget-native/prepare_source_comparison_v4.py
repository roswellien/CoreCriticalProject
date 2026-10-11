"""Seal the capacity-corrected source comparison preparation, without execution."""
from pathlib import Path
P=Path(__file__).resolve().parent
prior=P/'prepare_source_comparison_v3.py';source=prior.read_text()
for old,new in [('compare_prefix_v2.py','compare_prefix_v3.py'),('compare_registry_v2.py','compare_registry_v3.py'),('fixture-preparation-r10','fixture-preparation-r12'),('fixture-build-r10','fixture-build-r11'),('0dc60d24b135d33b11d336db0ccce7a37c0a07ee676d63742f3413d722861a54','209b73cd3d16280ca4173ec3f0ac0186681b4415a2b8b81c79aa46a634e96abb'),('4c4c5210af1388dc4721c39e4b70cc7505205863bd5015d6d89bd00fb5da1f76','004b2a21b58d1ac10d3b96a8726e092b8ada0fac2855f8ef358b16cea0f087bb'),('run_fixture_v3.py','run_fixture_v4.py'),('derive_controller_v3.py','derive_controller_v4.py')]:source=source.replace(old,new)
# The inherited wrapper's replacement recipe starts from the original baseline.
# Replace its baseline replacement destinations too, then preserve the entire
# immutable recipe chain as physical inputs to the new preparatory receipt.
source=source.replace("module.pin(P/'derive_source_comparison_v3.py');module.pin(__file__)","module.pin(P/'derive_source_comparison_v3.py');module.pin(P/'derive_source_comparison_v4.py');module.pin(prior);module.pin(__file__)")
exec(compile(source,str(prior),'exec'),globals())
