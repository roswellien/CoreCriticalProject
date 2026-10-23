"""Two immutable formatter module/domain bindings; no pair invocation or admission."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 pp=pin(R/'reports/m4-startup138-paired/comparer-preparation-r11/report.json','69888fc3aecb975215744406b7147da737f1593a6be19678dba606257351f6eb');parent=json.loads(pp.read_bytes());assert parent['passed']and parent['hunks']==51
 for p,h in parent['files'].items():pin(p,h)
 text=pin(parent['comparer'],parent['comparer_sha256']).read_text();before=text;hunks=json.loads(pin(pp.parent/'hunks.json',parent['files'][str((pp.parent/'hunks.json').resolve())]).read_bytes());extra=[]
 for old,new,label in[("ROOT/'tools/m4-startup131-paired/format_relations.py'","ROOT/'tools/m4-startup138-paired/format_relations_v4.py'",'Physical Game module and typed separately proven registrar helper'),('FMT.compare(source_original,source_native,native,stem,PAGES,mixed_contract)','FMT.compare(source_original,source_native,native,stem,PAGES,mixed_contract,dict(crt_domain[\'registry_fields\'][phase],callback=roots[entry]))','Exact own current source-derived CRT phase and physical callback relation')]:
  assert text.count(old)==1;position=text.index(old);text=text[:position]+new+text[position+len(old):];extra.append(dict(old=old,new=new,positions=[position],label=label))
 inverse=text
 for h in reversed(extra):
  p=h['positions'][0];assert inverse[p:p+len(h['new'])]==h['new'];inverse=inverse[:p]+h['old']+inverse[p+len(h['new']):]
 assert inverse==before;hunks.extend(extra);inverse=text
 for h in reversed(hunks):
  for p in h['positions']:
   assert inverse[p:p+len(h['new'])]==h['new'];inverse=inverse[:p]+h['old']+inverse[p+len(h['new']):]
 assert inverse==pin(R/'tools/m4-startup131-paired/paired_v2.py','61c3d15dea49cfc712cee70e04c2132470a20dd094abe79ada4f7971a736cd43').read_text();ast.parse(text)
 q=out/'paired138.py';q.write_text(text);pin(q);hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n');pin(hp);policy=pin(parent['policy_preparation'],parent['policy_preparation_sha256']);po=out/'policy-preparation.json';po.write_bytes(policy.read_bytes());pin(po)
 pin(R/'tools/m4-startup138-paired/format_relations_v4.py','c1f7c77d823fc4926f2e25f45fa8610f48b08751f1cef91d29fadea1440c90a8');pin(R/'reports/m4-startup138-paired/format-module-preflight-r2/report.json','6499700d4d77dc7e6e0b15df5d948d7693230db9ba10fc492d156176abd1fbfc');pin(__file__)
 report=dict(passed=True,scope='Two formatter classification/current-CRT source-domain bindings over51 retained hunks; independent classification admission required',parent_preparation_sha256=sha(pp),comparer=str(q.resolve()),comparer_sha256=sha(q),policy_preparation=str(po.resolve()),policy_preparation_sha256=sha(po),hunks=53,first51_hunks_retained=True,exact_two_delta_restores_preparation11=True,exact_inverse_restores_parent=True,policy_bytes_identical=True,full_pair_invocation_ready=False,all_current_domain_admissions=False,archive_reader_opened=False,raw_export_reader_opened=False,source_machine_executed=False,initializer_credit=0,files=pins)
 rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report_sha256=sha(rp),comparer_sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
