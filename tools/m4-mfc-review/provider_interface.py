"""Independent physical MFC allocator/free binding and literal operand interface.

This is a static gate. Loader identity supplies the two observed named import
bindings, while every operand comes from original bytes. No DLL is executed.
"""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-mfc-review'
MFC_SHA = '5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'
CRT_SHA = '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
GAME_SHA = '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
RECEIPTS = {
 'reports/m4-joint-startup71-root/acceptance-r1/report.json': '64c010e01930d4f84d7df9cb8cd932669ce25b6f3f1dc21989f197282025fdfc',
 'reports/m4-strings-native/next-mfc-r1/report.json': '112b31d1cb62f42756a7ae486bb174c474ea5049721f6084c57f5b701e611daf',
 'reports/m4-strings-native/next-mfc-linkage-r1/report.json': 'c10a6f6677535369cf87cf3e0ecc115c578cc51cd193c1d9ea902d68aed16bc8',
 'reports/m4-mfc-source/loader-identity-r1/report.json': '7925f659144954487b1b13d781d4aee48aa0b8d20887ce9ee8aa40ce7a12b09b',
 'reports/m4-mfc-native/lifts-r1/report.json': '3c49ba0a564416ec1c3eb1b3c656f82381947cfd47cabc8a076209246eecf73d',
}

def need(value, message):
 if not value: raise ValueError(message)
def sha(path):
 with Path(path).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def load(name, path):
 spec = importlib.util.spec_from_file_location(name, path)
 module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
 return module

