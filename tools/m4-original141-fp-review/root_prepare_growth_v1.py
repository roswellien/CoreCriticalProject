"""ROOT reviewed input-derived growth delta; preparation, never source acceptance."""
from pathlib import Path
import ast,hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[2]
P=R/'reports/m4-original141-fp-review/source-preparation-r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert sha(P/'report.json')=='b2740d19fc7db50dc0c83dcaf390777504b4edfc640fc74cffa999d939e43e18'
 q=json.loads((P/'report.json').read_bytes())
 for p,h in q['files'].items():assert sha(Path(p))==h
 a=Path(q['parent']).read_text();b=Path(q['derived_checker']).read_text();inverse=b
 assert len(q['changes'])==7
 for d in reversed(q['changes']):
  assert inverse.count(d['after'])==1
  inverse=inverse.replace(d['after'],d['before'])
 assert inverse==a;ast.parse(b)
 pre=R/'tools/m4-original141-fp-review/preflight_growth_v1.py'
 assert sha(pre)=='0331d5e2ff790a88d2552a092b4051bc7a46656bda312f745d12ac1ae1d1f99c'
 out=R/'reports/m4-original141-fp-review/root-growth-preflight-r1'
 subprocess.run([sys.executable,'-B',str(pre),str(out)],check=True)
 tests=json.loads((out/'report.json').read_bytes())
 assert tests['passed'] and tests['synthetic_positive_controls']==3 and len(tests['rejected'])==18 and len(set(tests['rejected']))==18
 assert not tests['source_evaluated'] and not tests['archive_reader_opened'] and tests['acceptance_credit']==0
 actual=R/'tools/m4-original141-source/widget_source141_v5.py';assert not actual.exists();actual.write_bytes(Path(q['derived_checker']).read_bytes())
 parent=R/'tools/m4-original141-source/replay_original141_v9.py';child=parent.with_name('replay_original141_v10.py');assert not child.exists()
 c=parent.read_text();assert c.count("'widget_source141_v4.py'")==1
 derived=c.replace("'widget_source141_v4.py'","'widget_source141_v5.py'");assert derived.replace("'widget_source141_v5.py'","'widget_source141_v4.py'")==c
 ast.parse(derived);child.write_text(derived)
 gate=R/'tools/m4-original141-source/root_admit_replay_v8.py';gate9=gate.with_name('root_admit_replay_v9.py');assert not gate9.exists()
 block=""" growth=read(fp/'source-preparation-r2/report.json','b2740d19fc7db50dc0c83dcaf390777504b4edfc640fc74cffa999d939e43e18');assert growth['passed']and growth['whole_inverse_equal']and not growth['source_evaluated']and not growth['archive_reader_opened']and growth['acceptance_credit']==0
 for p,h in growth['files'].items():pin(p,h)
 original=pin(growth['parent'],growth['parent_sha256']).read_text();inverse=pin(growth['derived_checker']).read_text()
 assert len(growth['changes'])==7
 for delta in reversed(growth['changes']):assert inverse.count(delta['after'])==1;inverse=inverse.replace(delta['after'],delta['before'])
 assert inverse==original
 actual=pin(R/'tools/m4-original141-source/widget_source141_v5.py','245771a6c72ab54fa6e27943848ea7f727cefc130d61100245d2450d107fbaf9');assert actual.read_bytes()==pin(growth['derived_checker']).read_bytes();ast.parse(actual.read_text())
 tests=read(fp/'root-growth-preflight-r1/report.json','TEST_SHA');assert tests['passed']and tests['synthetic_positive_controls']==3 and len(tests['rejected'])==18 and len(set(tests['rejected']))==18 and not tests['source_evaluated']and not tests['archive_reader_opened']and tests['acceptance_credit']==0
 for p,h in tests['files'].items():pin(p,h)
 parent=pin(R/'tools/m4-original141-source/replay_original141_v9.py').read_text();child=pin(R/'tools/m4-original141-source/replay_original141_v10.py').read_text();assert child.count("'widget_source141_v5.py'")==1 and child.replace("'widget_source141_v5.py'","'widget_source141_v4.py'")==parent;ast.parse(child)
 checks.append(dict(whole_widget_growth_inverse_hunks=7,whole_controller_inverse_hunks=1,pure_growth_positive_controls=3,pure_growth_adverses=18,own_BEFORE_growth_predictions=42,all_actual_source_births_must_match_own_prediction=True,retained_heap_and_whole_endpoint_guards=True,accepted_function_credit=0))
""".replace('TEST_SHA',sha(out/'report.json'))
 g=gate.read_text();assert g.count(' pin(sys.executable)\n')==1
 d=g.replace(' pin(sys.executable)\n',block+' pin(sys.executable)\n');assert d.replace(block,'')==g;ast.parse(d);gate9.write_text(d)
 record=R/'reports/m4-original141-fp-review/root-growth-delta-review-r1';assert not record.exists();record.mkdir()
 files={str(p.resolve()):sha(p) for p in (P/'report.json',P/'registry_growth_v1.py',Path(q['derived_checker']),actual,parent,child,gate,gate9,pre,out/'report.json',Path(__file__))}
 (record/'report.json').write_text(json.dumps(dict(passed=True,independent_review=True,whole_widget_inverse_hunks=7,whole_controller_inverse_hunks=1,whole_admission_inverse_hunks=1,source_execution=False,archive_reader_opened=False,accepted_function_credit=0,files=files),indent=2)+'\n')
 print(json.dumps(dict(preflight_sha256=sha(out/'report.json'),review_sha256=sha(record/'report.json'))))
if __name__=='__main__':main()
