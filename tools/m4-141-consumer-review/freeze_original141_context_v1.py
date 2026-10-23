"""Relocate historical mutable plan binding to its exact frozen bytes; no source edits."""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 old=R/'reports/m4-original141/geometry-preparation-r3';new=R/'reports/m4-original141/geometry-preparation-r4';source=R/'reports/m4-original141/source-preparation-r1';dest=R/'reports/m4-original141/source-preparation-r2';new.mkdir();dest.mkdir()
 report=json.loads((old/'report.json').read_bytes());live=R/'docs/m4-execution-plan-r14.md';historical=old/'frozen-plan.md';oldhash=report['files'][str(live)]
 assert sha(historical)==oldhash==report['current_plan_sha256']
 for p,h in report['files'].items():
  if p!=str(live):assert sha(Path(p))==h,p
 files={p:h for p,h in report['files'].items()if p!=str(live)}
 for p in old.iterdir():
  if p.is_file() and p.name!='report.json':shutil.copyfile(p,new/p.name);files[str(new/p.name)]=sha(new/p.name)
 shutil.copyfile(live,new/'current-context-plan.md');context_sha=sha(new/'current-context-plan.md');assert sha(live)==context_sha
 files[str(new/'current-context-plan.md')]=context_sha;files[str(old/'report.json')]=sha(old/'report.json');files[str(Path(__file__).resolve())]=sha(Path(__file__))
 relocation=dict(original_declared_path=str(live),original_declared_sha256=oldhash,historical_immutable_path=str(historical),historical_immutable_sha256=sha(historical),exact_historical_bytes=True,reason='Live plan is mutable review context, not compiler/source input. Preserve its original byte identity at already-frozen original location.',current_context_immutable_path=str(new/'current-context-plan.md'),current_context_sha256=context_sha,current_context_is_source_build_input=False)
 p=new/'plan-binding-relocation.json';p.write_text(json.dumps(relocation,indent=2)+'\n');files[str(p)]=sha(p)
 report.update(current_plan_sha256=context_sha,historical_plan_sha256=oldhash,plan_binding_relocation=relocation,physical_geometry_byteidentical_to_parent=True,files=files)
 (new/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 previous=json.loads((source/'report.json').read_bytes());files=dict(previous['files'])
 for p,h in files.items():assert sha(Path(p))==h,p
 files[str(source/'report.json')]=sha(source/'report.json');files[str(new/'report.json')]=sha(new/'report.json');files[str(new/'plan-binding-relocation.json')]=sha(new/'plan-binding-relocation.json')
 for p in source.iterdir():
  if p.is_file()and p.name not in('report.json','pins.json'):
   shutil.copyfile(p,dest/p.name);assert sha(dest/p.name)==sha(p);files[str(dest/p.name)]=sha(dest/p.name)
 previous.update(geometry_preparation=str(new/'report.json'),geometry_preparation_sha256=sha(new/'report.json'),plan_binding_relocation=relocation,whole_source_payload_byteidentical=True,source_parent_report=str(source/'report.json'),source_parent_sha256=sha(source/'report.json'),files=files)
 (dest/'report.json').write_text(json.dumps(previous,indent=2)+'\n');(dest/'pins.json').write_text(json.dumps(dict(files={**files,str(dest/'report.json'):sha(dest/'report.json')}),indent=2)+'\n')
 print(json.dumps(dict(geometry=str(new/'report.json'),geometry_sha256=sha(new/'report.json'),source=str(dest/'report.json'),source_sha256=sha(dest/'report.json'),context_sha256=context_sha)))
if __name__=='__main__':main()
