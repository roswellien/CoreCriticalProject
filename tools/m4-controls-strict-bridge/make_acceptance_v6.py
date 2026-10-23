"""Derive acceptance138_v6.py from acceptance138_v5.py by exact byte deltas.

v6 adds per-predicate sources: a configured gate may name, per current field, the
separately pinned ROOT report in which that value was measured (the proposal6 rows'
current_report_path). Such a predicate is read from that report, which must match its
SHA, report passed, be absorbed into the physical closure and be owned by the
independent review. Everything else (criteria, gates, expansion, union) is unchanged.
The script proves the exact inverse back to v5 before writing.
"""
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[2]
src=R/'tools/m4-controls-strict-bridge/acceptance138_v5.py';dst=R/'tools/m4-controls-strict-bridge/acceptance138_v6.py'
b=src.read_bytes()
NL=b'\n'
DELTAS=[
 (b'"""Current138 acceptance using retained131 criteria and full disk-backed union (v5: ordered-parallel whole-byte measurement; criteria/gates unchanged).',
  b'"""Current138 acceptance using retained131 criteria and full disk-backed union (v6: v5 plus per-predicate pinned ROOT measurement sources; criteria unchanged).'),
 (b"def typed_equal(actual,expected,label):need(type(actual)is type(expected)and actual==expected,'Exact typed '+label)"+NL,
  b"def typed_equal(actual,expected,label):need(type(actual)is type(expected)and actual==expected,'Exact typed '+label)"+NL+
  b"SOURCED={};REVIEW=None"+NL+
  b"def sourced(row,label,field):"+NL+
  b" # A predicate whose current value was measured in a separately pinned ROOT report."+NL+
  b" need(set(row)=={'path','sha256'},'Exact per-predicate source schema '+label+':'+field);path=(ROOT/row['path']).resolve();key=str(path)"+NL+
  b" if key not in SOURCED:"+NL+
  b"  report=read(path,row['sha256']);typed_equal(report.get('passed'),True,'Passed predicate source '+key);absorb(report)"+NL+
  b"  need(has(REVIEW,path,row['sha256']),'Independent review owns predicate source '+key);SOURCED[key]=report"+NL+
  b" return SOURCED[key]"+NL),
 (b" global PINS,SCOPES,GRAPH"+NL,b" global PINS,SCOPES,GRAPH,REVIEW"+NL),
 (b"  review=read(review_path,review_sha);absorb(review);",b"  review=read(review_path,review_sha);absorb(review);REVIEW=review;"),
 (b"need(set(gate)=={'path','sha256','equal'}and len(gate['equal'])>=2,'Exact complete measured gate schema '+label)",
  b"need(set(gate)=={'path','sha256','equal','sources'}and len(gate['equal'])>=2 and set(gate['sources'])<=set(gate['equal']),'Exact complete measured gate schema '+label)"),
 (b"for field,expected in gate['equal'].items():typed_equal(value_at(report,field),expected,label+':'+field);predicates+=1",
  b"for field,expected in gate['equal'].items():source=gate['sources'].get(field);typed_equal(value_at(report if source is None else sourced(source,label,field),field),expected,label+':'+field);predicates+=1"),
]
CRLF=b'\r'+NL
if CRLF in b:DELTAS=[(x.replace(NL,CRLF),y.replace(NL,CRLF))for x,y in DELTAS]
s=b
for a,c in DELTAS:assert s.count(a)==1,(a[:80],s.count(a));s=s.replace(a,c)
inv=s
for a,c in reversed(DELTAS):assert inv.count(c)==1,c[:60];inv=inv.replace(c,a)
assert inv==b,'Exact inverse to acceptance138_v5'
assert not dst.exists();dst.write_bytes(s);ast.parse(s.decode());print('wrote',dst)
