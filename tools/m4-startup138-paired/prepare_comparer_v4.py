"""Two exact current physical import binding deltas over frozen42hunk comparer."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 pp=pin(R/'reports/m4-startup138-paired/comparer-preparation-r3/report.json','53ba1a64c2a390fb5b2a8d8bfdb97624d6cfd1aff75465f3f65d005e5950b136');parent=json.loads(pp.read_bytes());assert parent['passed']and parent['hunks']==42
 for path,h in parent['files'].items():pin(path,h)
 text=pin(parent['comparer'],parent['comparer_sha256']).read_text();original=text;hunks=json.loads(pin(pp.parent/'hunks.json',parent['files'][str((pp.parent/'hunks.json').resolve())]).read_bytes());extra=[]
 def replace(old,new,label):
  nonlocal text
  assert text.count(old)==1;position=text.index(old);text=text[:position]+new+text[position+len(old):];extra.append(dict(old=old,new=new,positions=[position],label=label))
 old="CG=load('paired138_current_CRT_page_policy',ROOT/'tools/m4-startup138-paired/crt_page_policy_v2.py');crt_domains="
 new="CG=load('paired138_current_CRT_page_policy',ROOT/'tools/m4-startup138-paired/crt_page_policy_v3.py');crt_import_cells=json.loads(pin(policy['CRT_physical_import_cells_path'],policy['CRT_physical_import_cells_sha256']).read_bytes());need(len(crt_import_cells)==12 and {(r['level'],r['sequence'])for r in crt_import_cells}=={(l,s)for l in('O0','O2')for s in range(6)} and all(len(r['physical_import_cells'])==144 for r in crt_import_cells),'Exact physically attributed144import cells for all12 current case pairs');crt_domains="
 replace(old,new,'Physical helper plus complete sealed12table identity admission')
 replace("crt_domain['patches'],crt_domain['unused_input_offsets']);", "crt_domain['patches'],crt_domain['unused_input_offsets'],next(r['physical_import_cells']for r in crt_import_cells if r['level']==level and r['sequence']==seq));",'Required corresponding physically attributed own import table argument')
 restored=text
 for h in reversed(extra):
  for position in h['positions']:
   assert restored[position:position+len(h['new'])]==h['new'];restored=restored[:position]+h['old']+restored[position+len(h['new']):]
 assert restored==original
 hunks.extend(extra);inverse=text
 for h in reversed(hunks):
  for position in h['positions']:
   assert inverse[position:position+len(h['new'])]==h['new'];inverse=inverse[:position]+h['old']+inverse[position+len(h['new']):]
 accepted=pin(R/'tools/m4-startup131-paired/paired_v2.py','61c3d15dea49cfc712cee70e04c2132470a20dd094abe79ada4f7971a736cd43');assert inverse==accepted.read_text();ast.parse(text);target=out/'paired138.py';target.write_text(text);pin(target);hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n');pin(hp)
 policy=json.loads(pin(parent['policy_preparation'],parent['policy_preparation_sha256']).read_bytes());ip=pin(R/'reports/m4-startup138-paired/CRT-import-cell-policy-r3/report.json','07a81409de7d5aae90945079dd4ce295ead37fd6b3ea1cac4e723e95792e10aa');ig=json.loads(ip.read_bytes());assert ig['passed']and ig['ordinary_readers_closed']and ig['physical_named_cell_relations']==1728 and len(ig['negative_controls'])==36
 for path,h in ig['files'].items():pin(path,h)
 iv=pin(R/'reports/m4-startup138-paired/CRT-import-helper-inverse-r1/report.json','00459a1d5a888752145c1f10b2a14a90543f0fc0c75b74a98324c858b3b8911c');ivg=json.loads(iv.read_bytes());assert ivg['passed']and ivg['exact_reverse_to_parent']
 for path,h in ivg['files'].items():pin(path,h)
 cells=pin(ig['physical_import_cells_path'],ig['physical_import_cells_sha256']);tables=json.loads(cells.read_bytes());assert len(tables)==12 and {(r['level'],r['sequence'])for r in tables}=={(l,s)for l in('O0','O2')for s in range(6)}
 policy.update(schema='mw34-paired138-complete-finite-policy-pending-independent-review-v3',CRT_physical_import_cells_path=str(cells),CRT_physical_import_cells_sha256=sha(cells),CRT_physical_named_import_relation_count=1728,CRT_IAT_opaque_initial_difference_admission=False);policy['current_domain_receipts'].update({str(ip):sha(ip),str(iv):sha(iv)})
 for r in tables:assert len(r['physical_import_cells'])==144 and len({v['offset']for v in r['physical_import_cells']})==144 and sum(v['observer_shim']for v in r['physical_import_cells'])==8
 policyout=out/'policy-preparation.json';policyout.write_text(json.dumps(policy,indent=2)+'\n');pin(policyout);pin(__file__);pin(sys.executable)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Frozen42accepted131inverse hunks plus exactly2 current physical144import helper/table bindings; no pairing invocation or independent admission',parent_preparation_sha256=sha(pp),comparer=str(target),comparer_sha256=sha(target),policy_preparation=str(policyout),policy_preparation_sha256=sha(policyout),exact_inverse_restores_parent=True,exact_two_delta_restores_comparer3=True,all_parent_semantic_rules_retained=True,hunks=44,full_pair_invocation_ready=False,all_current_domain_admissions=False,archive_reader_opened=False,raw_export_reader_opened=False,source_machine_executed=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q),comparer_sha256=sha(target),hunks=44)))
if __name__=='__main__':main(sys.argv[1])
