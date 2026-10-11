"""Preserve failed execution controller and bind corrected contiguous evidence."""
from pathlib import Path
import ast, hashlib, json
P=Path(__file__).resolve().parent
prior=P/'run_fixture_v2.py'
s=prior.read_text()
replacements=[('fixture-build-r9','fixture-build-r10'),('fixture-preparation-r9','fixture-preparation-r10'),('4bd792e4cac56bfce6a635f53ff2cf5d0030e50572169e75d03bbcf977bb9e60','4c4c5210af1388dc4721c39e4b70cc7505205863bd5015d6d89bd00fb5da1f76'),('c761842bfb644d9bf6ec943f5c8c686facb5bc7efd1c4da2fd7151e15a112eb9','0dc60d24b135d33b11d336db0ccce7a37c0a07ee676d63742f3413d722861a54')]
for old,new in replacements:
 assert old in s,old
 s=s.replace(old,new)
ast.parse(s)
out=P/'run_fixture_v3.py';assert not out.exists();out.write_text(s)
print(json.dumps(dict(path=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),exact_replacements=replacements,executed=False)))
