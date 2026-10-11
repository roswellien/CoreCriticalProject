"""Bind corrected evidence and derive finite API names from literal contracts."""
from pathlib import Path
import ast,hashlib,json
P=Path(__file__).resolve().parent
replacements=[('fixture-build-r9','fixture-build-r10'),('fixture-preparation-r9','fixture-preparation-r10'),('4bd792e4cac56bfce6a635f53ff2cf5d0030e50572169e75d03bbcf977bb9e60','4c4c5210af1388dc4721c39e4b70cc7505205863bd5015d6d89bd00fb5da1f76'),('c761842bfb644d9bf6ec943f5c8c686facb5bc7efd1c4da2fd7151e15a112eb9','0dc60d24b135d33b11d336db0ccce7a37c0a07ee676d63742f3413d722861a54'),('compare_prefix.py','compare_prefix_v2.py'),('compare_registry.py','compare_registry_v2.py'),('run_fixture_v2.py','run_fixture_v3.py')]
for source,target in [('compare_prefix.py','compare_prefix_v2.py'),('compare_registry.py','compare_registry_v2.py')]:
 p=P/source;s=p.read_text()
 for old,new in replacements:s=s.replace(old,new)
 if source=='compare_registry.py':
  anchor="  values.append(dict(words=w,buffers=buffers,inputs=payload('input'),outputs=payload('output')))"
  changed="  sys.path.insert(0,str(R/'tools/m4-onexit-review'));import provider_responses_v2 as typed\n  contracts=typed.B.contracts();contracts.update(typed.NEW_CONTRACTS)\n  if w[31]==1:\n   need(w[2]==0 and w[3]==0x78146190,'Exact named bootstrap association');name_='MSVCP-resource-association'\n  else:\n   need(w[2]in contracts,'Every actual API has a recovered literal contract');name_=contracts[w[2]]['name']\n  values.append(dict(words=w,buffers=buffers,inputs=payload('input'),outputs=payload('output'),name=name_))"
  assert s.count(anchor)==1;s=s.replace(anchor,changed)
 ast.parse(s);q=P/target;assert not q.exists();q.write_text(s)
 print(json.dumps(dict(source=str(p),source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),output=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),executed=False)))
