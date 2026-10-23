"""Materialize unchanged accepted131 narrow predicates; never invoke their main."""
from pathlib import Path
import ast, hashlib, json, runpy, sys, textwrap
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def cut(s,a,b):
 assert s.count(a)==1 and s.count(b)==1
 return textwrap.dedent(s[s.index(a):s.index(b)])
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists()
 parent=R/'tools/m4-tree-review/review_joint131_prelaunch_v2.py'
 # The wrapper only defines the frozen main when __name__ is not __main__.
 ns=runpy.run_path(str(parent),run_name='schema_definition_only');s=ns['text'];ast.parse(s)
 blocks={
 'native-inputs.py':cut(s,"  retained=read(","  main=pin("),
 'native-linked.py':cut(s,"   component_object=pin(","   db=pin(bf/'.ninja_deps')"),
 'native-TLS.py':cut(s,"  TLS_names={","  assert 'const Inputs input;'"),
 'native-boundary.py':cut(s,"  boundary=pin(","  lift=read("),
 }
 edits={
 'native-linked.py':[("CMakeFiles/mw34_joint_startup131.dir","CMakeFiles/mw34_joint_startup138.dir")],
 'native-TLS.py':[("?emitter@?A0xBCC7028@m4_mfc1168_connected@mw34@@3UEmitter@?A0xBCC7028@12@A","?emitter@?A0xD25E2230@m4_mfc1168_connected@mw34@@3UEmitter@?A0xD25E2230@12@A")],
 'native-inputs.py':[], 'native-boundary.py':[]}
 out.mkdir(parents=True);pins={str(parent):sha(parent)};relations=[]
 q=out/'accepted131-materialized.py';q.write_text(s);pins[str(q)]=sha(q)
 for n,t in blocks.items():
  old=t
  for a,b in edits[n]:assert a in t;t=t.replace(a,b)
  inverse=t
  for a,b in reversed(edits[n]):inverse=inverse.replace(b,a)
  assert inverse==old;ast.parse(t)
  q=out/n;q.write_text(t);pins[str(q)]=sha(q)
  relations.append(dict(file=n,parent_materialized_sha256=sha(out/'accepted131-materialized.py'),whole_extracted_predicate_inverse=True,changes=[dict(before=a,after=b)for a,b in edits[n]]))
 baseline=json.loads((R/'reports/m4-joint-startup131-root/configuration-r1/configuration.json').read_bytes())
 for gate in('native_prelaunch','original_prelaunch','original_preparation','source_preparation'):
  b=baseline['gates'][gate];p=R/b['path'];assert sha(p)==b['sha256'];pins[str(p)]=b['sha256']
  j=json.loads(p.read_bytes())
  for p,h in j['files'].items():
   if Path(p).suffix=='.py' and Path(p).is_relative_to(R):assert sha(p)==h;pins[p]=h
 checker=R/'tools/m4-138-criteria-frontier/check_schema138_v1.py';pins[str(checker)]=sha(checker)
 inputs={
 'native_prelaunch':('reports/m4-tree-review/joint138-prelaunch-r10/report.json','cede59b7c9b77ab98b78da72374938775b3c78ec3e9a737f618bd688873e3325'),
 'native_preparation':('reports/m4-joint-startup138/preparation-r4/report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a'),
 'native_build':('reports/m4-joint-startup138/build-r5/build.json','7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47'),
 'original_prelaunch':('reports/m4-138-validation-review/original138-observer-prelaunch-r1/report.json','eeab0505853554e353c389a6cae857f6b2c5696c0c2044e406880234b9f37e0c'),
 'original_preparation':('reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161'),
 'original_build':('reports/m4-startup138-original/build-r5/build.json','da5e20d9dfbfbaf70e8ad59b94dce328c22eb5330507ebb22cb38c6ef6508676'),
 'source_closure':('reports/m4-tree-review/source138-closure-r1/report.json','fc2453e5a9ff713d122f73e3a165edbdcc43da1b31c18f8bae787e6d6b43b38b')}
 for p,h in inputs.values():assert sha(R/p)==h;pins[str(R/p)]=h
 p=out/'inputs.json';p.write_text(json.dumps(inputs,indent=2)+'\n');pins[str(p)]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__)
 report=dict(passed=True,scope='Code-only exact accepted131 extraction and finite current object-path/anonymous-emitter identity derivative; no current physical checker execution',whole_extracted_baseline_predicates_preserved=True,relations=relations,source_or_resource_main_invoked=False,worker_launched=False,archive_reader_opened=False,authoritative_allowance=False,configuration_created=False,acceptance_executed=False,initializer_credit=0,files=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(p),sha256=sha(p))))
if __name__=='__main__':main(sys.argv[1])
