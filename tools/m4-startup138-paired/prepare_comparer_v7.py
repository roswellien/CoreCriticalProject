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
 pp=pin(R/'reports/m4-startup138-paired/comparer-preparation-r6/report.json','e44982fcb1cdc7938c89ea0c65ce3aff66b9ceeb13d01931c0f87b8db638ecc6');parent=json.loads(pp.read_bytes());assert parent['passed']and parent['hunks']==48
 for p,h in parent['files'].items():pin(p,h)
 original=pin(parent['comparer'],parent['comparer_sha256']).read_text();lines=original.splitlines(keepends=True);old=lines[71];assert "execution=json.loads(pin(ROOT/'reports/m4-startup138-original/original-execution-r2/report.json'"in old and old.count("execution['files']")==1
 new=old.replace(';execution=json.loads(', ';original_execution=json.loads(').replace("execution['files']","original_execution['files']");position=sum(map(len,lines[:71]));text=original[:position]+new+original[position+len(old):];assert text[:position]+old+text[position+len(new):]==original
 hunks=json.loads(pin(pp.parent/'hunks.json',parent['files'][str((pp.parent/'hunks.json').resolve())]).read_bytes());hunks.append(dict(old=old,new=new,positions=[position],label='Keep original worker execution identity local; retain native execution levels'))
 inverse=text
 for h in reversed(hunks):
  for p in h['positions']:
   assert inverse[p:p+len(h['new'])]==h['new'];inverse=inverse[:p]+h['old']+inverse[p+len(h['new']):]
 assert inverse==pin(R/'tools/m4-startup131-paired/paired_v2.py','61c3d15dea49cfc712cee70e04c2132470a20dd094abe79ada4f7971a736cd43').read_text();ast.parse(text)
 target=out/'paired138.py';target.write_text(text);pin(target);hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n');pin(hp)
 policy=pin(parent['policy_preparation'],parent['policy_preparation_sha256']);po=out/'policy-preparation.json';po.write_bytes(policy.read_bytes());pin(po)
 failure=pin(R/'reports/m4-startup138-paired/paired-r1/failure.txt');assert "KeyError: 'levels'"in failure.read_text()
 pin(__file__);pin(sys.executable);report=dict(passed=True,scope='Exactly one line renames only original execution report variable and its worker file lookup',parent_preparation_sha256=sha(pp),comparer=str(target),comparer_sha256=sha(target),policy_preparation=str(po),policy_preparation_sha256=sha(po),exact_inverse_restores_parent=True,exact_one_delta_restores_comparer6=True,all_parent_semantic_rules_retained=True,hunks=49,first48_hunks_retained=True,policy_bytes_identical=True,full_pair_invocation_ready=False,all_current_domain_admissions=False,archive_reader_opened=False,raw_export_reader_opened=False,source_machine_executed=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report_sha256=sha(q),comparer_sha256=sha(target))))
if __name__=='__main__':main(sys.argv[1])
