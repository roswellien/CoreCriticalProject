"""Narrow immutable continuity binding and actual TREE aggregate schema fix."""
from pathlib import Path
import hashlib,json,difflib,ast
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141-source/controller-preparation-r5';assert not out.exists();out.mkdir();files={};rows=[]
 specs=[('replay_original141_v4.py','replay_original141_v5.py',[("'retained_corpus141_v1.py'","'retained_corpus141_v2.py'")]),('review_inherited141_v1.py','review_inherited141_v2.py',[("'retained_corpus141_v1.py'","'retained_corpus141_v2.py'"),("'replay_original141_v3.py'","'replay_original141_v5.py'"),("\"oldpages[page][1]\"in corpus and \"newpages[page][1]\"in corpus","\"actual_offset==offset\"in corpus and \"packed[page][1][at&4095:(at&4095)+n]==raw\"in corpus and \"origin_counts=={0:3962,1:18}\"in corpus"),("   child=read(case['receipt'],case['sha256']);s=case['source'];need(case['phase']==86 and s['phase']==86","   need(set(case)=={'sequence','path','sha256','source'},'Exact current TREE aggregate derivation schema');child=read(case['path'],case['sha256']);need(child['passed']and child['sequence']==case['sequence']and child['source_case_extent']==1 and child['original_validation_sha256']==C['validation']['sha256'],'Actual same-source current TREE child relation');s=case['source'];need(s['phase']==86")])]
 for parent,child,changes in specs:
  p=R/'tools/m4-original141-source'/parent;q=p.with_name(child);assert not q.exists();a=p.read_text();b=a
  for old,new in changes:assert b.count(old)==1,(old,b.count(old));b=b.replace(old,new)
  ast.parse(b);q.write_text(b);back=b
  for old,new in reversed(changes):assert back.count(new)==1;back=back.replace(new,old)
  assert back==a;before=a.splitlines(True);after=b.splitlines(True);d=[]
  for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
   if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(before[i:j]),child=''.join(after[k:l])))
  rows.append(dict(parent=str(p),child=str(q),exact_whole_inverse=True,hunks=len(d),deltas=d));files[str(p)]=sha(p);files[str(q)]=sha(q)
 (out/'inverse.json').write_text(json.dumps(rows,indent=2)+'\n');files[str(out/'inverse.json')]=sha(out/'inverse.json')
 for p in [R/'reports/m4-original141-source/retained-corpus-preparation-r3/report.json',R/'tools/m4-original141-source/retained_corpus141_v2.py',R/'reports/m4-original141-tree-source/source-r1/report.json',R/'reports/m4-original141-tree-source/source-r1/original-Tree-source-derivations.json',Path(__file__).resolve()]:files[str(p)]=sha(p)
 tree=json.loads((R/'reports/m4-original141-tree-source/source-r1/original-Tree-source-derivations.json').read_bytes());assert len(tree)==6 and all(set(row)=={'sequence','path','sha256','source'}and row['source']['phase']==86 for row in tree)
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,ordinary_export_reader_opened=False,canonical_reader_opened=False,initializer_credit=0,whole_inverse_files=rows,controller_delta='Only retained physical corpus helperv1 to v2. Source/family/registry/all69+global and actual reader domains unchanged.',reviewer_delta='Current controller5/helper2 physical source-byte guards and actual sixTREE schema sequence/path/sha/source; own source.phase86 and actual child same-validation/sequence/extent assertions retained/strengthened.',ROOT_admission_required_before_retry=True,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main()
