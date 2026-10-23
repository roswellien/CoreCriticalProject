"""Derive prepare_postterminal_templates_v2.py from v1 by exact byte deltas.

v2's bindings stage accepts the ROOT all39 review's per-field pinned sources (measured
fields whose current value lives in a separate ROOT measurement report) and emits them
as field_sources for configure_acceptance138_v5. The final45 stage is unchanged.
Proves the inverse back to v1 before writing.
"""
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[2]
src=R/'tools/m4-controls-terminal-composite/prepare_postterminal_templates_v1.py';dst=R/'tools/m4-controls-terminal-composite/prepare_postterminal_templates_v2.py'
b=src.read_bytes()
NL=b'\n'
DELTAS=[
 (b'"""UNEXECUTED two-stage data templates; never finalizer/config/checker/allowance."""',
  b'"""Two-stage data templates (v2: bindings carry per-field pinned ROOT measurement sources); never finalizer/config/checker/allowance."""'),
 (b"value=measured['fields'][row['current_field']];assert P.typed(value,row['current_expected'])",
  b"value=measured['fields'][row['current_field']];assert P.typed(value,row['current_expected'])"+NL+
  b"  source=measured.get('sources',{}).get(row['current_field'])"+NL+
  b"  if source is not None:assert set(source)=={'path','sha256'}and sha(Path(source['path']))==source['sha256']and json.loads(Path(source['path']).read_bytes())['passed']is True"),
 (b" return dict(gates=gates,field_translations=translations),",
  b" return dict(gates=gates,field_translations=translations,field_sources={k:v['sources']for k,v in gate_review['measured_gate_fields'].items()if v.get('sources')}),"),
]
CRLF=b'\r'+NL
if CRLF in b:DELTAS=[(x.replace(NL,CRLF),y.replace(NL,CRLF))for x,y in DELTAS]
s=b
for a,c in DELTAS:assert s.count(a)==1,(a[:80],s.count(a));s=s.replace(a,c)
inv=s
for a,c in reversed(DELTAS):assert inv.count(c)==1,c[:60];inv=inv.replace(c,a)
assert inv==b,'Exact inverse to prepare_postterminal_templates_v1'
assert not dst.exists();dst.write_bytes(s);ast.parse(s.decode());print('wrote',dst)
