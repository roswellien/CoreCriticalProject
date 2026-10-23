"""Immutable local original execution variable repair; no readers or admission."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 pp=pin(R/'reports/m4-startup138-paired/comparer-preparation-r9/report.json','2ef8e701d9f2307991d07fa1024b5a741d083534798a7174b02ad81d96a88b50');parent=json.loads(pp.read_bytes());assert parent['passed']and parent['hunks']==50
 for p,h in parent['files'].items():pin(p,h)
 original=pin(parent['comparer'],parent['comparer_sha256']).read_text();old="ROOT/'tools/m4-startup131-paired/tree_relations.py'";new="ROOT/'tools/m4-startup138-paired/tree_relations_v2.py'";assert original.count(old)==1;position=original.index(old);text=original[:position]+new+original[position+len(old):];assert text[:position]+old+text[position+len(new):]==original
 hunks=json.loads(pin(pp.parent/'hunks.json',parent['files'][str((pp.parent/'hunks.json').resolve())]).read_bytes());hunks.append(dict(old=old,new=new,positions=[position],label='Bind tree activation at actual current physical phase83'))
 inverse=text
 for h in reversed(hunks):
  for p in h['positions']:
   assert inverse[p:p+len(h['new'])]==h['new'];inverse=inverse[:p]+h['old']+inverse[p+len(h['new']):]
 assert inverse==pin(R/'tools/m4-startup131-paired/paired_v2.py','61c3d15dea49cfc712cee70e04c2132470a20dd094abe79ada4f7971a736cd43').read_text();ast.parse(text)
 target=out/'paired138.py';target.write_text(text);pin(target);hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n');pin(hp)
 policy=pin(parent['policy_preparation'],parent['policy_preparation_sha256']);po=out/'policy-preparation.json';po.write_bytes(policy.read_bytes());pin(po)
 failure=pin(R/'reports/m4-startup138-paired/paired-r3/failure.txt');assert 'tree static byte carry 79/after'in failure.read_text();pin(R/'tools/m4-startup138-paired/tree_relations_v2.py','8e1bd4057e3c5f4a3ccaa7c9ca1287891f58a4b8c8ce9490d9cd4fedde6ec2f5');pin(R/'reports/m4-startup138-paired/tree-phase-preflight-r1/report.json','c118dfb427f9804120de9c732b2f285514c998c3dc51c33bd22e42ca751f408e')
 pin(__file__);pin(sys.executable);report=dict(passed=True,scope='Exactly one import binds current physical tree phase83; prior50 changes retained',parent_preparation_sha256=sha(pp),comparer=str(target),comparer_sha256=sha(target),policy_preparation=str(po),policy_preparation_sha256=sha(po),exact_inverse_restores_parent=True,exact_one_delta_restores_comparer9preparation=True,all_parent_semantic_rules_retained=True,hunks=51,first50_hunks_retained=True,policy_bytes_identical=True,full_pair_invocation_ready=False,all_current_domain_admissions=False,archive_reader_opened=False,raw_export_reader_opened=False,source_machine_executed=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report_sha256=sha(q),comparer_sha256=sha(target))))
if __name__=='__main__':main(sys.argv[1])
