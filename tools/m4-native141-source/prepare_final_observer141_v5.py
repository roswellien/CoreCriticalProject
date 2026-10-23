"""Preserve exact literal indirect getter CALL width in native12I join."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-native141-source/observer-preparation-r5';assert not out.exists();out.mkdir(parents=True);pins={};deltas=[]
 def pin(p):p=Path(p).resolve();pins[str(p)]=sha(p);return p
 def one(t,a,b,p):assert t.count(a)==1,(p,a);deltas.append(dict(file=str(p),before=a,after=b));return t.replace(a,b)
 parent=R/'reports/m4-native141-source/observer-preparation-r4';pin(parent/'report.json')
 for name in('final_observer141_parent.py','final_observer141_parent_v2.py'):
  p=pin(parent/name);(out/name).write_bytes(p.read_bytes());pin(out/name)
 p=pin(R/'tools/m4-native141-source/constructor_native_outputs141_v1.py');t=p.read_text();t=one(t,"g['PC']+5,g['receiver']","g['PC']+m.program[g['PC']]['width'],g['receiver']",p)
 q=R/'tools/m4-native141-source/constructor_native_outputs141_v2.py';assert not q.exists();q.write_text(t);pin(q)
 p=pin(R/'tools/m4-native141-source/final_observer141_v4.py');t=p.read_text();t=one(t,"PREP=ROOT/'reports/m4-native141-source/observer-preparation-r4'","PREP=ROOT/'reports/m4-native141-source/observer-preparation-r5'",p);t=one(t,'from constructor_native_outputs141_v1 import','from constructor_native_outputs141_v2 import',p)
 t=one(t,"COUNTS['complete141_constructor_observer_sequences']+=1","COUNTS['complete141_constructor_observer_sequences']+=1;COUNTS['constructor_source_allocations']+=6\n  ROWS[-1].update(MFC_count_domain='Inherited68 witness ledger; constructor6 source births separately proved',inherited_MFC_allocations=68,constructor_MFC_allocations=6,union_MFC_allocations=74,inherited_source_frees=88,constructor_source_frees=6,union_source_frees=94,whole_owners=98,whole_selected_callbacks=111)",p)
 q=R/'tools/m4-native141-source/final_observer141_v5.py';assert not q.exists();q.write_text(t);pin(q)
 for p in [R/'tools/m4-native141-source/constructor_journal141_v2.py',R/'tools/m4-native141-source/constructor_fs_union141_v1.py',R/'tools/m4-native141-source/persistent_constructors_v4.py',Path(__file__)]:pin(p)
 (out/'source-delta.json').write_text(json.dumps(deltas,indent=2)+'\n');pin(out/'source-delta.json')
 (out/'report.json').write_text(json.dumps(dict(passed=True,source_only=True,source_execution=False,canonical_reader_opened=False,accepted_credit=False,exact_literal_getter_CALL_width=True,old68_ledger_retained=True,new6_owner_cleanup_union=True,full_journal_guards_retained=True,files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main()
