"""Additive lifetime/binding/per-case API guard repair; no capture reads."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 old=R/'tools/m4-startup130-paired/paired.py';new=old.with_name('paired_v2.py');assert not new.exists();s=old.read_text();hunks=[]
 def one(a,b):
  nonlocal s
  assert s.count(a)==1,a;s=s.replace(a,b);hunks.append(dict(old=a,new=b))
 one('   native.close();del native','   close_reader(native);native=None')
 one('  ori.close()','  close_reader(ori);ori=None')
 one(";policy_path,policy_gate,policy_sha=gate('paired_policy')", ";policy_path,policy_gate,policy_sha=gate('paired_policy');combined_review_path,combined_review_gate,combined_review_sha=gate('original_combined_review')")
 one(" policy=json.loads(pin(policy_gate['policy']", " need(combined_review_sha=='8365b62801e51146ec68bfbe597971745919c8722f2e9c411325a775376af186' and combined_review_gate['original_combined_source_sha256']==combined_sha,'Current independent original combined source review')\n policy=json.loads(pin(policy_gate['policy']")
 one("ROOT/'tools/m4-startup130-paired/format_relations.py'", "ROOT/'tools/m4-startup130-paired/format_relations_v2.py'")
 one('original_combined_source_sha256=combined_sha,','original_combined_source_sha256=combined_sha,original_combined_review_sha256=combined_review_sha,')
 ast.parse(s);new.write_text(s)
 oldf=old.with_name('format_relations.py');newf=old.with_name('format_relations_v2.py');assert not newf.exists();f=oldf.read_text()
 a="  for index,relation in enumerate(native['Lockit_API_relations']):"
 assert f.count(a)==1
 b="  need(len(native['Lockit_API_relations'])==2,'Exactly two source-derived mixed API relations per case')\n"+a
 f=f.replace(a,b);ast.parse(f);newf.write_text(f)
 out=R/'reports/m4-startup130-paired/comparer-preparation-r2';assert not out.exists();out.mkdir(parents=True)
 hp=out/'hunks.json';hp.write_text(json.dumps(dict(comparer=hunks,helper=[dict(old=a,new=b)]),indent=2)+'\n')
 paths=[old,new,oldf,newf,old.with_name('tree_relations.py'),Path(__file__),hp,R/'reports/m4-startup130-paired/comparer-preparation-r1/report.json',R/'reports/m4-tree-review/original130-combined-review-r3/report.json']
 report=dict(passed=True,scope='Additive exact reader lifetime repair, current independent source-review binding, and per-case exhaustive two mixed API guard; no capture opened',files={str(p.resolve()):sha(p)for p in paths},capture_reader_opened=False,executed=False,initializer_credit=0)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(sha(p))
if __name__=='__main__':main()
