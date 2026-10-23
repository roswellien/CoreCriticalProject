"""Exact current guarded CALL/unwind ownership for duplicate whole ASM bodies."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r3'
assert sha(old/'report.json')=='f278ee71f41a498ea9047008f86afd7b28d1f00cf4332812ec54140248805464'
pr=json.loads((old/'report.json').read_bytes());out=old.parent/'schema-checker-preparation-r4';assert not out.exists();out.mkdir()
changes=[("bm=linked_candidates(image,br,brels);assert len(bm)==1;address,actual=bm[0];target=address+29+struct.unpack_from('<i',actual,25)[0];assert target==wm[0][0]", "bm=linked_candidates(image,br,brels)\n# Both actual whole85-byte ASM copies have valid unwind entries. Attribute\n# this one through its physical CALL to the unique current guarded wrapper.\nbm=[(a,b)for a,b in bm if a+29+struct.unpack_from('<i',b,25)[0]==wm[0][0]]\nassert len(bm)==1;address,actual=bm[0];target=address+29+struct.unpack_from('<i',actual,25)[0];assert target==wm[0][0]"),
(" TLS_relations(image,owner_raw,owner_matches[0][1],owner_rel,sections_c)", " owner_TLS_count=counts['actual_compiler_TLS_cells']\n TLS_relations(image,owner_raw,owner_matches[0][1],owner_rel,sections_c)\n assert counts['actual_compiler_TLS_cells']==owner_TLS_count+1\n # Preserve the accepted named bridge/body TLS counter domain. This new\n # owner-scope supplement is counted separately; the physical row remains.\n counts['actual_compiler_TLS_cells']=owner_TLS_count\n counts['actual_bridge_owner_TLS_cells']+=1")]
pins={str(old/'report.json'):sha(old/'report.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())};relations=[]
for n in ['accepted131-materialized.py','native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py','native-linked.py','inputs.json']:
 p=old/n;assert sha(p)==pr['files'][str(p)];pins[str(p)]=sha(p);s=p.read_text()
 if n=='native-linked.py':
  for a,b in changes:assert s.count(a)==1;s=s.replace(a,b)
  restored=s
  for a,b in reversed(changes):restored=restored.replace(b,a)
  assert restored==p.read_text()
 (out/n).write_text(s);pins[str(out/n)]=sha(out/n);relations.append(dict(file=n,parent_sha256=sha(p),whole_equal=n!='native-linked.py',exact_inverse=n=='native-linked.py'))
checker=R/'tools/m4-138-criteria-frontier/check_schema138_v3.py';pins[str(checker)]=sha(checker)
result=dict(passed=True,scope='Code-only actual guarded CALL/unwind attribution and separate extra owner TLS evidence domain; no checker/worker/reader execution',whole_extracted_baseline_predicates_preserved=True,relations=relations,changes=[dict(before=a,after=b)for a,b in changes],files=pins)
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(sha(out/'report.json'))
