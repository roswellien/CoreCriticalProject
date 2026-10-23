"""Stage explicit component byteflow extension; independent admission pending."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'tools/m4-138-controls-review/review_source6_widgets.py';original=p.read_text();text=original;changes=[]
def one(a,b):
 global text
 assert text.count(a)==1;text=text.replace(a,b);changes.append(dict(before=a,after=b))
one("  for x in rows:\n", "  phase_rows=output('phases.json');phase_map={(x['level'],x['sequence'],x['entry']):x['phase']for x in phase_rows};need(len(phase_map)==1656,'Whole current selected phase map')\n  helper_path=pin(R/'tools/m4-138-controls-review/widget_byteflow.py');spec=importlib.util.spec_from_file_location('independent_widget_memory_byteflow',helper_path);BF=importlib.util.module_from_spec(spec);spec.loader.exec_module(BF)\n  paired_path=R/'reports/m4-joint-startup138-source/preparation-r11/paired_exports.py';spec=importlib.util.spec_from_file_location('independent_widget_ordinary_exports',pin(paired_path,r['files'][str(paired_path.resolve())]));EX=importlib.util.module_from_spec(spec);spec.loader.exec_module(EX)\n  byteflow=[]\n  for level in('O0','O2'):\n   facade=EX.Facade(next(v for v in r['paired_exports']if v['branch']==level),pin)\n   try:\n    for row in rows:\n     if row['level']!=level:continue\n     proof=BF.verify(row,facade.data,phase_map[level,row['sequence'],row['root']]);proof.update(level=level,sequence=row['sequence'],root=row['root']);byteflow.append(proof)\n     counts.update(proof['counts']);counts['independent_widget_memory_byteflows']+=1\n   finally:facade.close()\n  need(len(byteflow)==84,'All current component memory byteflows independently reviewed')\n  artifact=out/'independent-widget-byteflows.json';artifact.write_text(json.dumps(byteflow,indent=2)+'\\n');pin(artifact)\n  for x in rows:\n")
one("independent_full_literal_byteflow_replay=False", "independent_component_memory_byteflow=True,independent_full_literal_byteflow_replay=False,independent_CRT_backing_capacity_authority=False")
inverse=text
for c in reversed(changes):assert inverse.count(c['after'])==1;inverse=inverse.replace(c['after'],c['before'])
assert inverse==original;ast.parse(text)
q=R/'tools/m4-138-controls-review/review_source6_widgets_v2.py';assert not q.exists();q.write_text(text)
out=R/'reports/m4-138-controls-review/source6-widget-byteflow-preparation-r1';assert not out.exists();out.mkdir(parents=True)
paths=(p,q,Path(__file__),R/'tools/m4-138-controls-review/widget_byteflow.py',R/'reports/m4-138-controls-review/source6-widget-review-preparation-r1/report.json')
report=dict(passed=True,scope='Unexecuted84 full Game/provider/stack/TIB memory byteflow extension from producer-authenticated source BEFORE bytes. Separate exact callback writes delegated to CRT backing/capacity authority; CPU/State instruction semantics and raw identity equality not independently reexecuted. Strict failure on missing owned bytes/typed effects. No read/AFTER initializing memory.',changes=changes,inverse_restores_entire_parent=True,files={str(p.resolve()):sha(p)for p in paths},controller_executed=False,archive_reader_opened=False,full_source_widget_acceptance_closed=False,initializer_credit=0)
f=out/'report.json';f.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(f),tool_sha256=sha(q))))
