from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2];base=R/'tools/m4-138-validation-review/diagnose_transition_r3.py';text=base.read_text();changes=[]
def one(old,new,count=1):
 global text
 assert text.count(old)==count,(old,text.count(old));start=0
 for _ in range(count):
  pos=text.index(old,start);changes.append(dict(position=pos,old=old,new=new));text=text[:pos]+new+text[pos+len(old):];start=pos+len(new)
for old,new in(('mfc-transition-r3','mfc-transition-r4'),('preparation-r7','preparation-r8'),('original-execution-r1','original-execution-r2'),('build-r4','build-r5'),('m4-tree-review/original138-prelaunch-r5','m4-138-validation-review/original138-observer-prelaunch-r1')):one(old,new,text.count(old))
anchor="    obs=read('reports/m4-138-validation-review/original138-observer-prelaunch-r1/compiled-observers.json')"
extra="""
    assert pin(ROOT/'reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161')
    assert pin(ROOT/'reports/m4-startup138-original/original-execution-r2/report.json','5ca81f7a324e0cd2d712dbc9d80698bb4012d54ee4a26292bfb04fcb8899cf81')
    assert pin(ROOT/'reports/m4-138-validation-review/original138-observer-prelaunch-r1/report.json','eeab0505853554e353c389a6cae857f6b2c5696c0c2044e406880234b9f37e0c')
    assert prep['passed']and run['passed']and review['passed']and run['build_sha256']==review['build_sha256']=='da5e20d9dfbfbaf70e8ad59b94dce328c22eb5330507ebb22cb38c6ef6508676'and run['preflight_sha256']=='eeab0505853554e353c389a6cae857f6b2c5696c0c2044e406880234b9f37e0c'
"""
one(anchor,anchor+extra.rstrip());reverse=text
for d in reversed(changes):
 p=d['position'];assert reverse[p:p+len(d['new'])]==d['new'];reverse=reverse[:p]+d['old']+reverse[p+len(d['new']):]
assert reverse==base.read_text();ast.parse(text);target=base.with_name('diagnose_transition_r4.py');assert not target.exists();target.write_text(text)
out=R/'reports/m4-138-validation-review/current-transition-preparation-r1';assert not out.exists();out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=out/'report.json';q.write_text(json.dumps(dict(passed=True,exact_reverse_delta=True,changes=changes,archive_reader_opened=False,unchanged_13_span_and_whole_page_checks=True,files={str(p.resolve()):sha(p)for p in(base,target,Path(__file__))}),indent=2)+'\n');print(q,sha(q))
