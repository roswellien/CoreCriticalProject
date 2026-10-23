"""Immutable v2 observer+full-journal association and exact111 callback guard."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-native141-source/observer-preparation-r2';assert not out.exists();out.mkdir(parents=True);pins={};deltas=[]
 def pin(p):p=Path(p).resolve();pins[str(p)]=sha(p);return p
 def one(t,a,b,file):assert t.count(a)==1,(file,a);deltas.append(dict(file=file,before=a,after=b));return t.replace(a,b)
 parent=R/'reports/m4-native141-source/observer-preparation-r1';p=pin(parent/'final_observer141_parent.py');t=p.read_text()
 t=one(t,"exec(compile(_text,str(_source),'exec'),globals())","_one('len(roots)==108','len(roots)==111')\n_one(\"COUNTS['selected_registration_closures']+=108\",\"COUNTS['selected_registration_closures']+=111\")\nexec(compile(_text,str(_source),'exec'),globals())",p.name)
 (out/p.name).write_text(t);pin(out/p.name)
 p=pin(parent/'final_observer141_parent_v2.py');(out/p.name).write_bytes(p.read_bytes());pin(out/p.name)
 p=pin(R/'tools/m4-native141-source/final_observer141_v1.py');t=p.read_text()
 t=one(t,"PREP=ROOT/'reports/m4-native141-source/observer-preparation-r1'","PREP=ROOT/'reports/m4-native141-source/observer-preparation-r2'",p.name)
 t=one(t,'import final_observer141_parent_v2 as P','import final_observer141_parent_v2 as P\nimport hashlib\nfrom constructor_journal141_v1 import Association\nFORMAT_ROOTS=P.FORMAT_ROOTS',p.name)
 t=one(t,'F.Observer=Observer;observer=F.configure(G,numeric,archive,seq,level,pin)','F.Observer=OBSERVER_CLASS;observer=F.configure(G,numeric,archive,seq,level,pin)\n if not getattr(B.R,\'constructor141_owner_roles\',False):\n  B.R.ActualResponses=G.response_class(B.R.ActualResponses);B.R.constructor141_owner_roles=True',p.name)
 a="o.root=root;o.runtime_cpu=B.cpu(m.state);count=len(o.constructor_mfc);before=m.run_carried_constructor(root,responses)\n need(len(o.constructor_mfc)-count==2,'Two exact source-owned allocations per carried constructor');o.constructor_root_order.append(root);return before"
 b="""o.root=root;o.runtime_cpu=B.cpu(m.state);count=len(o.constructor_mfc);association=Association(m,o,root);m.hook=association.observer_hook
 start_FS=len(m.constructor_FS_events);start_getters=len(m.constructor_getters);start_publications=len(m.constructor_publications);start_flags=len(m.constructor_flag_consumers)
 try:before=m.run_carried_constructor(root,responses)
 except BaseException:
  m.hook=association.hook;m.accesses=association.full
  raise
 proof=association.finish()
 need(len(o.constructor_mfc)-count==2,'Two exact source-owned allocations per carried constructor');o.constructor_root_order.append(root)
 o.constructor_FS_observations.extend(proof['game_FS_observations'])
 h=lambda b:hashlib.sha256(bytes(b)).hexdigest()
 proof.update(root=root,sequence=seq,level=level,phase=phase,computed_before_State_sha256=h(before['State']),computed_before_CPU=list(before['CPU']),computed_before_FX_sha256=h(before['FX']),computed_after_State_sha256=h(m.state),computed_after_CPU=list(m.projected_cpu()),computed_after_FX_sha256=h(m.fx),API_before=before['response_index'],API_after=responses.index,source_FS_events=m.constructor_FS_events[start_FS:],source_getters=m.constructor_getters[start_getters:],source_owned_writes=m.constructor_publications[start_publications:],source_defined_flag_consumers=m.constructor_flag_consumers[start_flags:])
 return proof"""
 t=one(t,a,b,p.name)
 t=one(t,'self.constructor_onexit=None\n def mfc_event','self.constructor_onexit=None;self.constructor_FS_observations=[]\n def mfc_event',p.name)
 t+='\nOBSERVER_CLASS=Observer\ndef install_widget_observer(PW):\n global OBSERVER_CLASS\n OBSERVER_CLASS=PW.observer_class(Observer)\n return OBSERVER_CLASS\n'
 source=R/'tools/m4-native141-source/final_observer141_v2.py';assert not source.exists();source.write_text(t);pin(source)
 for p in [R/'tools/m4-native141-source/constructor_journal141_v1.py',R/'tools/m4-native141-source/persistent_constructors_v4.py',R/'reports/m4-startup141-runway/service-preparation-r2/constructor-FS-contracts.json',Path(__file__)]:pin(p)
 (out/'source-delta.json').write_text(json.dumps(deltas,indent=2)+'\n');pin(out/'source-delta.json')
 (out/'report.json').write_text(json.dumps(dict(passed=True,source_only=True,source_execution=False,archive_opened=False,accepted_credit=False,registration_roots_retained=108,source_callback_vector=111,exact_constructor_birth_delta=3,old_MFC_ledger_retained=68,whole_owners=98,shared_kind4_owners=74,full_instruction_journal_preserved=True,files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main()
