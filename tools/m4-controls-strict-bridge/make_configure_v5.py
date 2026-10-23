"""Derive configure_acceptance138_v5.py from configure_acceptance138_v4.py by exact byte deltas.

v5 consumes bindings with field_sources (per-predicate pinned ROOT measurement reports,
the proposal6 rows' current_report_path) and records them in each configured gate as
'sources' for acceptance138_v6. Each source must match its SHA and report passed, and
every given source must be used exactly. Proves the inverse back to v4 before writing.
"""
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[2]
src=R/'tools/m4-controls-strict-bridge/configure_acceptance138_v4.py';dst=R/'tools/m4-controls-strict-bridge/configure_acceptance138_v5.py'
b=src.read_bytes()
NL=b'\n'
DELTAS=[
 (b'"""Freeze explicitly bound completed gates; no unresolved identity defaults.',
  b'"""Freeze explicitly bound completed gates; no unresolved identity defaults (v5: per-predicate pinned measurement sources for acceptance138_v6).'),
 (b'import acceptance138_v4 as A',b'import acceptance138_v6 as A'),
 (b"def need(v,label):A.need(v,label)"+NL,
  b"def need(v,label):A.need(v,label)"+NL+
  b"def source_report(given,target,pins):"+NL+
  b" row=given[target];need(set(row)=={'path','sha256'},'Exact per-predicate source '+target);p=(R/row['path']).resolve();need(sha(p)==row['sha256'],'Whole per-predicate source identity '+str(p))"+NL+
  b" report=json.loads(p.read_bytes(),object_pairs_hook=A.unique_object);need(report.get('passed')is True,'Passed per-predicate source '+str(p));pins[str(p)]=row['sha256'];return report"+NL),
 (b"need(set(bindings)=={'gates','field_translations'},'Exact39-gate binding/translation schema')",
  b"need(set(bindings)=={'gates','field_translations','field_sources'}and set(bindings['field_sources'])<=A.REQUIRED,'Exact39-gate binding/translation/source schema')"),
 (b"equal=facets(row);gates[label]=dict(path=b['path'],sha256=b['sha256'],equal=equal)",
  b"equal=facets(row);sources={};given_sources=bindings['field_sources'].get(label,{});gates[label]=dict(path=b['path'],sha256=b['sha256'],equal=equal,sources=sources)"),
 (b"value=A.value_at(row,target);",b"value=A.value_at(source_report(given_sources,target,pins)if target in given_sources else row,target);"),
 (b"    equal[target]=value;coverage[label][field]=relation"+NL,
  b"    equal[target]=value;coverage[label][field]=relation"+NL+
  b"    if target in given_sources:sources[target]=dict(given_sources[target])"+NL),
 (b" need(set(bindings['field_translations'])<=A.BASE_REQUIRED,'Translations only retained accepted gates')",
  b" need(all(set(bindings['field_sources'].get(label,{}))==set(gate['sources'])for label,gate in gates.items()),'Every per-predicate source used exactly once by its predicate')"+NL+
  b" need(set(bindings['field_translations'])<=A.BASE_REQUIRED,'Translations only retained accepted gates')"),
]
CRLF=b'\r'+NL
if CRLF in b:DELTAS=[(x.replace(NL,CRLF),y.replace(NL,CRLF))for x,y in DELTAS]
s=b
for a,c in DELTAS:assert s.count(a)==1,(a[:80],s.count(a));s=s.replace(a,c)
inv=s
for a,c in reversed(DELTAS):assert inv.count(c)==1,c[:60];inv=inv.replace(c,a)
assert inv==b,'Exact inverse to configure_acceptance138_v4'
assert not dst.exists();dst.write_bytes(s);ast.parse(s.decode());print('wrote',dst)
