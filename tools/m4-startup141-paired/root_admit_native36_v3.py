"""ROOT causal allocation review extends unchanged source/projector admission."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,re,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-startup141-paired';final=base/'native-owner-metadata-final-preparation-r1'
 fp=final/'report.json';assert sha(fp)=='2821b813b7defa78700bf8de297d50d8fbdcd9e857b8b2a4bfe68daf2263f1cd'
 F=json.loads(fp.read_bytes());assert F['prepared_only'] and not F['source_execution'] and not F['reader_opened']
 pins={str(fp):sha(fp)}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;assert pins.setdefault(str(p),v)==v;return p
 for p,h in F['files'].items():pin(p,h)
 P=base/'native-owner-metadata-preparation-r2';prep=json.loads(pin(P/'report.json','7d4b5fc91440b40e07a7f36032c641a9e1d0695f97cfe749a167405266a89553').read_bytes())
 for p,h in prep['files'].items():pin(p,h)
 tools=R/'tools/m4-startup141-paired'
 def inverse(parent,child,delta):
  a=pin(parent).read_text();b=pin(child).read_text().splitlines(True);changes=json.loads(pin(delta).read_bytes())
  for d in changes:assert ''.join(b[d['child_start']:d['child_stop']])==d['child']
  for d in reversed(changes):b[d['child_start']:d['child_stop']]=d['parent'].splitlines(True)
  assert ''.join(b)==a;ast.parse(Path(child).read_text())
 for parent,child,delta in [('native_owner_metadata_v1.py','native_owner_metadata_v3.py','helper1-to3-inverse.json'),('native_owner_metadata_v3.py','native_owner_metadata_v5.py','helper3-to5-inverse.json'),('native_owner_metadata_controls_v1.py','native_owner_metadata_controls_v2.py','controls1-to2-inverse.json'),('constructor_native36_source141_v6.py','constructor_native36_source141_v7.py','source6-to7-inverse.json')]:inverse(tools/parent,tools/child,final/delta)
 inverse(tools/'constructor_native_input141_v3.py',tools/'constructor_native_input141_v4.py',P/'adapter4-inverse.json')
 inverse(tools/'constructor_native36_source141_v5.py',tools/'constructor_native36_source141_v6.py',P/'source6-inverse.json')
 provider=R/'reports/m4-startup141-runway/service-preparation-r2'
 physical=(provider/'source_contract.inc').read_text()+'\n'+(provider/'registry_contract.inc').read_text();contracts={}
 for match in re.finditer(r'\{(0x[0-9a-fA-F]+|\d+),(0x[0-9a-fA-F]+|\d+),(0x[0-9a-fA-F]+|\d+),(\d+),"([A-Za-z0-9_]+)",(\d+)\}',physical):
  pc,slot,raw,argc,name,tail=match.groups();pc=int(pc,0);row=[name,int(slot,0),int(raw,0),int(argc),int(tail)];assert pc not in contracts or contracts[pc]==row;contracts[pc]=row
 assert {int(k):v for k,v in json.loads((P/'physical-API-contracts.json').read_bytes()).items()}==contracts
 header=(provider/'locale_batch.hpp').read_text();operations=(provider/'locale_batch_operations.inc').read_text();lockit=(provider/'lockit_operations.inc').read_text();growth=(provider/'registry_api.inc').read_text()
 assert 'generation_' in header and 'token=0x48450001' in header.replace(' ','')
 assert 'section->generation' in lockit and 'object->generation=++generation_' in lockit
 assert 'object->generation=++generation_' in operations and 'a->generation=++generation_' in growth
 md=(tools/'native_owner_metadata_v5.py').read_text();ct=(tools/'native_owner_metadata_controls_v2.py').read_text()
 ns={};exec(compile(md,'ROOT reviewed pure causal metadata','exec'),ns);cs={};exec(compile(ct,'ROOT reviewed pure metadata controls','exec'),cs)
 result=cs['controls'](ns['derive']);assert result['passed'] and result['negative_controls']==40 and len(set(result['refused']))==40 and not result['source_execution'] and not result['reader_opened']
 co=base/'root-owner-metadata-controls-r1';assert not co.exists();co.mkdir();cq=co/'report.json';cq.write_text(json.dumps(dict(**result,independent_ROOT_review=True,complete_parent_inverses=True,complete_physical_API_contract_equality=True,accepted_function_credit=0,files=pins),indent=2)+'\n');pin(cq)
 parent=tools/'root_admit_native36_v2.py';pin(parent);spec=importlib.util.spec_from_file_location('ROOT_unchanged_native36_admission',parent);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.main(base/'native-owner-cuts-r3/report.json','d9b356af5dbec93b333c43bb11a335833ed4b74d6f118110b7f405d55c6a7e3f','ROOT-native36-admission-r3-base')
 previous=base/'ROOT-native36-admission-r3-base/report.json';A=json.loads(pin(previous).read_bytes());assert A['passed'] and A['scope_identity']=='native141_constructor36_own_source'
 for p,h in A['files'].items():pin(p,h)
 pin(__file__)
 for p,h in pins.items():assert sha(p)==h
 out=base/'ROOT-native36-admission-r3';assert not out.exists();out.mkdir();A.update(causal_owner_metadata_physically_reviewed=True,causal_metadata_pure_adverse_controls=40,final_allocation_summary_used=False,actual_current_cut_source_comparison_pending=True,complete_constructor_pair_gate=False,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(A,indent=2)+'\n');print('CAUSAL_ADMISSION_SHA='+sha(q))
if __name__=='__main__':main()
