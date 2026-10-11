"""Prepare finite literal registry provider and FPS registration tail checks."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-fps-native'/name;assert not out.exists();out.mkdir();parent=R/'tools/m4-widget-source-review/compare_registry_v7.py';target=R/'tools/m4-fps-native/compare_registry.py';assert not target.exists();t=parent.read_text();changes=[]
 def change(a,b,n=1):
  nonlocal t
  assert t.count(a)==n,(a,t.count(a));t=t.replace(a,b);changes.append(dict(before=a,after=b,count=n))
 change("R/'tools/m4-widget-native/compare_prefix_v4.py'","R/'tools/m4-fps-native/compare_prefix_v2.py'")
 change("out=R/'reports/m4-widget-native'","out=R/'reports/m4-fps-native'")
 change("len(derivations)==12,'Twelve physically bound prefix entry joins'","len(derivations)==14,'Fourteen physically bound prefix entry joins'")
 change("reports/m4-font479590-original/source-preparation-r1/game_model.py","reports/m4-fps-original/source-preparation-r4/game_model.py")
 change("contract=read(R/'reports/m4-widget-native/preparation-r3/contracts.json')","contract=read(R/'reports/m4-fps-native/component-preparation-r1/contracts.json')")
 change("need(tail['passed'],'Exact independently reviewed affine widget tail')","need(tail['passed'],'Exact independently reviewed prior six widget tails');need(len(contract['registration_epilogues'])==7,'Exact additive FPS tail contract')")
 change("reports/m4-widget-native/service-preparation-r3/locale_batch_operations.inc","reports/m4-fps-native/service-preparation-r2/locale_batch_operations.inc")
 change("reports/m4-widget-native/service-preparation-r3/lockit_operations.inc","reports/m4-fps-native/service-preparation-r2/lockit_operations.inc")
 change("len(before)==len(after)==6","len(before)==len(after)==7")
 change("'Six ordered actual provider entry/return boundaries'","'Seven ordered actual provider entry/return boundaries'")
 change("counts['whole_source_root_State3504_relations']==12 and counts['literal_tail_instructions']==120 and counts['literal_tail_RET_operand_relations']==36","counts['whole_source_root_State3504_relations']==14 and counts['literal_tail_instructions']==140 and counts['literal_tail_RET_operand_relations']==42")
 change("Exact six-root both-level source tail extent","Exact seven-root both-level source tail extent")
 marker="  contract=read(R/'reports/m4-fps-native/component-preparation-r1/contracts.json');"
 assert t.count(marker)==1
 extra="""  game=raw(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');nt=struct.unpack_from('<I',game,0x3c)[0];ns=struct.unpack_from('<H',game,nt+6)[0];opt=struct.unpack_from('<H',game,nt+20)[0];base=struct.unpack_from('<I',game,nt+24+28)[0]
  exact_contract=read(R/'reports/m4-fps-native/component-preparation-r1/contracts.json');epilogue=exact_contract['registration_epilogues'][-1];need(epilogue['root']==0x40f000 and epilogue['source_read_PC_and_frame_offsets']==[[0x5ac127,-16,4,False],[0x5ac154,-8,4,False],[0x40f02d,0,4,False]],'Three literal saved-return reads use exact affine FPS frames')
  rows_={v['pc']:v for v in exact_contract['instructions']}
  for pc in epilogue['source_PCs']:
   row=rows_[pc];payload=bytes.fromhex(row['bytes_hex']);matches=[];rva=pc-base
   for i in range(ns):
    off=nt+24+opt+40*i;vs,va,rs,ro=struct.unpack_from('<IIII',game,off+8)
    if va<=rva and rva+len(payload)<=va+rs:matches.append(game[ro+rva-va:ro+rva-va+len(payload)])
   eq(matches,[payload],'Whole actual physical FPS ten-instruction registration epilogue');counts['physical_additive_FPS_tail_instruction_joins']+=1
  contract=read(R/'reports/m4-fps-native/component-preparation-r1/contracts.json');"""
 t=t.replace(marker,extra);ast.parse(t);target.write_text(t);q=out/'source-relations.json';q.write_text(json.dumps(changes,indent=2)+'\n');pins={str(p.resolve()):sha(p)for p in(parent,target,q,Path(__file__),R/'reports/m4-fps-native/source-preparation-r1/report.json',R/'reports/m4-fps-native/compare_prefix_v2.py')};report=dict(passed=True,scope='Current literal registry provider, exact seven root epilogues and own current provider BEFORE comparison prepared only',registry_entrypoint=str(target),registry_sha256=sha(target),root_count=7,source_changes=len(changes),provider_literal_program_merged=True,AFTER_input_seed=False,host_onexit_substitution=False,actual_worker_launches=0,archive_reader_opened=False,initializer_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(q,sha(q))
if __name__=='__main__':main(sys.argv[1])
