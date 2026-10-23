"""Current compiled-review actual schema, same physical build requirement."""
from pathlib import Path
import hashlib,json,ast,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141-source/old4-preparation-r2';assert not out.exists();out.mkdir();rows=[];files={}
 specs=[('old4_source141_v1.py','old4_source141_v2.py',[("review['build_sha256']==validation['build_sha256']","review['files'][str(Path(validation['build_path']).resolve())]==validation['build_sha256']and Path(review['actual_compiled_preparation']).resolve()==Path(CONFIG['source_preparation']['path']).parent.resolve()")]),('replay_original141_v6.py','replay_original141_v7.py',[("'old4_source141_v1.py'","'old4_source141_v2.py'")])]
 for parent,child,changes in specs:
  p=R/'tools/m4-original141-source'/parent;q=p.with_name(child);assert not q.exists();a=p.read_text();b=a
  for old,new in changes:assert b.count(old)==1;b=b.replace(old,new)
  ast.parse(b);q.write_text(b);back=b
  for old,new in reversed(changes):assert back.count(new)==1;back=back.replace(new,old)
  assert back==a;before=a.splitlines(True);after=b.splitlines(True);d=[]
  for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
   if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(before[i:j]),child=''.join(after[k:l])))
  assert len(d)==1;rows.append(dict(parent=str(p),child=str(q),exact_whole_inverse=True,hunks=1,deltas=d));files[str(p)]=sha(p);files[str(q)]=sha(q)
 report=R/'reports/m4-original141/root-compiled-review-r2/report.json';v=json.loads(report.read_bytes());build=R/'reports/m4-original141/build-r2/build.json';assert 'build_sha256'not in v and v['files'][str(build.resolve())]==sha(build)and Path(v['actual_compiled_preparation']).resolve()==(R/'reports/m4-original141/source-preparation-r6').resolve()
 (out/'inverse.json').write_text(json.dumps(rows,indent=2)+'\n')
 for p in [report,build,out/'inverse.json',Path(__file__).resolve()]:files[str(p)]=sha(p)
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_reader_opened=False,initializer_credit=0,whole_inverse_files=rows,semantic_delta='Replace nonexistent currentcompiledreview build_sha256 field with actual authoritative files[whole currentbuild.json] same exact validationbuildSHA, additionally require same actualcompiled source6 directory. No source/body/span/owner/FS/API/frame/page/CPUFXENV change. Controller7 binds only old4v2 atopformatter2/currentcorpus2.',files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main()
