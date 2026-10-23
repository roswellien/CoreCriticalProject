"""Fresh common pair physical reviewers; preserve inherited source/object checks."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out=R/'reports/m4-version-source/common-prelaunch-review-preparation-r1';assert not out.exists();out.mkdir();changes_all={};files={}
for label,oldname,newname in(('original','review_version_original_prelaunch_v11.py','review_version_original_common_v12.py'),('native','review_version_prelaunch_v4.py','review_version_common_prelaunch_v5.py')):
 p=R/'tools/m4-tree-review'/oldname;scope={'__file__':str(p),'__name__':'materialize_only'};exec(compile(p.read_text(),str(p),'exec'),scope);text=scope['t'];parent=text;(out/(label+'-materialized-parent.py')).write_text(parent);changes=[]
 def one(old,new,count=1):
  global text
  assert text.count(old)==count,(label,old[:120],text.count(old));start=0
  for _ in range(count):
   pos=text.index(old,start);changes.append(dict(position=pos,old=old,new=new));text=text[:pos]+new+text[pos+len(old):];start=pos+len(new)
 if label=='original':
  for a,b in [('37e51c84827c8556d7c3ba96d4834bd809e0a85ae767ed4b30b100e178b5fad6','fafc198f6a20184cf3cc3bec67710e8f22eb7408789568eacefb73c90163d48f'),('cbe606c38282b970b3977305a030744f450923b928140d3f57b3502d7e36d4b7','14e3040ee8aa42f014a07d042bf3bab06d3565006b9ce5a2dfb39cf952893b52'),('original-preparation-r6','original-preparation-r8'),('original-build-r6','original-build-r8')]:one(a,b,text.count(a))
  one('  changed=[]',"  Common=module(R/'tools/m4-version-source/review_common_source_bridge.py','whole_common_source_bridge');common=Common.review(pin,read,counts)\n  changed=[]")
  one("for row in prep['source_relations']:","for row in common['original_parent']['source_relations']:")
  one("after=text(folder/'reference.cpp')", "after=common['original_parent_CPP']")
  one("v['name'].startswith('?version_')", "(v['name'].startswith('?version_')or '@m4_version_common@mw34@@'in v['name'])")
  one("controller=read(R/'reports/m4-version-source/original-controller-preparation-r3/report.json','d27b2f1b1391dbe56647d8c593ad1a83885ed887ec9f486e67ba727d3ed600bb')", "controller=read(R/'reports/m4-version-source/common-controllers-preparation-r1/report.json','03dc6dd94532209fb7885d29d65278dff34bb91d8835b1c29ca0543ecefac232')")
  one("pin(R/'tools/m4-version-source/run_original_v3.py','e6cafcbe42f728ba8e68913fd01f991061a3bb4335786fa7483c286b04e59e5d')", "pin(R/'tools/m4-version-source/run_original_common_v1.py','696bc67c1a611d896dad1b9d67380abb69d9f64eba9927926cfcaf1744757c75')")
  one('passed=passed,prelaunch_justified=passed',"passed=passed,prelaunch_justified=passed,common_caller_recipe_sha256='ca7f036b3693ef71bbbe5ce7a0af4ae3cb98755550d1bd1dcd8da955ab311281'")
 else:
  for a,b in [('ba1a85aea023afd7ef61608aa84656c10f431b44e0b097bf5e09778278aa18ee','d42a831e4d123021470ba99bc6589081f90dbf1f3e3bab5664c76356ab630bc6'),('d4959b4e37c2a8f38919545bcb3689d568f111bfe0495d639f5b029f3b20ee42','5cfc72f299317152c64b2d196dc1e6318e69fb89387a98603ba32d56d509372a'),('fixture-preparation-r3','fixture-preparation-r4'),('fixture-build-r2','fixture-build-r3')]:one(a,b,text.count(a))
  one("  api=pin(service/'session_impl.inc')", "  Common=load(R/'tools/m4-version-source/review_common_source_bridge.py','whole_common_source_bridge');common=Common.review(pin,read,counts)\n  api=pin(service/'session_impl.inc')")
  one("'?version_whole@','?borrow_version_'", "'?version_whole@','?version_common_caller@','?version_guest_environment@','?borrow_version_'")
  one("or '@m4_version_api@mw34@@'in n", "or '@m4_version_common@mw34@@'in n or '@m4_version_api@mw34@@'in n")
  one("pin(R/'tools/m4-version-source/run_fixture_v2.py')", "pin(R/'tools/m4-version-source/run_fixture_common_v1.py','5d48782342f3b429982aa5531a6d1367dd4b2f6674e487d895618f8f37bdaccc')")
  one("d=dict(passed=passed,scope=", "d=dict(passed=passed,common_caller_recipe_sha256='ca7f036b3693ef71bbbe5ce7a0af4ae3cb98755550d1bd1dcd8da955ab311281',scope=")
 reverse=text
 for d in reversed(changes):
  pos=d['position'];assert reverse[pos:pos+len(d['new'])]==d['new'];reverse=reverse[:pos]+d['old']+reverse[pos+len(d['new']):]
 assert reverse==parent;ast.parse(text);target=p.with_name(newname);assert not target.exists();target.write_text(text);changes_all[label]=changes
 for q in(p,target,out/(label+'-materialized-parent.py')):files[str(q.resolve())]=sha(q)
files[str(Path(__file__).resolve())]=sha(Path(__file__));bridge=R/'tools/m4-version-source/review_common_source_bridge.py';files[str(bridge)]=sha(bridge)
q=out/'report.json';q.write_text(json.dumps(dict(passed=True,exact_inverse_restores_both_materialized_parents=True,changes=changes_all,full_admission_unexecuted=True,archive_reader_opened=False,worker_launched=False,initializer_credit=0,files=files),indent=2)+'\n');print(q,sha(q))
