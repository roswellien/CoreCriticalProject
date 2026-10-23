"""Immutable ordinary per-case strict derivative of accepted connected verifier."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-preresource-strict-review/preparation-r1';assert not out.exists();out.mkdir(parents=True)
 parent=R/'tools/m4-mfc1168-native/verify_connected_controls.py';s=parent.read_text();changes=[]
 def replace(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);changes.append(dict(before=a,after=b))
 replace("out=ROOT/'reports/m4-mfc1168-native'/name", "out=ROOT/'reports/m4-138-preresource-strict-review'/name")
 replace('def main(execution,digest,name):','def main(execution,digest,name,admission_path,admission_sha):')
 replace(" def pin(p,h=None):\n  p=Path(p).resolve();v=sha(p);", " admission_path=Path(admission_path).resolve();need(sha(admission_path)==admission_sha,'Exact independent ROOT admission');admission=json.loads(admission_path.read_bytes());need(admission['passed']is True and admission['scope_identity']=='current138_preresource_strict_outputs','Current independent strict review admission');admitted=admission['files'];pins[str(admission_path)]=admission_sha\n for q,h in admitted.items():\n  q=Path(q);need(q.suffix.lower()not in('.mwb','.mwi','.zip')and q.name!='transport.json'and sha(q)==h,'Entire ordinary closure before imports')\n def pin(p,h=None):\n  p=Path(p).resolve();v=sha(p);need(p.is_relative_to(out.resolve())or admitted.get(str(p))==v,'Every external ordinary dependency admitted before use');")
 old="  e=json.loads(pin(execution,digest).read_bytes());need(e['passed']and e['all_workers_terminal']and e['all_bounded_readers_closed'],'Actual current24 denials structural gate');b=json.loads(pin(e['build'],e['build_sha256']).read_bytes());p=json.loads(pin(b['preparation'],b['preparation_sha256']).read_bytes());need(p['control_cases']==12,'Exact current12 control input contract')"
 new="""  e=json.loads(pin(execution,digest).read_bytes());need(e['passed']and e['worker_executed']and e['worker_closed']and e['facts']['exit_code']==0,'Actual current single worker terminal production');level=e['level'];mode=e['mode'];need(level in('O0','O2')and mode in range(1,13),'Exact current case identity')
  b=json.loads(pin(ROOT/'reports/m4-138-preresource-controls/build-r4/build.json','9a65633f858e7c06c5ca09a8191a41051321cf2848c1a25b4318bd4c61c08a9f').read_bytes());pr=json.loads(pin(b['preparation'],b['preparation_sha256']).read_bytes());p=json.loads(pin(pr['parent_preparation'],pr['parent_preparation_sha256']).read_bytes());need(pr['cases']['prefix_completed']==13 and pr['cases']['failed_phase']==13,'Current bounded refusal chronology')
  for q,h in e['files'].items():pin(q,h)
  need(e['facts']['arguments'][0]==b['workers'][level]['path'],'Actual current compiler-level worker');need(e['facts']['arguments'][-1]==str(mode),'Actual invoked single mode');need(e['facts']['arguments'][-2]==admission['producer_admission_sha256'],'Actual independently admitted producer invocation')"""
 replace(old,new)
 replace("  DS=load(ROOT/'tools/m4-crt-allocation-root/run_v2.py','mfc_causal_control_direct');V=", "  DS=load(ROOT/'tools/m4-138-preresource-strict-review/ordinary_case.py','strict_current_ordinary_case');V=")
 replace("  for level in('O0','O2'):\n   row=next(r for r in e['levels']if r['level']==level);a=DS.DirectSet(row['capture'],pin);closed=False", "  for level in(e['level'],):\n   a=DS.DirectoryCase(e['facts']['arguments'][-3],pin);closed=False\n   for key in a.entries:a.data(key)\n   eq(a.data('admission.txt').decode(),admission['producer_admission_sha256'],'Exact producer admission payload')")
 replace('    for mode in range(1,13):','    for mode in(e[\'mode\'],):\n     counts.update(DS.strict_case(a,mode))')
 replace("3:'physical raw import preimage'", "3:'physical raw import preimage'") if False else None
 replace("1:'Flat32'", "1:'source segment/entry identity'")
 replace("11:'causal connected source'", "11:'Typed guest TLS index3/borrowed CS24 argument'")
 replace("12:'Flat32'", "12:'source segment/entry identity'")
 replace('a.entries.clear();a.bundles.clear();del a;', 'a.entries.clear();del a;')
 replace("eq(counts['actual_precise_denials'],24,'All24 actual precise current denials');eq(counts['actual_unchanged_poisoned_retries'],24,'All24 full captured retries');eq(counts['whole_caller_FX512_ENV28'],48,'Every denial/retry complete actual caller')", "eq(counts['actual_precise_denials'],1,'One actual current precise denial');eq(counts['actual_unchanged_poisoned_retries'],1,'One whole same Context retry');eq(counts['whole_caller_FX512_ENV28'],2,'Both whole denial/retry caller boundaries')")
 replace("scope='Current24 connected precise public denials,", "level=e['level'],mode=e['mode'],scope='Single current138 ordinary legacy denial, strict full current inventory and real64entry; accepted literal causal prefixes/resource identities retained; all24 aggregation separate. ")
 replace("if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])", "if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3],Path(sys.argv[4]).resolve(),sys.argv[5])")
 ast.parse(s);inverse=s
 for d in reversed(changes):assert inverse.count(d['after'])==1;inverse=inverse.replace(d['after'],d['before'])
 assert inverse==parent.read_text()
 tool=out/'verify_case_v1.py';tool.write_text(s);(out/'exact-deltas.json').write_text(json.dumps(changes,indent=2)+'\n')
 pins={str(q):sha(q)for q in(parent,Path(__file__),R/'tools/m4-138-preresource-strict-review/ordinary_case.py',tool,out/'exact-deltas.json',R/'tools/m4-tree-review/review_mfc131_controls.py',R/'reports/m4-138-preresource-controls/preparation-r3/report.json',R/'reports/m4-138-preresource-controls/preparation-r3/controls_main.cpp',R/'reports/m4-138-preresource-controls/preparation-r3/native_main.cpp',R/'reports/m4-138-preresource-controls/build-r4/build.json')}
 result=dict(passed=True,scope='Unexecuted strict ordinary per-case preparation; inherited source/API/lifetime proof retained, whole current retries and64frame additional. No runtime claims',exact_inverse_hunks=len(changes),whole_parent_inverse=True,required_case_set=[[l,m]for l in('O0','O2')for m in range(1,13)],source_API_completed_counts={str(m):1 if m in(7,8)else 0 for m in range(1,13)},native_resource_scope='Constructor may initialize owned native TLS/CS before literal source APIs. Cleaned own resource fields/lifetime must close; compilerTLS is separate.',runtime_checker_executed=False,worker_executed=False,capture_reader_opened=False,accepted_function_credit=0,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),hunks=len(changes))))
if __name__=='__main__':main()
