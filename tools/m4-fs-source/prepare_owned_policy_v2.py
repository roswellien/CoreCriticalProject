"""Additive correction of the handler PC/address schema, with exact ledger joins."""
from pathlib import Path
import hashlib

ROOT=Path(__file__).resolve().parents[2]
old=ROOT/'tools/m4-fs-source/compare_owned_policy.py'
new=ROOT/'tools/m4-fs-source/compare_owned_policy_v2.py'
assert not new.exists(), 'Preserve the next owner checker version'
assert hashlib.sha256(old.read_bytes()).hexdigest()=='f7faedbc7e7285d1dee94a05101abaa10ef0c75beada3078625b669a356fe41b'
s=old.read_text()
s=s.replace('"""Exact current109 shared-owner typed relation, preserving branch padding."""','"""Exact current109 shared-owner relation, PC/address schema and raw ledger joins."""')
anchor="  pin(__file__);need(json.loads(pin(native_report).read_bytes())['passed'],'Final native109 execution');"
assert s.count(anchor)==1
s=s.replace(anchor,"""  pin(__file__)
  schema=json.loads(pin(ROOT/'reports/m4-mfc-native/preparation-r1/mfc-interface.json').read_bytes())
  need(schema['witness_words'][14:16]==['handlerReadPC','handlerValue'] and schema['import_words']==['v','index','root','pc','address','raw','projected','kind'],'Independent witness field14 is source readPC; source address is a distinct import-ledger field')
  provider=json.loads(pin(ROOT/'reports/m4-mfc-review/interface-r1/instruction-contracts.json','94fddd9fc34c0d1dff5100ae8a9f5c66b39e66854a1e5a2d07ac81966656dfeb').read_bytes())
  oldgame=json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json').read_bytes())
  PE=load(ROOT/'tools/analysis/pe.py','owned_source_pe')
  mfcpath=pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8')
  gamepath=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
  mfcimage=PE.PEImage(mfcpath.read_bytes());gameimage=PE.PEImage(gamepath.read_bytes())
  for pc,address,bytes_hex,contract,image in ((0x5f401ea1,0x5f49814c,'8b1d4c81495f',provider,mfcimage),(0x5f401ead,0x5f498970,'8b357089495f',provider,mfcimage),(0x5f401786,0x5f498148,'ff154881495f',provider,mfcimage),(0x5abd26,0x5bb4bc,'ff25bcb45b00',oldgame,gameimage)):
   row=next(r for r in contract['instructions'] if r['pc']==pc)
   memory=[o for o in row['decoded_operands'] if o['kind']=='memory']
   need(row['width']==6 and row['bytes_hex']==bytes_hex and len(memory)==1 and memory[0]['displacement']==address and memory[0]['bits']==32 and not memory[0]['terms'],'Independent physical source owning-import/handler PC and DWORD address')
   offset,_=image.rva_range(pc-image.image_base,6);need(image.read(offset,6)==bytes.fromhex(bytes_hex),'Exact authenticated PE operand bytes for import/handler source PC')
   counts['physical_import_source_instructions']+=1
  need(json.loads(pin(native_report,'f388380178cef6a17aa38eb8de39f19ed04ce49fa84caa8889bb4be75325763b').read_bytes())['passed'],'Final native109 execution');""")
oldcheck="and r[14:16]==(0x5f498970,0xffffffff),'Exact MFC allocator owning-IAT/handler source reads')"
assert s.count(oldcheck)==1
s=s.replace(oldcheck,"and r[14:16]==(0x5f401ead,0xffffffff),'Exact MFC allocator owning-IAT and handler readPC/value')")
anchor="      phase=phases[binding['root']];meta="
assert s.count(anchor)==1
s=s.replace(anchor,"""      call=program[binding['CALL_pc']];need(call['mnemonic']=='call' and r[6]==binding['CALL_pc']+call['width'] and r[12]==r[5]-24,'Physical genuine game CALL return and nested cdecl malloc frame')
      phase=phases[binding['root']];meta=""")
anchor="       if endpoint!='cleaned':need(ledger[8]"
assert s.count(anchor)==1
s=s.replace(anchor,"""       imports=rows(native.data(prefix+'mfc-import-ledger.bin'),8)
       observed=[w for w in imports if w[1]==r[1]]
       expected=[(1,r[1],binding['root'],0x5abd26,0x5bb4bc,0x80000337,0x5f401ea0,0),(1,r[1],binding['root'],0x5f401ea1,0x5f49814c,0x78001498,0x780012b3,1),(1,r[1],binding['root'],0x5f401ead,0x5f498970,0xffffffff,0xffffffff,3)]
       if endpoint=='cleaned':expected.append((1,r[1],binding['root'],0x5f401786,0x5f498148,0x7800138a,0x78001390,2))
       need(observed==expected,'Every exact source import/handler ledger row, including distinct source PC/address, owner index/root, raw/delivered identity and genuine free')
       counts['exact_owner_source_import_ledger_rows']+=len(expected);counts['exact_owner_source_import_ledger_endpoints']+=1
       if endpoint!='cleaned':need(ledger[8]""")
anchor="else:need(ledger[8:12]==(0,0,1,0)and record[25]==0x5f401782"
assert s.count(anchor)==1
s=s.replace(anchor,"else:need(record[27]==record[26]-8 and ledger[8:12]==(0,0,1,0)and record[25]==0x5f401782")
anchor="FS_handler_execution=False,files=PINS"
assert s.count(anchor)==1
s=s.replace(anchor,"FS_handler_execution=False,receipt_schema_correction='Native MFC witness word14 is handlerReadPC5F401EAD; exact operand address5F498970 is independently PE-authenticated and joined through import-ledger field4.',supersedes_failed_owner_checker='paired-owned-policy-r1 schema expectation only; all previous captures and candidate sources are retained unchanged',files=PINS")
compile(s,str(new),'exec');new.write_text(s)
print(hashlib.sha256(new.read_bytes()).hexdigest())
