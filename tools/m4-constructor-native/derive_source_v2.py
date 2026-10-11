"""Pure constructor source derivation, original/native architecture distinct."""
from pathlib import Path
import copy,importlib.util,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('constructor_source_exact_v2',R/'tools/m4-constructor-native/game_model_v2.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
def derive(domain,preparation):
 I=M.I;I.need(set(('branch','root','BEFORE_CPU_hex','BEFORE_FX_hex','BEFORE_memory','owners','APIs'))<=set(domain),'Explicit complete own-BEFORE source inputs')
 I.need(domain['branch']in('original','O0','O2')and domain['root']in M.ROOTS,'Current source branch/root')
 state=M.from_original_before(domain)if domain['branch']=='original'else bytes.fromhex(domain['BEFORE_State_hex'])
 cpu=bytes.fromhex(domain['BEFORE_CPU_hex']);fx=bytes.fromhex(domain['BEFORE_FX_hex']);I.need((len(state),len(cpu),len(fx))==(3504,40,512),'Whole own BEFORE architecture')
 memory={int(a):bytes.fromhex(b)for a,b in domain['BEFORE_memory'].items()};program,callbacks=M.source_program(preparation)
 imports={(f['PC'],f['address']):dict(raw=f['raw'],target=f['target'],owning_named_input=f['owning_named_input'])for f in domain.get('imports',[])}
 I.need(len(imports)==len(domain.get('imports',[])),'Distinct source owning import sites')
 m=M.Machine(state,fx,cpu,memory,program=program,callbacks=callbacks,owner_roles=domain['owners'],source_imports=imports)
 frame=m.reg('esp');ret=int.from_bytes(m.bytes(frame,4),'little');I.need(m.cursor==domain['root']and frame==0x20001800 and tuple(m.projected_cpu())==struct.unpack('<10I',cpu),'Actual committed source entry and frame')
 m.call_stack.append((domain['root'],frame,ret,0,m.reg('ebp'),m.reg('ebx'),m.reg('esi'),m.reg('edi'),0));m.begin_constructor(domain['root']);response=M.ActualAPIs(domain['APIs']);m.run(lambda x:x.cursor==ret,api=response);response.complete();m.end_constructor()
 I.need(m.reg('esp')==frame+4 and not m.call_stack and m.fp_depth==0,'Complete literal constructor/provider/FS return')
 result=m.result();owners=[]
 for original in m.constructor_owners:
  owner=copy.deepcopy(original)
  if owner.get('live',True):
   raw=m.bytes(owner['guest'],owner['extent']);owner['source_final_hex']=raw.hex();I.need(raw[owner['requested']:]==bytes.fromhex(owner['initial_hex'])[owner['requested']:],'Every own unused allocation tail conserved')
  owners.append(owner)
 result.update(root=domain['root'],branch=domain['branch'],source_computed_CPU=list(m.projected_cpu()),source_computed_State_hex=bytes(m.state).hex(),original_State_equality_claim=False,source_computed_FX_hex=m.fx.hex(),source_computed_memory={str(a):bytes(b).hex()for a,b in m.memory.items()},source_complete_owners=owners,source_remaining_undefined_flags=dict(m.arch_undefined),source_API_inputs=response.index,source_AFTER_seed=False,per_phase_reseed=False,native_capacity_inferred=False)
 return result
