"""ROOT finite structural relation admission after actual closed native36 PASS."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-startup141-paired';native=base/'native36-source-r8/report.json';original=R/'reports/m4-original141-source/source-r4-constructors/report.json'
 identities=[(native,'20c0105497eeab094c67e37cdd7f5db7ea94095e4ca0386a1f702a313ede8f96',36),(original,'8f910be42c5be26bf6e41260361b61b3ec258aefedf2cbdaabe35e3992498899',18)];pins={}
 for p,h,n in identities:
  assert sha(p)==h;D=json.loads(p.read_bytes());assert D['passed']is True and D['ordinary_reader_closed'] and D['source_AFTER_seed']is False and len(D['cases'])==n
  pins[str(p)]=h
  for path,identity in D['files'].items():assert pins.setdefault(path,identity)==identity
 for leaf,h in dict(constructor_structural54_pair_v1='4cf4fc32cd7450abd22e6be12e1130c614aef729d00f38de95e46c676ba0a282',constructor_relations141_v1='9300d8f5982c72a7f7c918a18fe867349d2ec0a02db92ed3761a64291ed6c018').items():
  p=R/'tools/m4-startup141-paired'/f'{leaf}.py';assert sha(p)==h;pins[str(p)]=h
 p=Path(__file__).resolve();pins[str(p)]=sha(p)
 for path,h in pins.items():assert sha(path)==h
 out=base/'ROOT-structural54-admission-r1';assert not out.exists();out.mkdir();q=out/'report.json'
 main_path=R/'tools/m4-startup141-paired/constructor_native36_source141_v13.py'
 q.write_text(json.dumps(dict(passed=True,independent_review=True,scope_identity='current141_constructor_structural54_pair',original18_sha256=identities[1][1],native36_sha256=identities[0][1],owner_export_sha256='d9b356af5dbec93b333c43bb11a335833ed4b74d6f118110b7f405d55c6a7e3f',native36_source_main_path=str(main_path),native36_source_main_sha256=sha(main_path),whole_original_State_claim=False,complete_constructor_acceptance_gate=False,accepted_function_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
