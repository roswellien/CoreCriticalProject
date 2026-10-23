"""Prepare exact additive observer source; no captures or machine execution."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-native141-source/observer-preparation-r1';assert not out.exists();out.mkdir(parents=True)
 pins={};deltas=[]
 def pin(p):p=Path(p).resolve();pins[str(p)]=sha(p);return p
 p=pin(R/'reports/m4-joint-startup138-source/preparation-r11/final_observer138.py');t=p.read_text()
 additions=[("_one('len(allocations)==len(responses.allocations)==85','len(allocations)==len(responses.allocations)==92')","_one('len(allocations)==len(responses.allocations)==85','len(allocations)==len(responses.allocations)==98')"),
 ('''_one("sum(a.get('kind',1)==4 for a in responses.allocations)==65","sum(a.get('kind',1)==4 for a in responses.allocations)==68")''','''_one("sum(a.get('kind',1)==4 for a in responses.allocations)==65","sum(a.get('kind',1)==4 for a in responses.allocations)==74")'''),
 ("exec(compile(_text,str(_source),'exec'),globals())","_one(\"record=next(r for r in self.mfc if r['words'][18]==owner['generation'])\",\"record=next(r for r in self.mfc+self.constructor_mfc if r['words'][18]==owner['generation'])\")\nexec(compile(_text,str(_source),'exec'),globals())")]
 for a,b in additions:assert t.count(a)==1;t=t.replace(a,b);deltas.append(dict(before=a,after=b))
 q=out/'final_observer141_parent.py';q.write_text(t);pin(q)
 w=pin(p.with_name('final_observer138_v2.py'));s=w.read_text();a='import final_observer138 as F';b='import final_observer141_parent as F';assert s.count(a)==1;s=s.replace(a,b);(out/'final_observer141_parent_v2.py').write_text(s);pin(out/'final_observer141_parent_v2.py');deltas.append(dict(file=w.name,before=a,after=b))
 for p in [R/'tools/m4-tree-source/final_observer125_v2.py',R/'tools/m4-native141-source/final_observer141_v1.py',R/'tools/m4-native141-source/persistent_constructors_v4.py',R/'reports/m4-startup141-runway/service-preparation-r2/session_impl.inc',R/'reports/m4-startup141-runway/readiness-r1/selected-order141.json',Path(__file__)]:pin(p)
 (out/'source-delta.json').write_text(json.dumps(deltas,indent=2)+'\n');pin(out/'source-delta.json')
 (out/'report.json').write_text(json.dumps(dict(passed=True,source_only=True,source_or_native_execution=False,canonical_reader_opened=False,accepted_credit=False,old_MFC_ledger_retained=68,new_constructor_owners=6,shared_kind4_owners=74,whole_owners=98,registration_roots_retained=108,files=pins),indent=2)+'\n')
 print(sha(out/'report.json'))
if __name__=='__main__':main()
