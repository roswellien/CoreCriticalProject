"""Independently bind new string instructions to physical original DLL bytes."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-strings-review'
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
LIFTS_SHA='4cfb5495ea88f9abef2f0a891f8b85aac33f32c6cc75b739ba418e402866a13e'
SOURCE_SHA='972ec961d7617d2e7b789d23ab1ce82da0c33424b37c12e2dc94c23d1e154341'
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh independent string interface');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Physical string source dependency '+str(p));pins[str(p)]=v;return p
 acceptance=pin(ROOT/'reports/m4-joint-startup54-root/acceptance-r1/report.json','5a7feb121fd1a8fc95d4e31da18af67099e91012b3f70e36e17575973b4cd89c');need(json.loads(acceptance.read_bytes())['connected_roots']==54,'Frozen accepted54 prerequisite')
 family=json.loads(pin(ROOT/'reports/m4-onexit-native/next-family-r2/report.json','2ad1d8ce2a7b7db6a108e1775def2eb1c89d6ab4e1803b7421c01feb23fc64c0').read_bytes());need(family['recommended']['count']==17,'Exact requested static17 family')
 lifts=json.loads(pin(ROOT/'reports/m4-strings-native/lifts-r1/report.json',LIFTS_SHA).read_bytes());need(lifts['passed']and not lifts['native_executed'],'Source-only literal lift receipt')
 source=json.loads(pin(ROOT/'reports/m4-strings-source/recovery-r7/report.json',SOURCE_SHA).read_bytes());need(source['passed'],'Frozen exact17 game/string source recovery')
 parser=load('independent_strings_operand_parser',pin(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py'))
 PE=load('independent_strings_PE',pin(ROOT/'tools/analysis/pe.py'))
 crt=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',PROVIDER_SHA).read_bytes();pe=PE.PEImage(crt)
 graphs=json.loads(pin(ROOT/'reports/m4-service-initializers/static-r1/MSVCRT.DLL.provider.json','2e7e0fdbf9b673aacc7da13ab1802e44db816db5b1a3d1ec50e2b59bcc12d4f5').read_bytes())['graphs']
 instructions={};bodies=[]
 for entry,name_ in((0x78010a6d,'_strdup'),(0x78002f32,'strlen'),(0x78002fab,'strcpy')):
  graph=graphs[str(entry)];need(not graph['FS_sites']and not graph['FP_sites']and not graph['unresolved_controls'],'Three bounded locally closed integer bodies')
  rows=[]
  for row in graph['instructions']:
   code=bytes.fromhex(row['bytes']);offset,_=pe.rva_range(row['pc']-pe.image_base,len(code));need(crt[offset:offset+len(code)]==code and len(code)==row['size'],'Exact original string instruction bytes')
   parsed=parser.instruction_contract(dict(pc=row['pc'],width=row['size'],bytes_hex=row['bytes'],mnemonic=row['mnemonic'],operands=row['operands'].split(' <')[0].strip()))
   need(row['pc']not in instructions or instructions[row['pc']]==parsed,'One literal instruction contract per originalPC');instructions[row['pc']]=parsed;rows.append(row['pc'])
  export=next(e for e in pe.exports()if name_ in e['names']);need(pe.image_base+export['rva']==entry,'Exact original named export/RVA')
  bodies.append(dict(name=name_,entry=entry,ordinal=export['ordinal'],rva=export['rva'],instructions=len(rows),original_PCs=rows))
 native_path=pin(ROOT/'reports/m4-strings-native/lifts-r1/instruction-contracts.json',lifts['instruction_contracts_sha256']);native=json.loads(native_path.read_bytes());need({r['pc']:r for r in native['instructions']}==instructions,'Independent original contracts exactly match changed native lift input')
 callback_path=pin(ROOT/'reports/m4-strings-native/lifts-r1/callbacks.json',lifts['callbacks_sha256']);callbacks=json.loads(callback_path.read_bytes())['State_offsets_by_original_PC'];expected={str(pc):[2069]for pc,r in instructions.items()if r['mnemonic']in('test','xor')};need(callbacks==expected,'Every undefinedAF callback is at its exact original logical instruction, no entry heuristic')
 game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();gp=PE.PEImage(game)
 def game_bytes(address,n):
  result=bytearray(n)
  for sec in gp.sections:
   start=gp.image_base+sec['virtual_address'];end=start+sec['virtual_size'];lo=max(address,start);hi=min(address+n,end)
   if hi<=lo:continue
   raw_hi=min(hi,start+sec['raw_size'])
   if raw_hi>lo:off=sec['raw_offset']+lo-start;result[lo-address:raw_hi-address]=game[off:off+raw_hi-lo]
  return bytes(result)
 inputs_path=pin(ROOT/'reports/m4-strings-source/recovery-r7/string-inputs.json');inputs=json.loads(inputs_path.read_bytes());need(len(inputs)==17 and sum(r['actual_strdup_called']for r in inputs)==16,'Exactly17 roots with16 actual nonnull string call domains')
 for record in inputs:
  if not record['actual_strdup_called']:
   need(record['root']==0x4e6a10 and record['source']==0 and record['size']==0 and record['source_descriptor']==0x60b868 and record['descriptor_bytes_hex']=='0000000000000000' and game_bytes(0x60b868,8)==bytes(8),'Exact source-null descriptor, not empty string argument')
   continue
  data=bytes.fromhex(record['bytes_hex']);physical=bytes.fromhex(record['physical_bytes_hex']);address=record['source'];need(address and record['size']==len(data)and data[-1:]==b'\0'and b'\0'not in data[:-1],'Bounded nonnull original NUL extent')
  need(record['nul_address']==address+len(data)-1 and record['physical_read_end']==(record['nul_address']+4)&~3 and address%4==record['alignment_prefix']==0,'Actual family alignedDWORD read domain includes bytes after NUL')
  need(len(physical)==record['physical_read_end']-address and game_bytes(address,len(physical))==physical and physical[:len(data)]==data,'Full physical original input/padding/BSS bytes independently bound')
 # Independently execute the exact physical integer constructor path up to
 # the later callback registration; no captured AFTER page is a model input.
 game_contracts=json.loads(pin(ROOT/'reports/m4-strings-source/recovery-r7/instruction-contracts.json').read_bytes())
 null_program={r['pc']:r for r in game_contracts['instructions']}
 P=load('null_constructor_independent',pin(ROOT/'tools/m4-onexit-review/provider_model.py'))
 null_pcs={0x4e6a10,0x4e6a15,0x4e6a20,0x4e6a25,0x4e6a2a,0x4e6a2f,0x4e6a60,0x4e6a61,0x4e6a62,0x4e6a66,0x4e6a68,0x4e6a6a,0x4e6a6b,0x4e6a70,0x4e6a73,0x4e6a7a,0x4e6a7d,0x4e6a7f,0x4e6a80,0x4e6a81,0x49d1c0,0x49d1c4,0x49d1c5,0x49d1c7,0x49d1c9,0x49d1cf,0x49d1dd,0x49d1df,0x49d1e0}
 for pc in null_pcs:
  r=null_program[pc];need(game_bytes(pc,r['width'])==bytes.fromhex(r['bytes_hex']),'Exact source-null constructor physical instruction '+hex(pc))
 state=bytearray(3504);struct.pack_into('<I',state,P.I.REG['esp'],0x20001800);struct.pack_into('<I',state,2472,0x4e6a10)
 null_machine=P.Machine(state,bytes(512),bytes(40),{0x20001000:bytes(4096),0x60b000:game_bytes(0x60b000,4096)},program=null_program,callbacks={});null_machine.cursor=0x4e6a10
 while null_machine.cursor!=0x4e6a30:
  need(len(null_machine.PCs)<100,'Finite exact null constructor path');null_machine.step()
 need(0x49d1cf in null_machine.PCs and not any(pc in null_machine.PCs for pc in(0x49d1d1,0x49d1d2,0x78010a6d))and null_machine.bytes(0x60b800,12)==bytes(12),'Literal descriptor load/null constructor branch causes no strdup or owned string')
 null_derivation=dict(entry=0x4e6a10,descriptor=0x60b868,descriptor_bytes=game_bytes(0x60b868,8).hex(),source_pointer=0,source_load_PC=0x4e6a68,branch_PC=0x49d1cf,stopped_before_registration=0x4e6a30,executed_original_PCs=null_machine.PCs,computed_object_bytes=null_machine.bytes(0x60b800,12).hex(),strdup_called=False,AFTER_seed=False)
 (out/'null-constructor-derivation.json').write_text(json.dumps(null_derivation,indent=2)+'\n');pin(out/'null-constructor-derivation.json')
 old_path=pin(ROOT/'reports/m4-onexit-review/interface-r1/instruction-contracts.json','9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d');old={r['pc']:r for r in json.loads(old_path.read_bytes())['instructions']};need(not(set(instructions)&set(old)),'117 changed string instructions add without replacing accepted1404 provider instructions')
 pin(__file__);pin(ROOT/'tools/m4-strings-review/provider_model.py');pin(ROOT/'tools/m4-onexit-review/provider_model.py');pin(ROOT/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py')
 interface=dict(schema='mw34-strings-independent-provider-interface-v1',instructions=[instructions[pc]for pc in sorted(instructions)],bodies=bodies,callbacks_by_original_PC=callbacks,inputs=inputs,accepted_provider_interface=str(old_path),accepted_provider_interface_sha256=sha(old_path),AFTER_machine_seed=False)
 path=out/'instruction-contracts.json';path.write_text(json.dumps(interface,indent=2)+'\n');pin(path)
 report=dict(passed=True,scope='Independent static original-byte/export/operand/callback and fixed string-input audit only',new_original_instructions=len(instructions),new_literal_bytes=sum(r['width']for r in instructions.values()),exact_original_exports=len(bodies),family_roots=len(inputs),actual_nonnull_string_inputs=16,null_constructor_paths=1,input_classification_supersedes=str(BASE/'interface-r1/report.json'),all_measured_input_pointers_aligned=True,bytes_beyond_NUL_retained=True,source_null_input_admitted=False,actual_malloc_failure_admitted=False,unhandled_FS_TLS_paths_admitted=False,instruction_contracts=str(path),instruction_contracts_sha256=sha(path),files=pins,native_executed=False,original_executed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),interface_sha256=sha(path),new_rows=len(instructions))))
if __name__=='__main__':main(sys.argv[1])
