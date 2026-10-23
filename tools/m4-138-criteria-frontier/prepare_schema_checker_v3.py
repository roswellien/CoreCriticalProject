"""Immutable owning-function attribution for otherwise identical O0 bridges."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r2'
assert sha(old/'report.json')=='f8f6a16f1cabe3309d8b78768b5948e4d5d83da2e920da1e67fdd12a58234f32'
out=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r3'
assert not out.exists();out.mkdir()
pr=json.loads((old/'report.json').read_bytes());pins={str(old/'report.json'):sha(old/'report.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
before="symbols_c,sections_c=C.parse(component_object.read_bytes());bridge_targets={}\n"
after=before+'''# A unique whole linked call bridge anchors its exact owning COFF function.
# At O0 identical-shaped read/write bridges exist in unrelated adapters.
# Require the original owning-symbol relocation, whole owner body, and exact
# initialized source-declared TLS cell; never accept an arbitrary candidate.
owner_symbol='?owner@m4_mfc1168_connected@mw34@@YA@PEAX@Z'
call_raw,call_relocs=C.function(symbols_c,sections_c,'mw34_mfc1168_call')
call_matches=linked_candidates(image,call_raw,call_relocs);assert len(call_matches)==1
owner_relocs=[r for r in call_relocs if r['symbol']['name']==owner_symbol]
owner_target=None
if level=='O0':
 assert len(owner_relocs)==1
 ca,cb=call_matches[0];r=owner_relocs[0];assert 4<=r['type']<=9
 owner_target=ca+r['offset']+4+(r['type']-4)+struct.unpack_from('<i',cb,r['offset'])[0]
 owner_raw,owner_rel=C.function(symbols_c,sections_c,owner_symbol)
 owner_matches=linked_candidates(image,owner_raw,owner_rel)
 assert len(owner_matches)==1 and owner_matches[0][0]==owner_target
 owner_tls=[r for r in owner_rel if r['type']==11]
 assert len(owner_tls)==1 and owner_tls[0]['symbol']['name']=='?current@Impl@Component@m4_mfc1168_connected@mw34@@2PEAU1234@EA'
 TLS_relations(image,owner_raw,owner_matches[0][1],owner_rel,sections_c)
 links.append(dict(level=level,symbol=owner_symbol,address=owner_target,whole_bytes=len(owner_raw),relocation_DWORDs=len(owner_rel),actual_typed_call_owner=True))
 counts['whole_physical_bridge_owner_joins']+=1
else:
 assert level=='O2' and not owner_relocs
'''
oldcase=""" if len(matches_c)!=1:
  direct=[r for r in relocs_c if r['symbol']['name']in bridge_targets];assert direct,symbol
  matches_c=[(a,b)for a,b in matches_c if all(a+r['offset']+4+(r['type']-4)+struct.unpack_from('<i',b,r['offset'])[0]==bridge_targets[r['symbol']['name']]for r in direct)]
"""
newcase=""" if len(matches_c)!=1:
  assert level=='O0' and owner_target is not None
  own=[r for r in relocs_c if r['symbol']['name']==owner_symbol]
  assert len(own)==1 and 4<=own[0]['type']<=9
  r=own[0]
  matches_c=[(a,b)for a,b in matches_c if a+r['offset']+4+(r['type']-4)+struct.unpack_from('<i',b,r['offset'])[0]==owner_target]
  counts['otherwise_identical_bridge_owner_attributions']+=1
"""
relations=[]
for n in ['accepted131-materialized.py','native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py','native-linked.py','inputs.json']:
 p=old/n;assert sha(p)==pr['files'][str(p)];s=p.read_text();pins[str(p)]=sha(p)
 if n=='native-linked.py':
  assert s.count(before)==1 and s.count(oldcase)==1
  s=s.replace(before,after).replace(oldcase,newcase)
  assert s.replace(after,before).replace(newcase,oldcase)==p.read_text()
 (out/n).write_text(s)
 relations.append(dict(file=n,parent_sha256=sha(p),whole_equal=n!='native-linked.py',exact_inverse=n=='native-linked.py'))
for p in out.iterdir():pins[str(p)]=sha(p)
checker=R/'tools/m4-138-criteria-frontier/check_schema138_v3.py';pins[str(checker)]=sha(checker)
report=dict(passed=True,scope='Code-only exact owning-function/TLS attribution derivative; no actual checker or worker run',whole_extracted_baseline_predicates_preserved=True,relations=relations,linked_delta=dict(before=before,after=after,old_case=oldcase,new_case=newcase),files=pins)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(sha(out/'report.json'))
