"""Bind every current named original141 proof to immutable historical/current plan bytes."""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=R/'reports/m4-original141';geometry=base/'geometry-preparation-r4';controls=base/'geometry-controls-r2';oldpatch=base/'patch-inventory-r1';patch=base/'patch-inventory-r2';oldsource=base/'source-preparation-r2';source=base/'source-preparation-r3';patch.mkdir();source.mkdir()
 relocation=json.loads((geometry/'plan-binding-relocation.json').read_bytes());assert sha(Path(relocation['historical_immutable_path']))==relocation['original_declared_sha256'];assert sha(Path(relocation['current_context_immutable_path']))==relocation['current_context_sha256']
 for parent in(geometry,controls,oldpatch,oldsource):
  d=json.loads((parent/'report.json').read_bytes())
  for p,h in d['files'].items():assert sha(Path(p))==h,p
 d=json.loads((oldpatch/'report.json').read_bytes());files=dict(d['files'])
 for name in('source-hook-inventory141.json',):
  shutil.copyfile(oldpatch/name,patch/name);assert sha(patch/name)==sha(oldpatch/name);files[str(patch/name)]=sha(patch/name)
 for parent in(geometry,controls):
  q=parent/'report.json';files[str(q)]=sha(q)
 files[str(oldpatch/'report.json')]=sha(oldpatch/'report.json');files[str(Path(__file__).resolve())]=sha(Path(__file__))
 d.update(current_geometry_report=str(geometry/'report.json'),current_geometry_sha256=sha(geometry/'report.json'),current_controls_report=str(controls/'report.json'),current_controls_sha256=sha(controls/'report.json'),physical_hook_inventory_byteidentical=True,plan_binding_relocation=relocation,files=files)
 (patch/'report.json').write_text(json.dumps(d,indent=2)+'\n')
 d=json.loads((oldsource/'report.json').read_bytes());files=dict(d['files']);files[str(oldsource/'report.json')]=sha(oldsource/'report.json')
 for p in oldsource.iterdir():
  if p.is_file()and p.name not in('report.json','pins.json'):
   shutil.copyfile(p,source/p.name);assert sha(p)==sha(source/p.name);files[str(source/p.name)]=sha(source/p.name)
 # Absorb fresh proof dependencies fully; inherited historical report bytes
 # remain pinned, but no consumer opportunistically reads the mutable plan.
 for parent in(geometry,controls,patch):
  q=parent/'report.json';files[str(q)]=sha(q)
  for p,h in json.loads(q.read_bytes())['files'].items():assert files.setdefault(p,h)==h
 d.update(geometry_preparation=str(geometry/'report.json'),geometry_preparation_sha256=sha(geometry/'report.json'),geometry_controls=str(controls/'report.json'),geometry_controls_sha256=sha(controls/'report.json'),patch_inventory=str(patch/'report.json'),patch_inventory_sha256=sha(patch/'report.json'),whole_source_payload_byteidentical=True,source_parent_report=str(oldsource/'report.json'),source_parent_sha256=sha(oldsource/'report.json'),files=files)
 assert str(R/'docs/m4-execution-plan-r14.md')not in files
 (source/'report.json').write_text(json.dumps(d,indent=2)+'\n');(source/'pins.json').write_text(json.dumps(dict(files={**files,str(source/'report.json'):sha(source/'report.json')}),indent=2)+'\n')
 print(json.dumps(dict(source=str(source/'report.json'),source_sha256=sha(source/'report.json'),patch=str(patch/'report.json'),patch_sha256=sha(patch/'report.json'),files=len(files))))
if __name__=='__main__':main()
