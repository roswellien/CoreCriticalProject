"""Rebind own-BEFORE comparers to the exact capacity-corrected candidate."""
from pathlib import Path
import ast, hashlib, json
P=Path(__file__).resolve().parent
changes=[('fixture-build-r10','fixture-build-r11'),('fixture-preparation-r10','fixture-preparation-r12'),('4c4c5210af1388dc4721c39e4b70cc7505205863bd5015d6d89bd00fb5da1f76','004b2a21b58d1ac10d3b96a8726e092b8ada0fac2855f8ef358b16cea0f087bb'),('0dc60d24b135d33b11d336db0ccce7a37c0a07ee676d63742f3413d722861a54','209b73cd3d16280ca4173ec3f0ac0186681b4415a2b8b81c79aa46a634e96abb'),('compare_prefix_v2.py','compare_prefix_v3.py'),('compare_registry_v2.py','compare_registry_v3.py')]
for before,after in [('compare_prefix_v2.py','compare_prefix_v3.py'),('compare_registry_v2.py','compare_registry_v3.py')]:
 p=P/before;s=p.read_text()
 for old,new in changes:s=s.replace(old,new)
 if before=='compare_registry_v2.py':
  anchor="  e=read(execution,execution_sha);p=read(prefix_path,prefix_sha);"
  assert s.count(anchor)==1
  s=s.replace(anchor,"  pin(C.__file__);e=read(execution,execution_sha);p=read(prefix_path,prefix_sha);")
 ast.parse(s);q=P/after;assert not q.exists();q.write_text(s)
 print(json.dumps(dict(source=str(p),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),output=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),executed=False)))
