"""Two whole lock13 object bindings over current46hunk comparer5."""
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
 pp=pin(R/'reports/m4-startup138-paired/comparer-preparation-r5/report.json','53529d80eec7a4055aa2a21222a60a1cea6ebfc31008fb81ed46271453888685');parent=json.loads(pp.read_bytes());assert parent['passed']and parent['hunks']==46
 for path,h in parent['files'].items():pin(path,h)
 text=pin(parent['comparer'],parent['comparer_sha256']).read_text();original=text;hunks=json.loads(pin(pp.parent/'hunks.json',parent['files'][str((pp.parent/'hunks.json').resolve())]).read_bytes());extra=[]
 def replace(old,new,label):
  nonlocal text
  assert text.count(old)==1;position=text.index(old);text=text[:position]+new+text[position+len(old):];extra.append(dict(old=old,new=new,positions=[position],label=label))
 replace("ROOT/'tools/m4-startup138-paired/crt_page_policy_v4.py'","ROOT/'tools/m4-startup138-paired/crt_page_policy_v5.py'",'Explicit whole24 consumed lock13 object helper')
 replace("crt_domain['typed_CRT_loader_cells']);need(len(crt_domain['registry_fields'])", "crt_domain['typed_CRT_loader_cells'],crt_domain['typed_CRT_lock13_objects']);need(len(crt_domain['registry_fields'])",'Exact own initialized lock13 complete24 resource table argument')
 reverse=text
 for h in reversed(extra):
  for position in h['positions']:
   assert reverse[position:position+len(h['new'])]==h['new'];reverse=reverse[:position]+h['old']+reverse[position+len(h['new']):]
 assert reverse==original;hunks.extend(extra);inverse=text
 for h in reversed(hunks):
  for position in h['positions']:
   assert inverse[position:position+len(h['new'])]==h['new'];inverse=inverse[:position]+h['old']+inverse[position+len(h['new']):]
 accepted=pin(R/'tools/m4-startup131-paired/paired_v2.py','61c3d15dea49cfc712cee70e04c2132470a20dd094abe79ada4f7971a736cd43');assert inverse==accepted.read_text();ast.parse(text);target=out/'paired138.py';target.write_text(text);pin(target);hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n');pin(hp)
 policy=json.loads(pin(parent['policy_preparation'],parent['policy_preparation_sha256']).read_bytes());lp=pin(R/'reports/m4-startup138-paired/CRT-lock13-helper-preflight-r2/report.json','3a34fb5c22458cd670903c89f9e4cb60af25a967aa2b5869f95a8f53845d196c');lg=json.loads(lp.read_bytes());assert lg['passed']and lg['exact_inverse_restores_helper4'] and lg['whole_source_expected_pages']==6624
 for path,h in lg['files'].items():pin(path,h)
 domains=pin(lg['domains_path'],lg['domains_sha256']);rows=json.loads(domains.read_bytes());assert len(rows)==12 and all(len(r['typed_CRT_loader_cells'])==len(r['typed_CRT_lock13_objects'])==1 and not(set(range(0x8c,0x90))|set(range(0x130,0x148)))&set(r['unused_input_offsets'])for r in rows)
 ir=pin(R/'reports/m4-startup138-paired/CRT-import-independent-r1/report.json','3ae59486055ce3d0ad21ff48075248fe3544d4c2ef3dbbe7d82181874a0c36a3');ig=json.loads(ir.read_bytes());assert ig['passed']and ig['finite_144_import_cell_policy_reviewed']
 for path,h in ig['files'].items():pin(path,h)
 policy.update(schema='mw34-paired138-complete-finite-policy-pending-independent-review-v5',CRT_page_source_domains_path=str(domains),CRT_page_source_domains_sha256=sha(domains),CRT_lock25_is_unused=False,CRT_lock13_whole24_is_unused=False);policy['current_domain_receipts'].update({str(lp):sha(lp),str(ir):sha(ir)});policyout=out/'policy-preparation.json';policyout.write_text(json.dumps(policy,indent=2)+'\n');pin(policyout);pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Frozen46hunk comparer5 plus exact2 whole24 lock13 helper/table bindings; consumed24 bytes explicitly typed and excluded fromunused; independent complete original caller-policy review pending',parent_preparation_sha256=sha(pp),comparer=str(target),comparer_sha256=sha(target),policy_preparation=str(policyout),policy_preparation_sha256=sha(policyout),exact_inverse_restores_parent=True,exact_two_delta_restores_comparer5=True,all_parent_semantic_rules_retained=True,hunks=48,full_pair_invocation_ready=False,all_current_domain_admissions=False,archive_reader_opened=False,raw_export_reader_opened=False,source_machine_executed=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q),comparer_sha256=sha(target),hunks=48)))
if __name__=='__main__':main(sys.argv[1])
