"""ROOT admission for finalize45_v3 (UNEXECUTED until an actual reviewer PASS).

Pins every file finalize45_v3 reads: itself, the template-produced candidate
manifest (schema mw34-terminal45-final-candidate-input-v1), proposal6, the parent
841-row table, mapping45 and all four actual composite gates (three terminal gates
plus the independent reviewer receipt). Requires the manifest's per-field reviews
to be byte-for-byte the ROOT field review's per_field_reviews, and that review to
bind the same gate SHAs. Creates no allowance, configuration or acceptance.
"""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PROPOSAL6='626c590fdde8e2077b4fa1fa2decdd76ef07f762466c0aad92a8fd81fe447505';PROPOSAL841='c9051a3c047efe3e029fc30a1d3706746eb0d4c6065a360cf3fe867d07274fb4';MAPPING45='79d6141deea3f2a7cc7faa58d2a1ada78a3122f3147d5fa90dbddb8b5ddce756'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(manifest_path,manifest_sha,field_review_path,field_review_sha,name):
 pins={}
 def pin(p,h):
  p=Path(p).resolve();v=sha(p);assert v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 def read(row):return json.loads(pin(row['path'],row['sha256']).read_bytes())
 M=read(dict(path=manifest_path,sha256=manifest_sha));assert M['schema']=='mw34-terminal45-final-candidate-input-v1'
 assert M['proposal6']['sha256']==PROPOSAL6 and M['proposal841']['sha256']==PROPOSAL841 and M['mapping45']['sha256']==MAPPING45
 parent=read(M['proposal6']);assert parent['passed']is True and parent['criteria']==841 and parent['files'][str(Path(M['proposal841']['path']).resolve())]==PROPOSAL841
 rows=read(M['proposal841']);mapping=read(M['mapping45']);assert len(rows)==841 and len(mapping)==45
 gates=M['actual_composite_gates'];assert set(gates)=={'controls_preparation','controls_prelaunch','controls','controls_review'}
 actual={k:read(v)for k,v in gates.items()};rv=actual['controls_review']
 assert rv['passed']is True and rv['controls_sha256']==gates['controls']['sha256']and rv['whole_composite_union_expanded']is True and rv['final_input_conservation']['metadata_only_cache_used']is False,'Actual independent reviewer PASS bound to the same controls gate'
 F=json.loads(pin(field_review_path,field_review_sha).read_bytes())
 assert F['passed']is True and F['independent_review']is True and F['fields_reviewed']==45 and len(F['changed_fields'])==6 and F['identity_fields']==39
 assert {k:dict(path=str(Path(v['path']).resolve()),sha256=v['sha256'])for k,v in F['actual_composite_gates'].items()}=={k:dict(path=str(Path(v['path']).resolve()),sha256=v['sha256'])for k,v in gates.items()},'Field review measured the same gates'
 assert json.dumps(M['independent_field_reviews'],sort_keys=True)==json.dumps(F['per_field_reviews'],sort_keys=True),'Manifest reviews are exactly the ROOT field review'
 finalizer=R/'tools/m4-controls-terminal-composite/finalize45_v3.py';pin(finalizer,sha(finalizer))
 for p,h in list(pins.items()):assert sha(p)==h
 pins[str(Path(__file__).resolve())]=sha(__file__)
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-controls-terminal-composite'/name;assert not out.exists();out.mkdir()
 value=dict(passed=True,terminal45_candidate_mapping_admitted=True,scope='Admits finalize45_v3 over the exact candidate manifest, ROOT field review and actual composite gates; no allowance/configuration/acceptance',field_review=dict(path=str(Path(field_review_path).resolve()),sha256=field_review_sha),allowance_created=False,configuration_created=False,acceptance_executed=False,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(admission=str(q),sha256=sha(q))))
if __name__=='__main__':main(*sys.argv[1:])
