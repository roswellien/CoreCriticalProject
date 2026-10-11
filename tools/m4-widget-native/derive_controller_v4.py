"""Bind corrected service guards while preserving both actual failed workers."""
from pathlib import Path
import ast,hashlib,json
P=Path(__file__).resolve().parent;prior=P/'run_fixture_v3.py';s=prior.read_text()
changes=[('fixture-build-r10','fixture-build-r11'),('fixture-preparation-r10','fixture-preparation-r12'),('4c4c5210af1388dc4721c39e4b70cc7505205863bd5015d6d89bd00fb5da1f76','004b2a21b58d1ac10d3b96a8726e092b8ada0fac2855f8ef358b16cea0f087bb'),('0dc60d24b135d33b11d336db0ccce7a37c0a07ee676d63742f3413d722861a54','209b73cd3d16280ca4173ec3f0ac0186681b4415a2b8b81c79aa46a634e96abb')]
for a,b in changes:assert a in s;s=s.replace(a,b)
ast.parse(s);out=P/'run_fixture_v4.py';assert not out.exists();out.write_text(s)
print(json.dumps(dict(path=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),prior=str(prior),prior_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),exact_changes=changes,executed=False)))
