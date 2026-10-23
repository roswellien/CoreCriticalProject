"""Exact inverse and current cached-input inventory readiness, no worker run."""
from pathlib import Path
import hashlib,json,sys,ast
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=R/'reports/m4-138-preresource-controls/readiness-r1';assert not out.exists();pins={}
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
pp=pin(R/'reports/m4-138-preresource-controls/preparation-r1/report.json','153435fdcb184b64fe9a2b39e30bcb50b4e773dc02f0cd64f2efcfc239b91bbb');pr=json.loads(pp.read_bytes());assert pr['passed']
bp=pin(pp.parent.parent/'build-r2/build.json','ba6a26b3af64a351057380507397999bb42ceb34d87c33627f8acc80235c6b6b');b=json.loads(bp.read_bytes());assert b['passed'] and b['preparation_sha256']==sha(pp)
for d in (pr,b):
 for p,h in d['files'].items():pin(p,h)
current=(pp.parent/'native_main.cpp').read_text();parent=Path(pr['parent_preparation']).parent/'native_main.cpp'
for c in reversed(pr['parent_main_changes']):assert current.count(c['after'])==1;current=current.replace(c['after'],c['before'])
assert current==pin(parent).read_text()
code=(pp.parent/'controls_main.cpp').read_text();legacy=code[code.index('// Connected source-role/public-memory controls.'):]
for c in reversed(pr['legacy_controls_changes']):assert legacy.count(c['after'])==1;legacy=legacy.replace(c['after'],c['before'])
assert legacy==pin(R/'reports/m4-mfc1168-native/connected-controls-preparation-r6/connected_controls.inc').read_text()
for p in [Path(__file__).resolve(),R/'tools/m4-138-preresource-controls/run_v1.py',R/'tools/m4-138-preresource-controls/build_v1.py',R/'tools/m4-138-preresource-controls/build_v2.py',R/'tools/m4-138-criteria-frontier/prepare_preresource_v1.py']:pin(p);ast.parse(p.read_text())
for v in pr['source_images']:p=pin(v['path']);assert p.stat().st_size==v['bytes']
relations=[]
for level,w in b['workers'].items():
 rs=w['linked_input_relations'];assert sum(not r['reused_whole_bytes']for r in rs)==1 and [r for r in rs if not r['reused_whole_bytes']][0]['current']==str(Path(w['object']).resolve())
 for r in rs:
  pin(r['parent'],r['parent_sha256'])
  if r['reused_whole_bytes']:assert r['current']==r['parent']
 relations.append(dict(level=level,all_linked_inputs=len(rs),reused=len(rs)-1,only_new_object=w['object'],worker_sha256=w['sha256']))
out.mkdir();recipe='''ROOT must independently review source/full-link/current cleanup, produce an exact admission receipt pinning build2/preparation1/run_v1/current4images/workers and the8 named prelaunch checks. No currently admitted execution.
After admission ONLY, invoke one case:
C:/Python314/python.exe -B tools/m4-138-preresource-controls/run_v1.py execution-O0-mode1-r1 ABSOLUTE_ROOT_RECEIPT ITS_SHA O0 1
Repeat separately all O0/O2 modes1..12 after ROOT authorization. No current8 controls rerun or full138 schedule. Each worker bound120sec, <=4096files/128MiB. Strict independent actual refusal/root/frame/API-zero/no-resources/private-retry/own-cleanup checker still required before historical-schema gate credit. Native count remains unchanged.
''';(out/'ROOT-recipe.txt').write_text(recipe);pin(out/'ROOT-recipe.txt')
report=dict(passed=True,scope='Ordinary build/source readiness only; whole source inverses and complete cached link input identities, not independent linked-code review or actual controls',relations=relations,no_worker_run=True,no_reader_run=True,current12_refusals_proven=False,TLS64_runtime_proven=False,zero_API_resources_proven=False,independent_ROOT_prelaunch_required=pr['required_prelaunch'],initializer_credit=0,accepted_function_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(sha(q))
