"""Additive physical malloc descriptors/callbacks; no archives or endpoints."""
from pathlib import Path
import ast, hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
O=R/'reports/m4-138-validation-review/constructor-allocator-literal-preparation-r1'
def need(v,m):
 if not v: raise ValueError(m)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
files={}
def pin(p,h=None):
 p=Path(p);v=sha(p);need(h is None or v==h,'Exact physical input '+str(p));files[str(p)]=v;return p
def put(p,d):
 need(not p.exists(),'Fresh immutable output '+str(p));p.write_bytes((json.dumps(d,indent=2,sort_keys=True)+'\n').encode());return pin(p)
need(not O.exists(),'Fresh preparation namespace')
rec=R/'reports/m4-crt-allocation-recovery/recovery-r1'
d=json.loads(pin(rec/'report.json','5ea56445e5367a421a28251f5e097b72f0d8370cf232a2fb4734b6698f14c2c6').read_bytes())
lift=R/'reports/m4-crt-allocation/lifts-r1';l=json.loads(pin(lift/'report.json').read_bytes());need(d['passed'] and l['passed'],'Existing physical recoveries passed')
decoder=load('constructor_literal_operand_decoder',pin(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py'))
cb=load('constructor_literal_callback_decoder',pin(R/'tools/m4-crt-locale-batch-recovery/callbacks.py'))
pe_module=load('constructor_malloc_physical_PE',pin(R/'tools/m4-crt/recover_provider.py'))
provider=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',d['provider_sha256']);pe=pe_module.PE(provider,d['provider_sha256'])
rows={}
for label in ('malloc-wrapper','malloc-size','malloc-worker-hot','malloc-round-mode1','malloc-null-cold'):
 sp=d['spans'][label];raw=pin(rec/(label+'.bin'),sp['sha256']).read_bytes()
 need(raw==pe.read(sp['start']-pe.base,len(raw)),'Whole physical provider span '+label)
 values=sp['instructions'];need(b''.join(bytes.fromhex(x['bytes_hex'])for x in values)==raw,'Contiguous recovered descriptors '+label)
 for x in values:
  row=decoder.instruction_contract(dict(x,width=len(bytes.fromhex(x['bytes_hex']))));need(row['pc']not in rows,'Distinct descriptor PC');rows[row['pc']]=row
callbacks={};maps={}
for name in ('malloc','size','worker','round','null','alloc_tail','worker_epilogue','size_ret'):
 b=l['source_bodies'][name];gp=pin(lift/(name+'-guest.ll'));hp=pin(lift/(name+'-host.ll'),b['host_sha256'])
 # The sealed guest is the pre-lowering trace here, unlike later optimized
 # locale traces. CFG propagation and callback destination recovery operate
 # on this same authentic guest trace; physical widths/joins are checked.
 body=cb.function(gp.read_text(),b['entry']);sites,mapping=cb.recover(body,body,b['entry'],rows)
 maps[name]=mapping
 for x in sites:
  pc=x['pc'];offsets=x['State_offsets'];need(pc not in callbacks or callbacks[pc]==offsets,'Overlapping callback order identical');callbacks[pc]=offsets
O.mkdir(parents=True)
rp=put(O/'instructions.json',dict(instructions=[rows[p]for p in sorted(rows)]));cp=put(O/'callbacks.json',dict(State_offsets_by_original_PC=callbacks,source_maps=maps))
parent=pin(R/'tools/m4-constructor-native/game_model_v2.py');derive=pin(R/'tools/m4-constructor-native/derive_source_v2.py')
model=R/'tools/m4-constructor-native/game_model_v3.py';need(not model.exists(),'Fresh additive model')
text='''"""Additive exact malloc source closure; inherited semantics unchanged."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('constructor_v2_frozen',R/'tools/m4-constructor-native/game_model_v2.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
I=P.I;G=P.G;ROOTS=P.ROOTS;BITS=P.BITS;ActualAPIs=P.ActualAPIs;Machine=P.Machine;from_original_before=P.from_original_before
def checked(p,h):
 raw=p.read_bytes();I.need(hashlib.sha256(raw).hexdigest()==h,'Pinned malloc physical literal descriptors');return json.loads(raw)
def source_program(preparation):
 program,callbacks=P.source_program(preparation)
 rows=checked(R/'reports/m4-138-validation-review/constructor-allocator-literal-preparation-r1/instructions.json','ROWSHA')['instructions']
 cb=checked(R/'reports/m4-138-validation-review/constructor-allocator-literal-preparation-r1/callbacks.json','CBSHA')['State_offsets_by_original_PC']
 for row in rows:
  pc=row['pc'];I.need(pc not in program or (program[pc]['width'],program[pc]['bytes_hex'],program[pc]['decoded_operands'])==(row['width'],row['bytes_hex'],row['decoded_operands']),'Exact shared literal row');program[pc]=row
 for pc,offsets in cb.items():
  pc=int(pc);offsets=tuple(offsets);I.need(pc not in callbacks or callbacks[pc]==offsets,'Exact shared undefined callback order');callbacks[pc]=offsets
 return program,callbacks
'''.replace('ROWSHA',sha(rp)).replace('CBSHA',sha(cp))
ast.parse(text);model.write_text(text);pin(model)
dp=R/'tools/m4-constructor-native/derive_source_v3.py';need(not dp.exists(),'Fresh derivation')
old=derive.read_text();new=old.replace('game_model_v2.py','game_model_v3.py').replace('constructor_source_exact_v2','constructor_source_exact_v3');need(new.replace('game_model_v3.py','game_model_v2.py').replace('constructor_source_exact_v3','constructor_source_exact_v2')==old,'Exact derivation inverse');ast.parse(new);dp.write_text(new);pin(dp)
m=load('malloc_model_preflight',model);prep=pin(R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json');program,callbacks=m.source_program(prep)
for pc in (0x780012f2,0x780012f9,0x78001367,0x7800136a):need(pc in program,'Genuine malloc FS source PC closure')
report=dict(passed=True,scope='Exact physical descriptor/callback merge and derivation inverse only',physical_rows=len(rows),program_rows=len(program),callback_sites=len(callbacks),new_callback_sites=len(json.loads(cp.read_bytes())['State_offsets_by_original_PC']),source_maps=maps,model=str(model),derivation=str(dp),inherited_semantics_unchanged=True,exact_derivation_inverse=True,finite_execution_controls_pending=True,input_adapter_pending=True,whole_source_comparison_pending=True,archive_reader_opened=False,source_AFTER_seed=False,native_executed=False,initializer_credit=0,files=files)
q=put(O/'report.json',report);print(json.dumps(dict(passed=True,report=str(q),sha256=sha(q))))
