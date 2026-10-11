"""Physical table-slot plan only; isolated evidence remains unchanged."""
from pathlib import Path
import hashlib,json,struct,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-fps-native'/name;assert not out.exists();out.mkdir();cp=R/'reports/m4-fps-native/component-preparation-r1/contracts.json';contract=json.loads(cp.read_bytes());game=R/'MW3/Mech3.exe';b=game.read_bytes();assert sha(game)=='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf';nt=struct.unpack_from('<I',b,0x3c)[0];ns=struct.unpack_from('<H',b,nt+6)[0];opt=struct.unpack_from('<H',b,nt+20)[0];base=struct.unpack_from('<I',b,nt+24+28)[0]
 slots={0x40e250:0x5e0048,0x40ef50:0x5e004c,0x40f000:0x5e0050,0x479590:0x5e00cc,0x5a3c30:0x5e0234,0x5a3ff0:0x5e0238,0x5a66f0:0x5e023c};plan=[]
 for phase,root in enumerate(sorted(contract['roots'],key=lambda v:slots[v['root']])):
  slot=slots[root['root']];rva=slot-base;matches=[]
  for i in range(ns):
   off=nt+24+opt+40*i;vs,va,rs,ro=struct.unpack_from('<IIII',b,off+8)
   if va<=rva and rva+4<=va+rs:matches.append((ro+rva-va,b[ro+rva-va:ro+rva-va+4]))
  assert len(matches)==1 and struct.unpack('<I',matches[0][1])[0]==root['root'] and root['slot']==slot
  payload=json.dumps(root,sort_keys=True,separators=(',',':')).encode();plan.append(dict(group_phase=phase,isolated_phase=contract['roots'].index(root),root=root['root'],physical_slot=slot,file_offset=matches[0][0],slot_bytes_hex=matches[0][1].hex(),entire_per_root_contract_sha256=hashlib.sha256(payload).hexdigest(),GDI_rows=len(root['GDI_calls']),virtual_rows=len(root['virtual_calls']),FS_rows=len(root['FS_operations']),array_invocations=len(root['array_invocations']),registration=root['registration']))
 q=out/'phase-plan.json';q.write_text(json.dumps(plan,indent=2)+'\n');pins={str(p.resolve()):sha(p)for p in(cp,game,q,Path(__file__))};report=dict(passed=True,scope='Independent physical seven-root table-slot order and immutable isolated per-root contract association; planning only',connected_group_order=[v['root']for v in plan],isolated_group_order=[v['root']for v in contract['roots']],physical_slot_joins=7,existing_isolated_artifacts_changed=False,whole_original_chronological_prefix_required=True,phase_indexed_owners_and_source_operands_required=True,current_GDI_handle_generations_and_FS_state_must_be_rederived=True,callbacks_and_registrations_must_follow_actual_full_table=True,isolated_source_closure_implies_connected_credit=False,actual_worker_launches=0,archive_reader_opened=False,initializer_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(q,sha(q))
if __name__=='__main__':main(sys.argv[1])
