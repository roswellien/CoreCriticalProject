"""Ordinary current native37 constructor literal CPU/State/FX/pages/owners gate."""
from pathlib import Path
import json,hashlib,importlib.util,struct,sys,traceback
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2]
def main(admission_path,admission_sha,configuration_path,configuration_sha,owner_export_path,owner_export_sha,name):
 admission_path=Path(admission_path).resolve();assert hashlib.file_digest(admission_path.open('rb'),'sha256').hexdigest()==admission_sha;admission=json.loads(admission_path.read_bytes());assert admission['passed']is True and admission['independent_review']is True and admission['scope_identity']=='native141_constructor36_own_source'and admission['configuration_sha256']==configuration_sha
 admitted={}
 for p,h in admission['files'].items():
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';assert str(p)not in admitted and hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==h;admitted[str(p)]=h
 admitted[str(admission_path)]=admission_sha
 assert admission['owner_export_sha256']==owner_export_sha
 out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir();pins={};passed=False;f=None;owner_reader=None;cases=[];stage={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert p.is_relative_to(out.resolve())or admitted.get(str(p))==v;assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(R/p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def need(v,m):
  if not v:raise ValueError(m)
 def write(p,v):
  p.write_text(json.dumps(v,indent=2,default=lambda v:v.hex()if isinstance(v,(bytes,bytearray))else (_ for _ in()).throw(TypeError(type(v).__name__)))+'\n');pin(p)
 try:
  C=json.loads(pin(configuration_path,configuration_sha).read_bytes());need(C['schema']=='mw34-native141-constructor36-source-inputs-v1','Exact finite current own-source configuration');need(C['native_source']['sha256']=='8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3','Actual native source6 identity')
  receipt=json.loads(pin(C['native_source']['path'],C['native_source']['sha256']).read_bytes());need(receipt['passed']and receipt['reader_closed']and receipt['paired_export_readers_closed']and receipt['complete_persistent141_constructors']and receipt['per_phase_BEFORE_machine_seed']is False and receipt['candidate_AFTER_machine_seed']is False,'Actual fullcarried native141 proof; old original export excluded')
  source_rows=json.loads(pin(Path(C['native_source']['path']).parent/'Constructor-carried-source-derivations.json',receipt['files'][str((Path(C['native_source']['path']).parent/'Constructor-carried-source-derivations.json').resolve())]).read_bytes());need(len(source_rows)==36 and {(r['level'],r['sequence'],r['root'])for r in source_rows}=={(l,s,r)for l in('O0','O2')for s in range(6)for r in(0x4103f0,0x410440,0x459b40)},'Complete distinct actual current carried36 constructor rows')
  original=json.loads(pin(C['current_original18']['path'],C['current_original18']['sha256']).read_bytes());need(C['current_original18']['sha256']=='8f910be42c5be26bf6e41260361b61b3ec258aefedf2cbdaabe35e3992498899'and original['passed']and len(original['cases'])==18 and original['source_AFTER_seed']is False and original['canonical_reader_opened']is False,'Exact independent currently passed original18, not failed combined success')
  for dep,h in original['files'].items():pin(dep,h)
  def input_audit(event,args):
   if event!='open'or not args or not isinstance(args[0],(str,bytes)):return
   dep=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0;reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)
   if reading:
    if dep.suffix.lower()=='.pyc':raise PermissionError('No cached bytecode import; only ROOT-admitted physical source')
    need(dep.suffix.lower()not in('.mwb','.mwi','.zip')and dep.name!='transport.json','No archives through indirect source import')
    if dep.is_relative_to(R)or str(dep)in admitted:need(dep.is_relative_to(out.resolve())or str(dep)in admitted,'Every source import/descriptor/read preauthenticated')
  sys.addaudithook(input_audit)
  executed=receipt['executed_lineage'];build=json.loads(pin(executed['build'],executed['build_sha256']).read_bytes());joint_preparation=json.loads(pin(executed['joint_preparation'],executed['joint_preparation_sha256']).read_bytes());need(build['passed']and joint_preparation['passed']and build['preparation_sha256']==executed['joint_preparation_sha256'],'Exact current compiled native ENV producer lineage')
  projector_receipt=json.loads(pin(R/'reports/m4-startup141-paired/native-constructor-source-preparation-r4/projector-contract.json').read_bytes());need(projector_receipt['joint_preparation_sha256']==executed['joint_preparation_sha256']and projector_receipt['native_build_sha256']==executed['build_sha256'],'Physically reviewed same current protocol/remill layout')
  for dep,h in projector_receipt['files'].items():pin(dep,h)
  ENV=load('tools/m4-startup141-paired/native_ENV28_v1.py','current_native_State_ENV_projector')

  E=load('tools/m4-startup138-original/export_reader_r2.py','ex');A=load('tools/m4-startup141-paired/constructor_native_input141_v6.py','input');D=load('tools/m4-constructor-native/derive_source_v9.py','derive');preparation=pin(R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json','26b896f0523439030cbdd6cf4bd98cfadfbb9b15451bf80950600c37db892e6e')
  MD=load('tools/m4-startup141-paired/native_owner_metadata_v7.py','causal_current_native_owner_metadata');physical_contracts={int(k):v for k,v in json.loads(pin('D:\\Projects\\MW34Recomp\\reports\\m4-startup141-paired\\native-owner-metadata-preparation-r2\\physical-API-contracts.json').read_bytes()).items()}
  HF=load('tools/m4-startup141-paired/native_heap_field_cut_v1.py','finite_native_heap_field_cut')
  supplement=json.loads(pin(owner_export_path,owner_export_sha).read_bytes());need(supplement['passed']and supplement['reader_closed']and supplement['paired_export_readers_closed']and supplement['model_executed']is False and supplement['worker_launched']is False and supplement['source_sha256']==C['native_source']['sha256']and supplement['execution_sha256']=='536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6','Exact closed ROOT-admitted current owner-cut export, not source credit')
  need(len(supplement['cases'])==36 and {(v['level'],v['sequence'],v['root'])for v in supplement['cases']}=={(l,s,r)for l in('O0','O2')for s in range(6)for r in(0x4103f0,0x410440,0x459b40)},'Complete distinct current owner-cut36')
  for level in('O0','O2'):
   owner_reader=E.ExportReader(owner_export_path,owner_export_sha,level,pin)
   f=E.ExportReader(C['native_source']['path'],C['native_source']['sha256'],level,pin);f.words=lambda key,n,kind='I':struct.unpack('<'+kind*n,f.data(key));table=f.words('selected-table.bin',141)
   for seq in range(6):
    for root in(0x4103f0,0x410440,0x459b40):
     stage=dict(branch=level,sequence=seq,root=root,operation='own BEFORE');case=out/f'{level}-{seq}-{root}';case.mkdir();carried=next(r for r in source_rows if(r['level'],r['sequence'],r['root'])==(level,seq,root));cut=next(v for v in supplement['cases']if(v['level'],v['sequence'],v['root'])==(level,seq,root));need(cut['checkpoint_name']=='constructor-mfc-before'and cut['static_or_stack_checkpoint_bytes_seeded']is False,'Only typed own dynamic-owner input cut')
     owner_cut=dict(level=level,sequence=seq,root=root,checkpoint_prefix=cut['checkpoint_prefix'],checkpoint_name=owner_reader.data(cut['checkpoint_prefix']+'-name.bin').decode(),pages=[dict(address=int(k.rsplit('-page-',1)[1][:-4]),logical_key=k,bytes=owner_reader.entries[k]['bytes'],sha256=owner_reader.entries[k]['sha256'],hex=owner_reader.data(k).hex())for k in cut['keys']['owner_input']]);inp=A.build(f,level,seq,root,carried,owner_cut,MD,physical_contracts,HF);write(case/'input.json',inp)
     stage['operation']='literal execution';result=D.derive(inp,preparation)
     need(result['source_computed_memory'][str(0x78035000)]==inp['heap_initial_field_cut']['memory_hex']and not any(x[4]and x[1]<0x78035008 and x[1]+x[3]>0x78035000 for x in result['accesses']),'Exact sourcecomputed two DWORD conservation; no source write and no raw whole-page endpoint claim')
     program,_=D.M.source_program(preparation);need(all(not program[pc]['mnemonic'].startswith('f')for pc in result['PCs']),'Every reached literal instruction integer-only before endpoint opens')
     need(len(bytes.fromhex(inp['BEFORE_ENV28_hex']))==28 and len(inp['APIs'])==5 and all(len(bytes.fromhex(v['actual_API_before_FX512_hex']))==512 and v['actual_API_before_FX512_hex']==v['actual_API_after_FX512_hex']for v in inp['APIs']),'Complete actual all5 API FX conservation corroboration only; not an ENV equality theorem')
     need(ENV.project(bytes.fromhex(inp['BEFORE_State_hex'])).hex()==inp['BEFORE_ENV28_hex'],'Actual ownBEFORE28 equals physical deterministic native State projector')
     result['source_computed_ENV28_hex']=ENV.project(bytes.fromhex(result['source_computed_State_hex'])).hex();result['source_ENV_input_cut']='Entire literal SOURCE-computed State3504 projected by exact current native protocol, including metadata intentionally zeroed in observed FX6..23; hardware/original FNSTENV not inferred'

     write(case/'source-derivation.json',result)
     # Equality targets are opened only after source computation terminates.
     stage['operation']='whole endpoint equality';phase=table.index(root);stem=f'sequence-{seq}/';raw=f.data(stem+f'phase-{phase}.bin');after=stem+f'Constructors/root-{root}/after/'
     target=dict(CPU=list(struct.unpack_from('<10I',raw,76)),State_hex=f.data(after+'State.bin').hex(),FX_hex=f.data(after+'FX.bin').hex())
     for key,value in target.items():need(result['source_computed_'+key]==value,'Entire native source '+key)
     need(target['CPU']==carried['computed_after_CPU']and hashlib.sha256(bytes.fromhex(target['State_hex'])).hexdigest()==carried['computed_after_State_sha256']and hashlib.sha256(bytes.fromhex(target['FX_hex'])).hexdigest()==carried['computed_after_FX_sha256'],'Own complete endpoint independently joins fullcarried source6 result')
     need(result['source_computed_ENV28_hex']==raw[2192:2220].hex()and inp['BEFORE_ENV28_hex']==raw[2164:2192].hex(),'Entire own literal-derived ENV28 result equals actual endpoint; before field separately authenticated')
     need(result['accesses']==carried['whole_literal_source_accesses'],'Every current whole ordered component/provider/shared literal operand equals independently carried source6 journal')
     memory={v:raw[71908+i*4096:71908+(i+1)*4096]for i,v in enumerate(A.FIXED)}
     for key in f.entries:
      if key.startswith(stem+f'phase-{phase}-after-page-'):memory[int(key.rsplit('-',1)[1][:-4])]=f.data(key)
     memory[0x5f2000]=f.data(stem+f'phase-{phase}-after-constructor-global5F2000.bin')
     roots=(0x4103f0,0x410440,0x459b40);which=roots.index(root);ends=[];points=[]
     base=stem+'selected/'
     for key in f.entries:
      if key.startswith(base+'registry-checkpoint-')and key.endswith('-name.bin'):
       index=int(key[len(base+'registry-checkpoint-'):].split('-')[0]);name=f.data(key)
       if name==b'constructor-mfc-after':ends.append(index)
       if name==b'widget-onexit-after':points.append(index)
     end=min(v for v in points if v>sorted(ends)[(2,5,7)[which]]);prefix=base+f'registry-checkpoint-{end}'
     for key in f.entries:
      if key.startswith(prefix+'-page-'):
       address=int(key[len(prefix)+6:-4]);observed=f.data(key)
       if address not in memory:memory[address]=observed
     # Terminal owner bytes are opened only after literal execution and never
     # enter the BEFORE adapter or source response model.
     need(owner_reader.data(cut['endpoint_checkpoint_prefix']+'-name.bin')==b'widget-onexit-after','Exact current terminal registrar owner equality cut')
     for key in cut['keys']['endpoint']:
      address=int(key.rsplit('-page-',1)[1][:-4]);need(0x31000000<=address<0x32000000 and address not in memory,'Distinct current full terminal dynamic owner target');memory[address]=owner_reader.data(key)
     owner_count=0
     for address,observed in memory.items():
      computed=bytes.fromhex(result['source_computed_memory'][str(address)]);need(computed[:len(observed)]==observed,'Every whole current source/stack/owner endpoint '+hex(address));owner_count+=0x31000000<=address<0x32000000
     target['regions']=[dict(address=a,bytes=len(b),hex=b.hex())for a,b in sorted(memory.items())];write(case/'endpoint.json',target)
     access_before=f.data(stem+f'Constructors/root-{root}/before/accesses.bin');access_after=f.data(after+'accesses.bin');need(access_after.startswith(access_before),'Whole cumulative constructor source prefix');wanted=list(struct.iter_unpack('<IIQII',access_after[len(access_before):]));borrowed=[tuple(v)for v in result['accesses']if v[0]in(0x5abd1a,0x5abd26)];call_before=f.data(stem+f'Constructors/root-{root}/before/calls.bin');call_after=f.data(after+'calls.bin');need(call_after.startswith(call_before),'Exact cumulative borrowed MFC call prefix');calls=list(struct.iter_unpack('<12I',call_after[len(call_before):]));need(borrowed==[(v[2],0x5bb4bc if v[2]==0x5abd26 else 0x5bb4c8,0x80000337 if v[2]==0x5abd26 else 0x80000339,4,0)for v in calls],'Every separately executed literal trampoline IAT read joins one actual authenticated native borrowed source CALL');projections=list(struct.iter_unpack('<8I',f.data(stem+'selected/locale-research-projections.bin')));relations=[v for v in projections if v[0]==11 and v[1]==root];need(relations==[(11,root,v[1],v[2],0x5bb4bc if v[2]==0x5abd26 else 0x5bb4c8,0x80000337 if v[2]==0x5abd26 else 0x80000339,v[3],v[4])for v in calls],'Every current borrowed source CALL has exact actual ordinal/IAT/frame projection');computed=[tuple(v)for v in result['accesses']if 0x400000<=v[0]<0x9f5000 and v[0]not in(0x5abd1a,0x5abd26)];need(computed==wanted,'Every physical game constructor component operand in actual source order; typed borrowed trampolines joined separately')
     cases.append(dict(branch=level,sequence=seq,root=root,whole_State=True,whole_CPU=True,whole_FX=True,whole_own_CPU40=True,defined_EFLAGS=True,whole_own_State3504=True,whole_own_FX512=True,whole_own_ENV28=True,whole_own_pages_and_backings=True,source_ENV28_derived_from_BEFORE=True,source_ENV28_projected_from_entire_source_computed_State=True,actual_all5_API_FX_conserved=True,API_FX_implies_hardware_ENV_equality_claim=False,previous_checkpoint_nonphase_owner_carry_independently_proven=False,source_AFTER_seed=False,independent_current_fullcarry_join=True,whole_current_ordered_operand_joins=len(result['accesses']),entire_endpoint_regions=len(memory),whole_owner_backings=owner_count,game_source_operands=len(wanted),source_API_facts=len(inp['APIs']),source_COMPLETE=True));print(json.dumps(cases[-1]),flush=True)
   f.close();f=None;owner_reader.close();owner_reader=None
  need(len(cases)==36,'Both native levels/all6CW-TOP domains/all3constructors');passed=True
 except BaseException:write(out/'frontier.json',stage);(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if f is not None:f.close()
  if owner_reader is not None:owner_reader.close()
  pin(__file__);pin(admission_path,admission_sha);
  for dep,h in pins.items():need(hashlib.file_digest(Path(dep).open('rb'),'sha256').hexdigest()==h,'Final whole admitted current code/input/derived output conservation')
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Current native141 finite36 literal own constructor equality independently joined to actual fullcarried source6; original18 structural pairing and complete paired141 separate. Own previous-checkpoint nonphase region carry physical review and first-FS-read initial-field policy remain explicit dependencies.',configuration_sha256=configuration_sha,current_native_source_sha256=C['native_source']['sha256']if'C'in locals()else None,owner_export_sha256=owner_export_sha,current_original18_sha256=C['current_original18']['sha256']if'C'in locals()else None,cases=cases,frontier=stage,source_AFTER_seed=False,canonical_reader_opened=False,ordinary_reader_closed=True,original_cases=0,initializer_credit=0,input_carry_policy_review_pending=True,files=pins),indent=2)+'\n');print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(*sys.argv[1:])
