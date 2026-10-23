"""Compose exact growth proof with pure whole-memory endpoint reconstruction."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'tools/m4-138-controls-review/review_source6_widgets_v3.py';original=p.read_text();text=original;changes=[]
def one(a,b):
 global text
 assert text.count(a)==1;text=text.replace(a,b);changes.append(dict(before=a,after=b))
one("  for x in rows:\n", "  growth_results={}\n  for x in rows:\n")
one("counts['physically_discriminated_growth_intervals']+=int(growth['growth'])", "counts['physically_discriminated_growth_intervals']+=int(growth['growth']);growth_results[case+(root,)]=growth")
helper=R/'tools/m4-138-controls-review/widget_byteflow.py'
addition="""  helper_path=pin(R/'tools/m4-138-controls-review/widget_byteflow.py',HELPER_SHA);spec=importlib.util.spec_from_file_location('independent_whole_widget_memory',helper_path);BF=importlib.util.module_from_spec(spec);spec.loader.exec_module(BF)
  paired_path=R/'reports/m4-joint-startup138-source/preparation-r11/paired_exports.py';spec=importlib.util.spec_from_file_location('independent_widget_raw_equality_exports',pin(paired_path,r['files'][str(paired_path.resolve())]));EX=importlib.util.module_from_spec(spec);spec.loader.exec_module(EX);byteflows=[]
  for level in('O0','O2'):
   facade=EX.Facade(next(v for v in r['paired_exports']if v['branch']==level),pin)
   try:
    for row in rows:
     if row['level']!=level:continue
     key=level,row['sequence'],row['root'];proof=BF.verify(row,facade.data,phase_map[key]['phase']);growth=growth_results[key]
     need(proof['delegated_registry_callback_store']['address']==growth['callback_slot'],'Separately owned callback publication exact typed capacity/reallocation-derived slot')
     proof.update(level=level,sequence=row['sequence'],root=row['root'],literal_registry_ownership_and_capacity=growth);byteflows.append(proof);counts.update(proof['counts']);counts['independent_widget_memory_byteflows']+=1
   finally:facade.close()
  need(len(byteflows)==84,'Every complete current widget memory byteflow')
  artifact=out/'independent-widget-memory-byteflows.json';artifact.write_text(json.dumps(byteflows,indent=2)+'\\n');pin(artifact)
  for q,h in list(PINS.items()):pin(q,h)
""".replace('HELPER_SHA',repr(sha(helper)))
one("  for q,h in list(PINS.items()):pin(q,h)\n",addition)
one("independent_full_literal_byteflow_replay=False", "independent_component_memory_byteflow=passed,independent_current_registry_slot_capacity_derivation=passed,independent_full_literal_byteflow_replay=False")
inverse=text
for c in reversed(changes):assert inverse.count(c['after'])==1;inverse=inverse.replace(c['after'],c['before'])
assert inverse==original;ast.parse(text);q=R/'tools/m4-138-controls-review/review_source6_widgets_v4.py';assert not q.exists();q.write_text(text)
out=R/'reports/m4-138-controls-review/source6-widget-complete-memory-preparation-r1';assert not out.exists();out.mkdir(parents=True)
paths=(p,q,helper,Path(__file__),R/'reports/m4-138-controls-review/source6-widget-growth-preparation-r1/report.json',R/'reports/m4-138-controls-review/source6-widget-byteflow-preflight-r1/report.json')
r=dict(passed=True,scope='Unexecuted exact composition of discriminated CRT growth/current owned callback slot and whole Game/provider/stack/TIB read/write byteflow from sealed source-computed BEFORE. Literal CPU/State instruction reexecution and repeated raw identity equality are not claimed; full acceptance remains separate.',changes=changes,inverse_restores_entire_parent=True,files={str(p.resolve()):sha(p)for p in paths},reviewer_executed=False,capture_archives_opened=0,full_source_widget_acceptance_closed=False,initializer_credit=0)
f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(f),tool_sha256=sha(q))))
