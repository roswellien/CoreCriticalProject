"""Independent bounded prepared observer/source chronology review. No archives."""
from pathlib import Path
import json,hashlib,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];P={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix not in('.mwb','.zip');d=sha(p);assert h is None or d==h,(p,h,d);P[str(p)]=d;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
 prep=read(R/'reports/m4-formatting-source/provider130-preparation-r6/report.json','e54661004e29d8fba117a86b724005c20fd616aac1009c28c0e2b9a8110dbdb0');assert prep['passed']and prep['whole_FS_raw16Q']and not prep['executed']and not prep['capture_reader_opened']
 for p,h in prep['files'].items():pin(p,h)
 base=pin(R/'tools/m4-formatting-source/formatting_derivations.py').read_text();v2=pin(R/'tools/m4-formatting-source/formatting_derivations_v2.py').read_text();v3=pin(R/'tools/m4-formatting-source/formatting_derivations_v3.py').read_text();observer=pin(R/'tools/m4-formatting-source/final_observer130_v2.py').read_text();parent=pin(R/'tools/m4-formatting-source/final_observer130.py').read_text();provider=pin(prep['tool']).read_text()
 for a in("all(w[1]==i for i,w in enumerate(actual_all))","equal(w,expected,'Whole16Q mixed private owned operand source relation')","equal(w,expected,'Complete16Q mixed publication from actual source occurrence')","equal(actual_frames[frame['index']],expected","equal(im,(1,root,site,spec['owning_IAT'],r[2],spec['source_target'],ri+1,0)","m.bytes(a['guest']+request,a['extent']-request)==a['initial'][request:]"):
  assert a in base,a
 for a in("source_call['EAX_after']","source_call['source_access_entered_index']==pi+1","source_call['source_access_returned_index']==ei+1","source_call['API_index']==api['API_index']","source_call['API_after']==api['API_index']+1"):
  assert a in v2,a
 for a in("*raw,ev['source_access_index']+int(point==84),read['before_head'],frame['depth']+int(point==84),0xffffffff,0","equal(w,expected_raw","all(w[1]==i for i,w in enumerate(raw_frames))"):
  assert a in v3,a
 for a in("m.reg('ecx')==frame+48","source_State_before_hex=bytes(m.state).hex()","m.reg('esp')==r['frame']+4","EAX_after=m.reg('eax')","source_State_after_hex=bytes(m.state).hex()"):
  assert a in observer,a
 for a in("len(actual)==len(self.mfc)==68","len(allocations)==len(responses.allocations)==92","for owner in reversed(responses.allocations)","w[14:17]==(1,1,owner['native'])","COUNTS['actual_source_frees']+=88","COUNTS['selected_registration_closures']+=101","COUNTS['complete_Lockit_semantic_API_relations']+=36"):
  assert a in parent,a
 for a in("R.EXPECTED_LOCKIT_CALLS=36","len(image_raw)==36*40","len(machine.lockit_state_reads)==36","len(fs_observations)==84","len(fsframes)==28 and len(rawrecords)==56","index==28","len(rows)==1560 and len(format_rows)==48 and len(cosine_rows)==12 and len(tree_rows)==12","counts['whole_page_BEFORE']==counts['whole_page_AFTER']==1560*46","need(READS<=set(PINS)","a.close();a.entries.clear()"):
  assert a in provider,a
 assert provider.count('B2.bootstrap(')==1
 for a in("equal(bytes(machine.state),b[141540:145044]","equal(bytes(machine.state),b[145044:148548]","equal(machine.cpu,b[76:116]","equal(fx,b[628:1140]","equal(env,b[2192:2220]","equal(machine.bytes(p,4096),actual"):
  assert a in provider,a
 library=pin(R/'reports/m4-formatting-native/preparation-r19/fs_operations.inc').read_text();assert 'scope,record.source_access_index'not in library # full exact native raw record is checked by v3, no guessed schema substitution
 for rel in('tools/m4-tree-source/final_observer125_v2.py','tools/m4-lockit-source/identity_records.py','tools/m4-formatting-source/continuity130.py'):pin(R/rel)
 pin(__file__);target=out/'report.json';target.write_text(json.dumps(dict(passed=True,scope='Independent prepared combined130 source/provider code review of exact private operand/publication/FS/CALL chronology, persistent machine conservation and normal complete lifecycle inventory; actual run2 output and executed dependency closure remain required',preparation_sha256=sha(R/'reports/m4-formatting-source/provider130-preparation-r6/report.json'),source_and_provider_combined=True,whole_mixed_owned_row_words=16,whole_mixed_publication_row_words=16,whole_mixed_frame_words=32,whole_mixed_raw_FS_words=16,source_after_machine_seed=False,bootstrap_calls=1,planned_sequences=12,planned_phases=1560,planned_source_page_endpoints=143520,planned_MFC_per_sequence=68,planned_string_per_sequence=19,planned_formatter_per_sequence=4,planned_peak_owners=92,planned_callbacks_per_sequence=101,planned_source_frees_per_sequence=88,planned_CS_deletes_per_sequence=5,planned_Lockit_API_relations_per_sequence=36,planned_FS_invocations_per_sequence=28,planned_raw_FS_snapshots_per_sequence=56,capture_archives_opened=0,actual_execution_review=False,whole_dependency_union_physically_rehashed=False,initializer_credit=0,files=P),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(target))))
if __name__=='__main__':main(sys.argv[1])
