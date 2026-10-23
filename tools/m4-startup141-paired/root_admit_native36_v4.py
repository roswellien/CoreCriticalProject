"""ROOT exact bootstrap chronology correction; prior scopes remain unchanged."""
from pathlib import Path
import ast,copy,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-startup141-paired';p=base/'ROOT-native36-admission-r3/report.json'
 assert sha(p)=='083c82fe7096c3e8a746cdb9d9df60a2fa1c1191ce8fcb158b0707bb3d3492a8'
 A=json.loads(p.read_bytes());pins=dict(A['files']);pins[str(p)]=sha(p)
 folder=base/'native-owner-bootstrap-order-preparation-r1';q=folder/'report.json'
 assert sha(q)=='557b43fab21f15cd096585c022d5553d1e6b9dd0f6a96e53f0e2f87f3b3bc78b'
 F=json.loads(q.read_bytes());assert F['prepared_only'] and not F['source_execution'] and not F['reader_opened']
 pins[str(q)]=sha(q)
 for path,h in F['files'].items():assert pins.setdefault(path,h)==h
 for path,h in pins.items():assert sha(path)==h
 tools=R/'tools/m4-startup141-paired'
 for parent,child,delta in [('native_owner_metadata_v5.py','native_owner_metadata_v6.py','metadata5-to6-inverse.json'),('native_owner_metadata_controls_v2.py','native_owner_metadata_controls_v3.py','controls2-to3-inverse.json'),('constructor_native36_source141_v7.py','constructor_native36_source141_v8.py','source7-to8-inverse.json')]:
  a=(tools/parent).read_text();b=(tools/child).read_text().splitlines(True);changes=json.loads((folder/delta).read_bytes())
  for d in changes:assert ''.join(b[d['child_start']:d['child_stop']])==d['child']
  for d in reversed(changes):b[d['child_start']:d['child_stop']]=d['parent'].splitlines(True)
  assert ''.join(b)==a;ast.parse((tools/child).read_text())
 session=(R/'reports/m4-startup141-runway/service-preparation-r2/session_impl.inc').read_text();start=session.index('void bootstrap()');end=session.index('void enter(',start);body=session[start:end]
 assert body.index('binding->start(*parent)')<body.index('binding->lockit_bootstrap()')<body.index('binding->external_source_call(0x78004482')
 assert 'live_critical_sections()==4' in body
 ns={};exec(compile((tools/'native_owner_metadata_v6.py').read_text(),'ROOT pure causal bootstrap metadata','exec'),ns)
 cs={};exec(compile((tools/'native_owner_metadata_controls_v3.py').read_text(),'ROOT pure ordered bootstrap controls','exec'),cs)
 result=cs['controls'](ns['derive']);assert result['passed'] and result['negative_controls']==40 and len(set(result['refused']))==40
 controls=base/'root-owner-metadata-controls-r2';assert not controls.exists();controls.mkdir();cq=controls/'report.json';cq.write_text(json.dumps(dict(**result,independent_ROOT_review=True,source_bootstrap_order_reviewed=True,causal_order='counter0, CS1..4, Lockit5, registry6',accepted_function_credit=0,files={str(tools/f):sha(tools/f) for f in ('native_owner_metadata_v6.py','native_owner_metadata_controls_v3.py')}),indent=2)+'\n');pins[str(cq)]=sha(cq);pins[str(Path(__file__).resolve())]=sha(__file__)
 for path,h in pins.items():assert sha(path)==h
 out=base/'ROOT-native36-admission-r4';assert not out.exists();out.mkdir();A.update(source_bootstrap_order_reviewed=True,Lockit_first_generation_assumption_rejected=True,causal_order='counter0, CS1..4, Lockit5, registry6',files=pins)
 target=out/'report.json';target.write_text(json.dumps(A,indent=2)+'\n');print(sha(target))
if __name__=='__main__':main()