def main(version):
 out = BASE / version; need(not out.exists(), 'Fresh independent MFC static gate')
 pins = {}
 def pin(path, expected=None):
  path = Path(path).resolve(); digest = sha(path)
  need(expected is None or expected == digest, 'Exact physical MFC dependency ' + str(path))
  pins[str(path)] = digest; return path
 receipts = {p: json.loads(pin(ROOT / p, h).read_bytes()) for p, h in RECEIPTS.items()}
 accepted = receipts['reports/m4-joint-startup71-root/acceptance-r1/report.json']
 need(accepted['passed'] and accepted['connected_roots'] == 71, 'Accepted connected71 parent')
 lifts = receipts['reports/m4-mfc-native/lifts-r1/report.json']
 loader = receipts['reports/m4-mfc-source/loader-identity-r1/report.json']
 need(lifts['passed'] and not lifts['native_executed'], 'Bounded non-executed native literal lift input')
 need(loader['passed'] and loader['original_loader_executed'] and not loader['allocator_source_called'] and not loader['free_source_called'], 'Actual loader evidence without constructor execution credit')
 pin(loader['observation'], loader['observation_sha256'])
 PE = load('mfc_independent_PE', pin(ROOT / 'tools/analysis/pe.py'))
 parser = load('mfc_independent_operand_parser', pin(ROOT / 'tools/m4-crt-locale-batch-recovery/recover_v2.py'))
 mfc_data = pin(ROOT / 'local/mw3-staged/Shared_DLLs/MFC42.DLL', MFC_SHA).read_bytes()
 crt_data = pin(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL', CRT_SHA).read_bytes()
 game_data = pin(ROOT / 'MW3/Mech3.exe', GAME_SHA).read_bytes()
 mfc = PE.PEImage(mfc_data); crt = PE.PEImage(crt_data); game = PE.PEImage(game_data)
 def physical(pe, data, address, size):
  offset, _ = pe.rva_range(address - pe.image_base, size)
  return data[offset:offset+size]
 local = json.loads(pin(ROOT / 'reports/m4-strings-native/next-mfc-r1/provider-local.json', '67b6e3f0402a2c148b00ed4ab120578f2dd59940b864e67c8046cef582bea9fd').read_bytes())
 all_rows = {}; admitted = {}; bodies = []
 for key, ordinal, entry, limit in (('ordinal823', 823, 0x5f401ea0, 0x5f401ec9), ('ordinal825', 825, 0x5f401782, 0x5f40178e)):
  graph = local[key]; need(graph['entry'] == entry and not graph['FS_sites'] and not graph['FP_sites'], 'Exact non-FP local provider roots')
  export = next(e for e in mfc.exports() if e['ordinal'] == ordinal)
  need(mfc.image_base + export['rva'] == entry, 'Actual physical MFC ordinal export')
  for row in graph['instructions']:
   raw = bytes.fromhex(row['bytes'])
   need(len(raw) == row['size'] and physical(mfc, mfc_data, row['pc'], len(raw)) == raw, 'Exact original MFC instruction ' + hex(row['pc']))
   contract = parser.instruction_contract(dict(pc=row['pc'], width=row['size'], bytes_hex=row['bytes'], mnemonic=row['mnemonic'], operands=row['operands'].split(' <')[0].strip()))
   need(row['pc'] not in all_rows, 'Unique original provider PC'); all_rows[row['pc']] = contract
   if entry <= row['pc'] < limit: admitted[row['pc']] = contract
  rows = [admitted[pc] for pc in sorted(admitted) if entry <= pc < limit]
  need(b''.join(bytes.fromhex(r['bytes_hex']) for r in rows) == physical(mfc, mfc_data, entry, limit-entry), 'Complete contiguous admitted physical body')
  bodies.append(dict(ordinal=ordinal, entry=entry, end_exclusive=limit, original_rows=len(rows), physical_bytes=limit-entry, bytes_hex=physical(mfc,mfc_data,entry,limit-entry).hex(), physical_bytes_sha256=hashlib.sha256(physical(mfc,mfc_data,entry,limit-entry)).hexdigest()))
 need(len(all_rows) == 37 and len(admitted) == 23, '33 local allocation plus four free rows, only 19 positive allocation rows admitted')
 native = json.loads(pin(ROOT / 'reports/m4-mfc-native/lifts-r1/instruction-contracts.json', lifts['instruction_contracts_sha256']).read_bytes())
 need({r['pc']:r for r in native['instructions']} == admitted, 'Independent original operands match native literal input')
 callback_data = json.loads(pin(ROOT / 'reports/m4-mfc-native/lifts-r1/callbacks.json', lifts['callbacks_sha256']).read_bytes())
 callbacks = callback_data['State_offsets_by_original_PC']
 need(callbacks == {str(0x5f401eba): [2069]}, 'Exact undefined AF at literal TEST EDI,EDI only')
 bindings = []
 for name, slot, raw, target, pc in (('malloc',0x5f49814c,0x78001498,0x780012b3,0x5f401ea1), ('free',0x5f498148,0x7800138a,0x78001390,0x5f401786)):
  fact = next(r for r in loader['bindings'] if r['name'] == name)
  export = next(e for e in crt.exports() if name in e['names'])
  need(struct.unpack('<I',physical(mfc,mfc_data,slot,4))[0] == raw and crt.image_base+export['rva'] == target, 'Named physical import and export retain different raw bound address')
  need(fact['MFC_IAT_slot'] == slot and fact['raw_bound_IAT'] == raw and fact['actual_loader_target'] == target and fact['actual_owner_named_export'] == target and fact['actual_owner_base'] == crt.image_base and fact['owning_module_sha256'] == CRT_SHA, 'Actual original32 named target owner')
  need(physical(crt,crt_data,target,32).hex() == fact['target_first32_hex'] and fact['original_named_export'] == export, 'Actual loaded code bytes and exact physical named export')
  need(Path(fact['actual_owner_path']).resolve() == (ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').resolve(), 'Exact staged actual loader owner path')
  bindings.append(dict(name=name, read_PC=pc, source_IAT=slot, physical_raw=raw, actual_loader_target=target, delivered_source_target=target, preserve_raw_memory=True, preserve_raw_source_access=True, source_projection_only=True, original_loader_receipt_sha256=RECEIPTS['reports/m4-mfc-source/loader-identity-r1/report.json']))
 handler = struct.unpack('<I',physical(mfc,mfc_data,0x5f498970,4))[0]
 need(handler == 0xffffffff and loader['MFC_handler']['post_loader_value'] == handler, 'Literal and genuine loaded handler read agree')
 need(loader['MFC_allocator_export823']==0x5f401ea0 and loader['MFC_free_export825']==0x5f401782 and loader['MFC_base']==mfc.image_base, 'Loaded physical ordinal ownership')
 game_import = local['game_IAT']; need(game_import == dict(slot=0x5bb4bc, raw_bound=0x80000337, ordinal=823, target=0x5f401ea0), 'Exact game ordinal823 relocation domain')
 need(struct.unpack('<I',physical(game,game_data,0x5bb4bc,4))[0] == 0x80000337, 'Retained actual game raw ordinal IAT bytes')
 abi = dict(allocator=dict(entry=0x5f401ea0, entry_frame='F', request_address='F+4', malloc_call_PC=0x5f401eb5, malloc_frame='F-24', malloc_argument_address='F-20', malloc_return=0x5f401eb7, argument_pop_PC=0x5f401eb9, allocator_RET=0x5f401ec8, final_SP='F+4', restored_nonvolatiles=['ebx','ebp','esi','edi'], final_ECX='request', original_request_not_popped=True), free=dict(entry=0x5f401782, entry_frame='F', argument_address='F+4', CRTfree_call_PC=0x5f401786, CRTfree_frame='F-8', CRTfree_argument_address='F-4', CRTfree_return=0x5f40178c, argument_pop_PC=0x5f40178c, free_RET=0x5f40178d, final_SP='F+4', final_ECX='freed_guest_alias', original_argument_not_popped=True))
 out.mkdir(parents=True)
 interface = dict(schema='mw34-mfc-independent-provider-interface-v1', instructions=[admitted[pc] for pc in sorted(admitted)], callbacks_by_original_PC=callbacks, bodies=bodies, source_import_projections=bindings, game_ordinal_projection=game_import, handler_read=dict(PC=0x5f401ead,address=0x5f498970,physical_raw=handler,actual_post_loader=handler), ABI=abi, refused_frontiers=[dict(PC=0x5f41b01e,reason='Actual null allocator branch requires unresolved handler/TLS source closure'),dict(PC=0x5f4010fd,reason='Unadmitted TLS context retrieval'),dict(PC=0x5f41b02f,reason='Unadmitted handler CALL ESI')], AFTER_machine_seed=False)
 path=out/'instruction-contracts.json'; path.write_text(json.dumps(interface,indent=2)+'\n'); pin(path)
 provenance=out/'local-provenance.json'; provenance.write_text(json.dumps(dict(instructions=[all_rows[pc] for pc in sorted(all_rows)],admitted_PCs=sorted(admitted),cold_PCs=sorted(set(all_rows)-set(admitted))),indent=2)+'\n'); pin(provenance)
 pin(__file__); pin(ROOT/'tools/m4-mfc-review/provider_model.py')
 report=dict(passed=True,schema='mw34-mfc-independent-static-gate-v1',scope='Physical original operand/byte/export/loader identity and cdecl frame review; no constructor or native execution',new_original_instructions=23,new_literal_bytes=53,local_provenance_instructions=37,local_provenance_bytes=sum(r['width']for r in all_rows.values()),positive_allocator_instructions=19,free_instructions=4,family_roots=32,actual_loader_named_bindings=2,raw_bound_values_retained=True,null_allocator_failure_path_admitted=False,handler_TLS_path_admitted=False,source_import_projection=True,instruction_contracts=str(path),instruction_contracts_sha256=sha(path),files=pins,AFTER_machine_seed=False,native_executed=False,original_constructor_executed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),interface_sha256=sha(path))))
if __name__=='__main__': main(sys.argv[1])
