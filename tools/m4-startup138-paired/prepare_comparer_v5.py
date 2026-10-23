"""Two finite lock25 bindings over current physical44hunk comparer4."""
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
 pp=pin(R/'reports/m4-startup138-paired/comparer-preparation-r4/report.json','657bb80441dc79aeebae676ef1d7f622f36a9918115385ae275e29e48cccb051');parent=json.loads(pp.read_bytes());assert parent['passed']and parent['hunks']==44
 for path,h in parent['files'].items():pin(path,h)
 text=pin(parent['comparer'],parent['comparer_sha256']).read_text();original=text;hunks=json.loads(pin(pp.parent/'hunks.json',parent['files'][str((pp.parent/'hunks.json').resolve())]).read_bytes());extra=[]
 def replace(old,new,label):
  nonlocal text
  assert text.count(old)==1;position=text.index(old);text=text[:position]+new+text[position+len(old):];extra.append(dict(old=old,new=new,positions=[position],label=label))
 replace("ROOT/'tools/m4-startup138-paired/crt_page_policy_v3.py'","ROOT/'tools/m4-startup138-paired/crt_page_policy_v4.py'",'Explicit typed consumed lock25 cell helper')
 replace("r['sequence']==seq));need(len(crt_domain['registry_fields'])", "r['sequence']==seq),crt_domain['typed_CRT_loader_cells']);need(len(crt_domain['registry_fields'])",'Exact own retained initialized lock25 field table argument')
 reverse=text
 for h in reversed(extra):
  for position in h['positions']:
   assert reverse[position:position+len(h['new'])]==h['new'];reverse=reverse[:position]+h['old']+reverse[position+len(h['new']):]
 assert reverse==original;hunks.extend(extra);inverse=text
 for h in reversed(hunks):
  for position in h['positions']:
   assert inverse[position:position+len(h['new'])]==h['new'];inverse=inverse[:position]+h['old']+inverse[position+len(h['new']):]
 accepted=pin(R/'tools/m4-startup131-paired/paired_v2.py','61c3d15dea49cfc712cee70e04c2132470a20dd094abe79ada4f7971a736cd43');assert inverse==accepted.read_text();ast.parse(text);target=out/'paired138.py';target.write_text(text);pin(target);hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n');pin(hp)
 policy=json.loads(pin(parent['policy_preparation'],parent['policy_preparation_sha256']).read_bytes());lp=pin(R/'reports/m4-startup138-paired/CRT-lock25-domain-r1/report.json','974053dfbd2dc7b4808e1f09b14efcdc57a968e29c0a7539d2e99fb8cd61eae1');lg=json.loads(lp.read_bytes());assert lg['passed']and lg['typed_lock25_cell_relations']==12
 for path,h in lg['files'].items():pin(path,h)
 domains=pin(lg['domains_path'],lg['domains_sha256']);rows=json.loads(domains.read_bytes());assert len(rows)==12 and all(len(r['typed_CRT_loader_cells'])==1 and not set(range(0x8c,0x90))&set(r['unused_input_offsets'])for r in rows)
 ir=pin(R/'reports/m4-startup138-paired/CRT-import-independent-r1/report.json','3ae59486055ce3d0ad21ff48075248fe3544d4c2ef3dbbe7d82181874a0c36a3');ig=json.loads(ir.read_bytes());assert ig['passed']and ig['finite_144_import_cell_policy_reviewed']
 for path,h in ig['files'].items():pin(path,h)
 policy.update(schema='mw34-paired138-complete-finite-policy-pending-independent-review-v4',CRT_page_source_domains_path=str(domains),CRT_page_source_domains_sha256=sha(domains),CRT_lock25_is_unused=False);policy['current_domain_receipts'].update({str(lp):sha(lp),str(ir):sha(ir)});policyout=out/'policy-preparation.json';policyout.write_text(json.dumps(policy,indent=2)+'\n');pin(policyout);pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Frozen44hunk comparer4 plus exact2 typedlock25 helper/table bindings; four consumed bytes excluded fromunused; independent complete original caller-policy review pending',parent_preparation_sha256=sha(pp),comparer=str(target),comparer_sha256=sha(target),policy_preparation=str(policyout),policy_preparation_sha256=sha(policyout),exact_inverse_restores_parent=True,exact_two_delta_restores_comparer4=True,all_parent_semantic_rules_retained=True,hunks=46,full_pair_invocation_ready=False,all_current_domain_admissions=False,archive_reader_opened=False,raw_export_reader_opened=False,source_machine_executed=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q),comparer_sha256=sha(target),hunks=46)))
if __name__=='__main__':main(sys.argv[1])
