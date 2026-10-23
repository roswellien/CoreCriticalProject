"""Prepare inverse-reviewable accepted131 source reviews for sealed source6.

No reviewer invocation, capture access, machine replay, or acceptance credit.
"""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-138-controls-review/source6-review-preparation-r1';assert not out.exists();out.mkdir(parents=True)
 source=R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json'
 assert sha(source)=='40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052'
 sr=json.loads(source.read_bytes());prep=R/'reports/m4-joint-startup138-source/preparation-r11/report.json';ph=sha(prep)
 files={str(p.resolve()):sha(p)for p in(source,prep,Path(__file__))};derivatives=[]
 def derive(parent,name,mutate):
  p=R/parent;text=p.read_text();original=text;changes=[]
  def one(a,b):
   nonlocal text
   assert text.count(a)==1,(name,a,text.count(a));text=text.replace(a,b);changes.append(dict(before=a,after=b))
  mutate(one)
  inverse=text
  for c in reversed(changes):
   assert inverse.count(c['after'])==1,(name,c['after']);inverse=inverse.replace(c['after'],c['before'])
  assert inverse==original;ast.parse(text)
  q=R/'tools/m4-138-controls-review'/name;assert not q.exists();q.write_text(text)
  files[str(p.resolve())]=sha(p);files[str(q.resolve())]=sha(q)
  derivatives.append(dict(parent=str(p.resolve()),derivative=str(q.resolve()),changes=changes,inverse_restores_entire_parent=True))
 gate="\n  source6_preparation=read(R/'reports/m4-joint-startup138-source/preparation-r11/report.json','"+ph+"');need(source6_preparation['passed']and source6_preparation['archive_reader_opened']is False and source6_preparation['source_execution_performed']is False,'Exact current source6 prepared reader')\n  for q,h in source6_preparation['files'].items():pin(q,h)"
 def provider(one):
  one("'e250499a23537e21a206989f1dc9f1db2e40faae57840daa3b7cd4bb8d3a7a57'","'2203162c6c12c3f4c4b35009c39f2ddaaf52bea3abca9a8823d36237d7f0a4f6'")
  one("and sha(Path(j['native_library']).parent/'report.json')==lineage['inherited_native_preparation_sha256']", "and lineage['current_service_preparation_sha256']=='cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9' and sha(pin(lineage['current_service_preparation'],lineage['current_service_preparation_sha256']))==sha(Path(j['native_library']).parent/'report.json')")
  one("  boundary=[",gate+"\n  boundary=[")
  for a,b in [('tools/m4-joint-startup131/compare_provider_v6.py','reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py'),('tools/m4-formatting-source/final_observer130_v2.py','reports/m4-joint-startup138-source/preparation-r11/final_observer138_v2.py'),('tools/m4-formatting-source/final_observer130.py','reports/m4-joint-startup138-source/preparation-r11/final_observer138.py'),('tools/m4-joint-startup131/continuity131.py','reports/m4-joint-startup138-source/preparation-r11/continuity138.py')]:one(a,b)
  for a,b in [('persistent131_sequences=12','persistent138_sequences=12'),('persistent_phases=1572','persistent_phases=1656'),('whole_page_BEFORE=72312','whole_page_BEFORE=114264'),('whole_page_AFTER=72312','whole_page_AFTER=114264'),('literal_registration_roots=1212','literal_registration_roots=1296'),("==6996","==7164"),("selected_used_bytes']==404","selected_used_bytes']==432"),('capacity>=404','capacity>=432'),('(capacity-404)','(capacity-432)'),('total==28140','total==28788'),('selected_registration_closures=1212','selected_registration_closures=1296'),('reviewed_full_source_phases=1572','reviewed_full_source_phases=1656'),('reviewed_whole_source_page_endpoints=144624','reviewed_whole_source_page_endpoints=228528')]:one(a,b)
  one("  records=output(r,p,'API-identity-proofs.json');", "  need(r['counts']['literal_widget_roots']==84 and r['counts']['actual_GDI_source_calls']==1788 and r['counts']['actual_manual_owned_font_frees']==180 and r['counts']['complete_widget_caller_cleanup_restores']==12,'Exact additional current widget/GDI source scope; independent widget review remains separate')\n  records=output(r,p,'API-identity-proofs.json');")
 def closure(one):
  one("  for q,h in source['files'].items():\n   if Path(q).suffix.lower()in",gate+"\n  for q,h in source['files'].items():\n   if Path(q).suffix.lower()in")
  one("tools/m4-joint-startup131/compare_provider_v6.py","reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py")
  one("model=pin(model_receipt['model'],model_receipt['model_sha256'])", "inherited_model=pin(model_receipt['model'],model_receipt['model_sha256']);model=R/'reports/m4-fps-original/source-preparation-r4/game_model.py';pin(model,source['files'][str(model.resolve())])")
  one("len(program)==pre['physical_source_rows']==4637 and len(callbacks)==pre['source_callback_PC_count']==195", "pre['physical_source_rows']==4637 and pre['source_callback_PC_count']==195 and len(program)==5728 and len(callbacks)==255")
  one("  need(observations and counts[", "  need(source['counts']['persistent_phases']==1656 and source['counts']['whole_page_BEFORE']==source['counts']['whole_page_AFTER']==114264 and source['counts']['literal_widget_roots']==84,'Exact complete persistent138 source coverage')\n  need(observations and counts[")
 def mfc(one):
  one("sys.path.insert(0,str(R/'tools/m4-joint-startup131'))\nimport paired_exports as EX", "_paired_spec=importlib.util.spec_from_file_location('source6_mfc_paired_exports',R/'reports/m4-joint-startup138-source/preparation-r11/paired_exports.py')\nEX=importlib.util.module_from_spec(_paired_spec);_paired_spec.loader.exec_module(EX)")
 derive('tools/m4-tree-review/review_provider131_v2.py','review_source6_provider.py',provider)
 derive('tools/m4-tree-review/seal_source131_closure_v2.py','seal_source6_closure.py',closure)
 derive('tools/m4-tree-review/review_joint131_mfc_outputs_v2.py','review_source6_mfc.py',mfc)
 result=dict(passed=True,scope='Unexecuted exact accepted131 review derivatives. Source6 current lineage and exact coverage substitutions; inherited semantic/hardware/owner/resource/type predicates retained. Independent widget closure and paired policy remain separate gates.',source_provider_path=str(source.resolve()),source_provider_sha256=sha(source),derivatives=derivatives,files=files,reviewers_executed=False,capture_archives_opened=0,source_machine_executed=False,initializer_credit=0)
 p=out/'report.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p))))
if __name__=='__main__':main()
