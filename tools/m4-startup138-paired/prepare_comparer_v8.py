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
 pp=pin(R/'reports/m4-startup138-paired/comparer-preparation-r7/report.json','a005a4989556903f6f7e04308dca12f9a96fe3d8b4ed0e6c50c7a94c4fe76f6c');parent=json.loads(pp.read_bytes());assert parent['passed']and parent['hunks']==49
 for p,h in parent['files'].items():pin(p,h)
 original=pin(parent['comparer'],parent['comparer_sha256']).read_text();old="ROOT/'tools/m4-startup138-paired/widget_relations_v7.py'";new="ROOT/'tools/m4-startup138-paired/widget_relations_v8.py'";assert original.count(old)==1;position=original.index(old);text=original[:position]+new+original[position+len(old):];assert text[:position]+old+text[position+len(new):]==original
 hunks=json.loads(pin(pp.parent/'hunks.json',parent['files'][str((pp.parent/'hunks.json').resolve())]).read_bytes());hunks.append(dict(old=old,new=new,positions=[position],label='Bind exact source-terminal handle lastwriter helper8'))
 inverse=text
 for h in reversed(hunks):
  for p in h['positions']:
   assert inverse[p:p+len(h['new'])]==h['new'];inverse=inverse[:p]+h['old']+inverse[p+len(h['new']):]
 assert inverse==pin(R/'tools/m4-startup131-paired/paired_v2.py','61c3d15dea49cfc712cee70e04c2132470a20dd094abe79ada4f7971a736cd43').read_text();ast.parse(text)
 target=out/'paired138.py';target.write_text(text);pin(target);hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n');pin(hp)
 policy=pin(parent['policy_preparation'],parent['policy_preparation_sha256']);po=out/'policy-preparation.json';po.write_bytes(policy.read_bytes());pin(po)
 failure=pin(R/'reports/m4-startup138-paired/paired-r2/failure.txt');assert 'latest own source handle value'in failure.read_text();pin(R/'tools/m4-startup138-paired/widget_relations_v8.py','7f9a38687815fd5e74330a2fb04d2dce1d4d3933912cd20c00aa21b882f3caff');pin(R/'reports/m4-startup138-paired/widget-terminal-writer-preflight-r1/report.json','89eb78351636acf5e442681cf781dd82704ca59df4469aa13cc31683286246b7')
 pin(__file__);pin(sys.executable);report=dict(passed=True,scope='Exactly one import binds source terminal handle writer helper8; prior49 changes retained',parent_preparation_sha256=sha(pp),comparer=str(target),comparer_sha256=sha(target),policy_preparation=str(po),policy_preparation_sha256=sha(po),exact_inverse_restores_parent=True,exact_one_delta_restores_comparer7=True,all_parent_semantic_rules_retained=True,hunks=50,first49_hunks_retained=True,policy_bytes_identical=True,full_pair_invocation_ready=False,all_current_domain_admissions=False,archive_reader_opened=False,raw_export_reader_opened=False,source_machine_executed=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report_sha256=sha(q),comparer_sha256=sha(target))))
if __name__=='__main__':main(sys.argv[1])
