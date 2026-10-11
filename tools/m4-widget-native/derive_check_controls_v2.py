"""Exact additive two-source-store bootstrap baseline for frozen controls."""
from pathlib import Path
import ast,hashlib
R=Path(__file__).resolve().parents[2]
parent=R/'tools/m4-widget-native/check_controls.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='40f7b545055c86f4b183c164b33f40dd0c240c43d6a3ba18a49ad4a8a9cd028a'
out=R/'tools/m4-widget-native/check_controls_v2.py';assert not out.exists()
t=parent.read_text()
needle="  seen=set()\n"
replacement="""  pin(R/'tools/m4-widget-native/check_controls.py','40f7b545055c86f4b183c164b33f40dd0c240c43d6a3ba18a49ad4a8a9cd028a');pin(R/'tools/m4-widget-native/derive_check_controls_v2.py')
  game=raw(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');nt=struct.unpack_from('<I',game,0x3c)[0];sections=struct.unpack_from('<H',game,nt+6)[0];optional=struct.unpack_from('<H',game,nt+20)[0];base=struct.unpack_from('<I',game,nt+24+28)[0]
  session=raw(R/'reports/m4-widget-native/service-preparation-r3/session_impl.inc').decode();need('binding->registry_root_=0x5ac3d8' in session and 'lb::dispatch_body(0x5ac3d8,&s,binding.get())' in session and 'r.memory().load<unsigned>({0x9a17ec})==UINT32_MAX&&r.memory().load<unsigned>({0x9a17f0})==UINT32_MAX' in session,'Actual current bootstrap invokes literal sentinel fragment and checks both stores')
  sentinel=((0x5ac3d8,0x9a17ec,'c705ec179a00ffffffff'),(0x5ac3e2,0x9a17f0,'c705f0179a00ffffffff'))
  for pc,address,hexbytes in sentinel:
   matches=[];rva=pc-base
   for i in range(sections):
    off=nt+24+optional+40*i;virtual_size,va,raw_size,raw_offset=struct.unpack_from('<IIII',game,off+8)
    if va<=rva and rva+10<=va+raw_size:matches.append(game[raw_offset+rva-va:raw_offset+rva-va+10])
   eq(matches,[bytes.fromhex(hexbytes)],'Whole exact physical MOV absolute sentinel instruction');eq(struct.unpack('<I',bytes.fromhex(hexbytes)[2:6])[0],address,'Literal physical sentinel operand address');eq(struct.unpack('<I',bytes.fromhex(hexbytes)[6:])[0],0xffffffff,'Literal physical sentinel source immediate');counts['whole_physical_bootstrap_sentinel_instructions']+=1
  seen=set()
"""
assert t.count(needle)==1;t=t.replace(needle,replacement)
needle="   if mode==3:store(physical,0x5bb070,bytes(4))\n"
replacement="""   bootstrap_accesses=rows(raw(folder/'retry-before/locale-source-accesses.bin'),24,'<IIQII')
   for pc,address,hexbytes in sentinel:
    eq([v for v in bootstrap_accesses if v[0]==pc],[(pc,address,0xffffffff,4,1)],'Exact actual bootstrap source ledger joins independently physical sentinel MOV');eq(payload(physical,address,4),bytes(4),'Authentic physical sentinel input before bootstrap is zero');store(physical,address,struct.pack('<I',0xffffffff));counts['exact_actual_bootstrap_sentinel_store_joins']+=1
   if mode==3:store(physical,0x5bb070,bytes(4))
"""
assert t.count(needle)==1;t=t.replace(needle,replacement)
t=t.replace("bootstrap_and_cleanup_source_execution_modeled=False,hardware_scope=", "bootstrap_and_cleanup_source_execution_modeled=False,finite_bootstrap_effects='Only two physically authenticated MOV DWORD sentinel stores joined to actual source ledger; entire remaining own Game input remains exact',hardware_scope=")
assert t.count("finite_bootstrap_effects=")==1
ast.parse(t);out.write_text(t)
print(out,hashlib.sha256(out.read_bytes()).hexdigest())
