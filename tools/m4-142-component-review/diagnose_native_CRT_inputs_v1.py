"""UNEXECUTED bounded serialized ordinary-export diagnostic; never archives."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(output):
 out=Path(output).resolve();assert not out.exists();out.mkdir(parents=True);pins={};active=None;closed=[];results=[];passed=False
 def pin(path,h=None):
  p=Path(path).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 try:
  recipe_path=pin(R/'reports/m4-142-component-review/prefix-recipe-r2/recipe.json');recipe=json.loads(recipe_path.read_text())
  rp=pin(R/'tools/m4-startup131-original/export_reader.py');s=importlib.util.spec_from_file_location('hypot_input_transport',rp);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  for declaration in recipe['exports']:
   branch=declaration['branch'];active=m.ExportReader(declaration['report_path'],declaration['report_sha256'],branch,pin)
   branch_result=dict(branch=branch,source_report_path=declaration['report_path'],source_report_sha256=declaration['report_sha256'],cuts=[])
   try:
    for seq in range(6):
     pfx=f'phase/{seq}/'if branch=='original'else f'sequence-{seq}/'
     cut=dict(sequence=seq,observed_following_root=0x4b5af0,hypot_root_observed=False,missing_required_keys=[],genuine_cut_files=[],other_page_declarations=[])
     keys=[pfx+'81.bin',pfx+'82.bin']if branch=='original'else[pfx+'phase-81.bin',pfx+'phase-82.bin']
     for page in (0x7802f000,0x7803b000):
      keys.extend([f'phase/{seq}/82/CRT-before/{page}.bin',f'phase/{seq}/81/CRT-after/{page}.bin']if branch=='original'else[f'sequence-{seq}/phase-82-before-page-{page}.bin'])
      # Inventory only: other snapshots are not promoted to own cut inputs.
      found=[k for k in active.entries if k.startswith(pfx)and str(page)in k]
      assert len(found)<=2048,'Bounded page-name diagnostic inventory budget'
      cut['other_page_declarations'].append(dict(page=page,paths=found,used_as_cut_input=False))
     for key in keys:
      if key not in active.entries:cut['missing_required_keys'].append(key);continue
      data=active.data(key);q=out/branch/f'sequence-{seq}'/key.replace('/','__');q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);pin(q);cut['genuine_cut_files'].append(dict(logical_key=key,path=str(q),bytes=len(data),sha256=pins[str(q)]))
     cut['native_missing_page_values_seeded']=False;cut['State_constructed']=False;cut['projected_FX_promoted_to_runtime_State']=False;branch_result['cuts'].append(cut)
   finally:active.close();assert active.closed;closed.append(branch);active=None
   results.append(branch_result)
  pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if active is not None:active.close();closed.append('failed-current-reader');active=None
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Actual sealed ordinary key-presence and bounded raw-cut extraction only; no carried HYPOT State/model construction or source execution',serialized_reader_branches_closed=closed,ordinary_reader_closed=active is None,canonical_reader_opened=False,results=results,missing_key_not_unmapped_claim=True,other_page_inventory_not_input=True,accepted_credit=0,files=pins),indent=2)+'\n');print(str(q))
if __name__=='__main__':main(sys.argv[1])
