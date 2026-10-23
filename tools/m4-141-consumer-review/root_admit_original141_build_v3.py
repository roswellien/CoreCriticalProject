"""Admit compilation of exact original141 source; forbid execution credit."""
from pathlib import Path
import hashlib,json,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-original141/root-build-admission-r3';assert not out.exists();out.mkdir();pins={};passed=False;checks=[]
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v,(p,h,v);assert pins.setdefault(str(p),v)==v;return p
def receipt(rel,h):
 d=json.loads(pin(R/rel,h).read_bytes());assert d['passed']
 for p,h in d['files'].items():pin(p,h)
 return d
try:
 d=receipt('reports/m4-original141/source-preparation-r2/report.json','7c1acf0bb08043cf8a371a6b31d7fc3f4071771dae936a748abad66969c8cbd8')
 receipt('reports/m4-original141/geometry-preparation-r4/report.json','b4db7730b17d2ff8fbcb6013a5ff03489e48a449f62b526e36a6e608cdf20513')
 receipt('reports/m4-original141/geometry-controls-r2/report.json','7e1daf0ab03e597818d62099eb8c74482c17823688e36b374eadf260f295aa93')
 receipt('reports/m4-original141/patch-inventory-r1/report.json','fce4a4f45872ea36d21333b19861e3316c6ec31ca6818a6ccdd9f2ab2dc671cc')
 current=R/'reports/m4-original141/source-preparation-r2';old=R/'reports/m4-startup138-original/preparation-r8'
 for target,delta,count in [('reference.cpp','CPP-deltas.json',22),('reference_x86.asm','reference-ASM-deltas.json',2),('fs_observer_x86.asm','FS-ASM-deltas.json',2)]:
  text=pin(current/target).read_text();rows=json.loads(pin(current/delta).read_bytes());assert len(rows)==count
  for row in reversed(rows):assert text.count(row['new'])==1;text=text.replace(row['new'],row['old'],1)
  assert text==pin(old/target).read_text()
 checks.append('Entire original138 CPP and reference/FS ASM retained through exact22+2+2 inverse edits')
 assert pin(current/'CMakeLists.txt').read_text()==pin(old/'CMakeLists.txt').read_text().replace('api_boundaries.asm "','api_boundaries.asm constructor_observer_x86.asm "',1)
 for n in ('constructor_normal.hpp','constructor_observer_x86.asm','constructor-hook-bindings.json'):
  assert pin(current/n).read_bytes()==pin(R/'reports/m4-138-validation-review/constructor-input-capture-preparation-r5'/n).read_bytes()
 broker=json.loads(pin(current/'broker-delta.json').read_bytes());text=pin(current/'original_broker.hpp').read_text();assert text.count(broker['new'])==1;assert text.replace(broker['new'],broker['old'])==pin(old/'original_broker.hpp').read_text()
 for n in ('pages.bin','spec.hpp','protocol.hpp','selected-order.json','fs-hook-bindings.json'):assert pin(current/n).read_bytes()==pin(R/'reports/m4-original141/geometry-preparation-r4'/n).read_bytes()
 assert d['root_count']==141 and d['phases']==846 and d['callback_count']==111 and d['Record_bytes']==356992
 checks.append('Exact tested constructor input supplement,143 disjoint hook spans,111 physical callbacks and sparse-page reservations; no guard relaxation')
 # Compile only. Actual compiled whole observer/PUSHFD/source-stack and strict
 # CRT/IAT full-page validation are mandatory before any worker launch.
 script=pin(R/'tools/m4-startup138-original/build.ps1').read_text()
 script=script.replace("reports/m4-startup138-original","reports/m4-original141").replace('phases=828;roots=138','phases=846;roots=141')
 assert script.count('combined_pages=69;')==1
 script=script.replace('combined_pages=69;','combined_pages=69;constructor_global_extra_page_bytes=4096;')
 q=R/'tools/m4-141-consumer-review/build_original141.ps1';assert not q.exists();q.write_text(script);pin(q)
 pin(current/'pins.json');pin(__file__)
 for p,h in tuple(pins.items()):assert sha(p)==h
 passed=True
except Exception:(out/'failure.txt').write_text(traceback.format_exc())
(out/'report.json').write_text(json.dumps(dict(passed=passed,independent_review=True,checks=checks,compile_admitted=passed,worker_executed=False,worker_launch_admitted=False,compiled_provenance_review_required=True,CRT_IAT_whole_page_validator_required=True,original141_equivalence=False,initializer_credit=0,files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=passed,files=len(pins),report_sha256=sha(out/'report.json'))))
raise SystemExit(0 if passed else 1)
