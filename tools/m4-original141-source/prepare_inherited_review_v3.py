"""Only current physically corrected formatter/controller reviewer bindings."""
from pathlib import Path
import hashlib,json,difflib,ast
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141-source/inherited-review-preparation-r3';assert not out.exists();out.mkdir();p=R/'tools/m4-original141-source/review_inherited141_v2.py';q=p.with_name('review_inherited141_v3.py');assert not q.exists();a=p.read_text();b=a
 changes=[('format_source141_v1.py','format_source141_v2.py'),('replay_original141_v5.py','replay_original141_v7.py')]
 for old,new in changes:assert b.count(old)==1;b=b.replace(old,new)
 ast.parse(b);q.write_text(b);back=b
 for old,new in reversed(changes):assert back.count(new)==1;back=back.replace(new,old)
 assert back==a;before=a.splitlines(True);after=b.splitlines(True);d=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
  if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(before[i:j]),child=''.join(after[k:l])))
 (out/'inverse.json').write_text(json.dumps(d,indent=2)+'\n');files={str(x):sha(x)for x in[p,q,out/'inverse.json',R/'tools/m4-original141-source/format_source141_v2.py',R/'tools/m4-original141-source/replay_original141_v7.py',R/'reports/m4-original141-source/format-preparation-r2/report.json',R/'reports/m4-original141-source/old4-preparation-r2/report.json',Path(__file__).resolve()]}
 r=out/'report.json';r.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_reader_opened=False,initializer_credit=0,exact_whole_parent_inverse=True,inverse_hunks=len(d),semantic_delta='Only current exactlinked formatter2 and controller7 code bindings. All historical3955/current3980 corpus guards, actualTREE path/schema/phase86, ownerbyteflow/FS/CPUFXENV/callercoverage assertions unchanged.',actual_current_source_PASS_sha256_pending=True,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(r),sha256=sha(r))))
if __name__=='__main__':main()
