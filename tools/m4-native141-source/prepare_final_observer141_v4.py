"""Immutable exact physical imports and whole component/mirror proof joins."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-native141-source/observer-preparation-r4';assert not out.exists();out.mkdir(parents=True);pins={};deltas=[]
 def pin(p):p=Path(p).resolve();pins[str(p)]=sha(p);return p
 def one(t,a,b,file):assert t.count(a)==1,(file,a);deltas.append(dict(file=file,before=a,after=b));return t.replace(a,b)
 parent=R/'reports/m4-native141-source/observer-preparation-r3';pin(parent/'report.json')
 for name in('final_observer141_parent.py','final_observer141_parent_v2.py'):
  p=pin(parent/name);(out/name).write_bytes(p.read_bytes());pin(out/name)
 src=pin(R/'tools/m4-native141-source/constructor_journal141_v1.py');t=src.read_text()
 t=one(t,'self.fs=[];self.specs=fs_specs()','self.fs=[];self.specs=fs_specs();self.mirrors=[];self.component_FS=[];self.game_frames=[];self.serial=o.constructor_game_FS_serial',src.name)
 a="self.component.append(row)";b="""self.component.append(row)
    owners=[a for a in m.responses.allocations if a['live']and a['guest']<=row[1]and row[1]+row[3]<=a['guest']+a['mapped']];need(len(owners)<=1,'At most one exact current source owner extent')
    owner=owners[0]if owners else None
    if row[4]or owner:
     if owner:need(owner.get('kind')==4 and row[1]+row[3]<=owner['guest']+owner['requested'],'Source literal component operand remains inside actual MFC request')
     self.mirrors.append((self.root,row[0],row[1],row[3],row[2],row[4],owner['guest']if owner else 0,owner['generation']if owner else 0,owner['requested']if owner else 0,owner['extent']if owner else 0,owner.get('capacity',0)if owner else 0,0))
    if row[1]==m.word(2168):
     previous=self.fs[-1]['before_head'];kind=0
     if row[4]:
      if self.game_frames and row[2]==self.game_frames[-1][1]:
       frame,prev=self.game_frames.pop();need(previous==frame and word(m,frame)==prev,'Same literal game constructor predecessor restored');kind=2
      else:
       need(row[2]==m.reg('esp')and word(m,row[2])==previous,'Exact literal game source frame installed');self.game_frames.append((row[2],previous));self.serial+=1;kind=1
     else:need(row[2]==previous,'Whole actual source FS read')
     self.component_FS.append((self.root,row[0],row[4],previous,row[2],kind,len(self.game_frames),self.serial,0,0,0,0))"""
 t=one(t,a,b,src.name)
 t=one(t,"self.m.accesses=self.provider;self.m.hook=self.hook","need(not self.game_frames,'All independent component game FS scopes restored');self.o.constructor_game_FS_serial=self.serial\n  self.m.accesses=self.provider;self.m.hook=self.hook",src.name)
 t=one(t,"game_FS_observations=self.fs,full_literal_journal_preserved_during_instruction_guards=True","game_FS_observations=self.fs,component_FS_rows=[list(r)for r in self.component_FS],constructor_mirror_rows=[list(r)for r in self.mirrors],full_literal_journal_preserved_during_instruction_guards=True",src.name)
 q=R/'tools/m4-native141-source/constructor_journal141_v2.py';assert not q.exists();q.write_text(t);pin(q)
 src=pin(R/'tools/m4-native141-source/final_observer141_v3.py');t=src.read_text()
 t=one(t,"PREP=ROOT/'reports/m4-native141-source/observer-preparation-r3'","PREP=ROOT/'reports/m4-native141-source/observer-preparation-r4'",src.name)
 t=one(t,'from constructor_journal141_v1 import Association','sys.path.insert(0,str(Path(__file__).resolve().parent))\nfrom constructor_journal141_v2 import Association\nfrom constructor_native_outputs141_v1 import install_named,compare as compare_native_constructor',src.name)
 t=one(t,'self.constructor_FS_observations=[]','self.constructor_FS_observations=[];self.constructor_game_FS_serial=0;self.constructor_mirror_rows=[];self.constructor_call_results=[]',src.name)
 a="self.check(m,f'constructor-mfc-{len(self.constructor_call_rows)-1}-after');self.constructor_active_call=None"
 b="self.constructor_call_results.append((c['root'],c['site'],c['thunk'],c['frame'],c['ret'],c['request'],m.reg('eax'),0,0,0,0,0));"+a
 t=one(t,a,b,src.name)
 t=one(t,"o.root=root;o.runtime_cpu=B.cpu(m.state);count=len(o.constructor_mfc);association=Association(m,o,root);m.hook=association.observer_hook","o.root=root;o.runtime_cpu=B.cpu(m.state);count=len(o.constructor_mfc);install_named(m,o);call_start=len(o.constructor_call_results);association=Association(m,o,root);m.hook=association.observer_hook",src.name)
 t=one(t,"o.constructor_FS_observations.extend(proof['game_FS_observations'])","o.constructor_FS_observations.extend(proof['game_FS_observations']);o.constructor_mirror_rows.extend(proof['constructor_mirror_rows']);proof['constructor_call_results']=[list(r)for r in o.constructor_call_results[call_start:]]",src.name)
 t=one(t,' return proof\ndef prove_constructor_projections',' compare_native_constructor(a,seq,root,before,m,proof,o)\n return proof\ndef prove_constructor_projections',src.name)
 t+='''
_owners_parent=Observer.owners
def _owners141(self,m,responses,stage,expected_callbacks):
 _owners_parent(self,m,responses,stage,expected_callbacks)
 actual=list(struct.iter_unpack('<12Q',self.a.data(f'sequence-{self.seq}/{stage}/constructor-source-mirror-accesses.bin')))
 need(actual==[tuple(r)for r in self.constructor_mirror_rows],'Whole constructor mirror journal from current source operands/owners/generations')
 need(self.a.words(f'sequence-{self.seq}/{stage}/constructor-FS-source-scope.bin',2)==(0,0),'All literal constructor component/provider ownership scopes closed')
Observer.owners=_owners141
'''
 q=R/'tools/m4-native141-source/final_observer141_v4.py';assert not q.exists();q.write_text(t);pin(q)
 for p in [R/'tools/m4-native141-source/constructor_native_outputs141_v1.py',R/'tools/m4-native141-source/constructor_fs_union141_v1.py',R/'tools/m4-native141-source/persistent_constructors_v4.py',R/'reports/m4-138-validation-review/constructor-provider-named-proof-r1/report.json',R/'reports/m4-138-validation-review/constructor-source-dependency-review-r8/report.json',Path(__file__)]:pin(p)
 corrected_v3=dict(parent=str((R/'tools/m4-native141-source/final_observer141_v2.py').resolve()),parent_sha256=sha(R/'tools/m4-native141-source/final_observer141_v2.py'),child=str((R/'tools/m4-native141-source/final_observer141_v3.py').resolve()),child_sha256=sha(R/'tools/m4-native141-source/final_observer141_v3.py'),metadata_only_correction=True,retained_defect=str(parent/'source-delta.json'))
 (out/'corrected-v3-source-parent.json').write_text(json.dumps(corrected_v3,indent=2)+'\n');pin(out/'corrected-v3-source-parent.json')
 (out/'source-delta.json').write_text(json.dumps(deltas,indent=2)+'\n');pin(out/'source-delta.json')
 (out/'report.json').write_text(json.dumps(dict(passed=True,source_only=True,source_execution=False,canonical_reader_opened=False,accepted_credit=False,whole_component_access_calls_FS_getters_State_CPU_FX_compared_at_execution=True,whole_mirror_journals_at_all3_lifecycle_stages=True,physical_named_import_proof_required=True,full_instruction_journal_preserved=True,files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main()
