"""Rebind immutable source comparers/controller to precise52 compiled candidate."""
from pathlib import Path
import ast,hashlib,json
P=Path(__file__).resolve().parent;R=P.parents[1]
changes=[('fixture-preparation-r12','fixture-preparation-r16'),('fixture-build-r11','fixture-build-r13'),('209b73cd3d16280ca4173ec3f0ac0186681b4415a2b8b81c79aa46a634e96abb','58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401'),('004b2a21b58d1ac10d3b96a8726e092b8ada0fac2855f8ef358b16cea0f087bb','036d33c85494a29c358a4d7e2016606bbdb9290316be52ac2ae32b07f96a3d98'),('compare_prefix_v3.py','compare_prefix_v4.py')]
relations=[]
for a,b in [('run_fixture_v4.py','run_fixture_v5.py'),('compare_prefix_v3.py','compare_prefix_v4.py'),('compare_registry_v3.py','compare_registry_v4.py')]:
 before=P/a;raw=before.read_text();s=raw
 for old,new in changes:s=s.replace(old,new)
 if a.startswith('run_'):assert s.count('(1,1,6,51,0,0,0,0)')==1;s=s.replace('(1,1,6,51,0,0,0,0)','(1,1,6,52,0,0,0,0)')
 ast.parse(s);out=P/b;assert not out.exists();out.write_text(s)
 relations.append(dict(prior_path=str(before),prior_sha256=hashlib.sha256(before.read_bytes()).hexdigest(),current_path=str(out),current_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),permitted_changes=changes+([['(1,1,6,51,0,0,0,0)','(1,1,6,52,0,0,0,0)']]if a.startswith('run_')else[])))
f=R/'reports/m4-widget-native/bindings52-preparation-r1';assert not f.exists();f.mkdir();report=dict(passed=True,scope='Pure current52 controller/comparer pin derivation; no workers or semantic comparisons executed',relations=relations,source_semantic_guards_changed=False,native_executed=False,initializer_credit=0);q=f/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(q,hashlib.sha256(q.read_bytes()).hexdigest())
