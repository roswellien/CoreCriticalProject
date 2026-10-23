"""ROOT review of exact recorded Lockit lifecycle row; inherited scopes unchanged."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-startup141-paired';p=base/'ROOT-native36-admission-r4/report.json'
 assert sha(p)=='ab109111a75ddf19aec4256455e0ec31a4016722999ec21ff93357671f53d9f2'
 A=json.loads(p.read_bytes());pins=dict(A['files']);pins[str(p)]=sha(p)
 folder=base/'native-owner-lifecycle-preparation-r1';q=folder/'report.json'
 assert sha(q)=='b175b6736b3e5ceb7c532ccd31baf523a3ee4f10efc636a307bae6cae667fd4c'
 F=json.loads(q.read_bytes());assert F['prepared_only'] and not F['source_execution'] and not F['reader_opened']
 pins[str(q)]=sha(q)
 for path,h in F['files'].items():assert pins.setdefault(path,h)==h
 for path,h in pins.items():assert sha(path)==h
 td=R/'tools/m4-startup141-paired'
 for parent,child,delta in [('native_owner_metadata_v6.py','native_owner_metadata_v7.py','helper6-to7-inverse.json'),('native_owner_metadata_controls_v3.py','native_owner_metadata_controls_v4.py','controls3-to4-inverse.json'),('constructor_native36_source141_v8.py','constructor_native36_source141_v9.py','source8-to9-inverse.json')]:
  a=(td/parent).read_text();b=(td/child).read_text().splitlines(True);changes=json.loads((folder/delta).read_bytes())
  for d in changes:assert ''.join(b[d['child_start']:d['child_stop']])==d['child']
  for d in reversed(changes):b[d['child_start']:d['child_stop']]=d['parent'].splitlines(True)
  assert ''.join(b)==a;ast.parse((td/child).read_text())
 ns={};exec(compile((td/'native_owner_metadata_v7.py').read_text(),'ROOT pure exact lifecycle metadata','exec'),ns)
 cs={};exec(compile((td/'native_owner_metadata_controls_v4.py').read_text(),'ROOT pure lifecycle controls','exec'),cs)
 result=cs['controls'](ns['derive']);assert result['passed'] and result['negative_controls']==51 and len(set(result['refused']))==51
 out=base/'root-owner-metadata-controls-r3';assert not out.exists();out.mkdir();cq=out/'report.json'
 cq.write_text(json.dumps(dict(**result,independent_ROOT_review=True,actual_recorded_lifecycle_API4_reviewed=True,accepted_function_credit=0,files={str(td/f):sha(td/f) for f in ('native_owner_metadata_v7.py','native_owner_metadata_controls_v4.py')}),indent=2)+'\n')
 pins[str(cq)]=sha(cq);pins[str(Path(__file__).resolve())]=sha(__file__)
 for path,h in pins.items():assert sha(path)==h
 out=base/'ROOT-native36-admission-r5';assert not out.exists();out.mkdir()
 A.update(actual_recorded_lifecycle_API4_reviewed=True,lifecycle_has_no_source_CALL_or_CPU_claim=True,files=pins)
 target=out/'report.json';target.write_text(json.dumps(A,indent=2)+'\n');print(sha(target))
if __name__=='__main__':main()
