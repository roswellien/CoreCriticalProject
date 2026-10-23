"""Ordinary current native37 constructor literal CPU/State/FX/pages/owners gate."""
from pathlib import Path
import json,hashlib,importlib.util,struct,sys,traceback
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={};passed=False;f=None;cases=[];stage={}
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(R/p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def need(v,m):
  if not v:raise ValueError(m)
 def write(p,v):
  p.write_text(json.dumps(v,indent=2,default=lambda v:v.hex()if isinstance(v,(bytes,bytearray))else (_ for _ in()).throw(TypeError(type(v).__name__)))+'\n');pin(p)
 try:
  receipt=json.loads(pin(R/'reports/m4-138-validation-review/constructor37-raw-export-r1/report.json','2d5039d9ec0e4ae118a10c031f367bef3f97f78175bb0e57b3dbb2f813e582a1').read_bytes());need(receipt['passed']and receipt['reader_closed'],'Current closed native37 ordinary export')
  E=load('tools/m4-joint-startup131/paired_exports.py','ex');A=load('tools/m4-138-validation-review/constructor_native_input_v7.py','input');D=load('tools/m4-constructor-native/derive_source_v8.py','derive');preparation=pin(R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json','26b896f0523439030cbdd6cf4bd98cfadfbb9b15451bf80950600c37db892e6e')
  for export in receipt['paired_exports']:
   level=export['branch'];f=E.Facade(export,pin);table=f.words('selected-table.bin',37)
   for seq in range(6):
    for root in(0x4103f0,0x410440,0x459b40):
     stage=dict(branch=level,sequence=seq,root=root,operation='own BEFORE');case=out/f'{level}-{seq}-{root}';case.mkdir();inp=A.build(f,level,seq,root);write(case/'input.json',inp)
     stage['operation']='literal execution';result=D.derive(inp,preparation);write(case/'source-derivation.json',result)
     # Equality targets are opened only after source computation terminates.
     stage['operation']='whole endpoint equality';phase=table.index(root);stem=f'sequence-{seq}/';raw=f.data(stem+f'phase-{phase}.bin');after=stem+f'Constructors/root-{root}/after/'
     target=dict(CPU=list(struct.unpack_from('<10I',raw,76)),State_hex=f.data(after+'State.bin').hex(),FX_hex=f.data(after+'FX.bin').hex())
     for key,value in target.items():need(result['source_computed_'+key]==value,'Entire native source '+key)
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
     owner_count=0
     for address,observed in memory.items():
      computed=bytes.fromhex(result['source_computed_memory'][str(address)]);need(computed[:len(observed)]==observed,'Every whole current source/stack/owner endpoint '+hex(address));owner_count+=0x31000000<=address<0x32000000
     target['regions']=[dict(address=a,bytes=len(b),hex=b.hex())for a,b in sorted(memory.items())];write(case/'endpoint.json',target)
     access_before=f.data(stem+f'Constructors/root-{root}/before/accesses.bin');access_after=f.data(after+'accesses.bin');need(access_after.startswith(access_before),'Whole cumulative constructor source prefix');wanted=list(struct.iter_unpack('<IIQII',access_after[len(access_before):]));borrowed=[tuple(v)for v in result['accesses']if v[0]in(0x5abd1a,0x5abd26)];call_before=f.data(stem+f'Constructors/root-{root}/before/calls.bin');call_after=f.data(after+'calls.bin');need(call_after.startswith(call_before),'Exact cumulative borrowed MFC call prefix');calls=list(struct.iter_unpack('<12I',call_after[len(call_before):]));need(borrowed==[(v[2],0x5bb4bc if v[2]==0x5abd26 else 0x5bb4c8,0x80000337 if v[2]==0x5abd26 else 0x80000339,4,0)for v in calls],'Every separately executed literal trampoline IAT read joins one actual authenticated native borrowed source CALL');projections=list(struct.iter_unpack('<8I',f.data(stem+'selected/locale-research-projections.bin')));relations=[v for v in projections if v[0]==11 and v[1]==root];need(relations==[(11,root,v[1],v[2],0x5bb4bc if v[2]==0x5abd26 else 0x5bb4c8,0x80000337 if v[2]==0x5abd26 else 0x80000339,v[3],v[4])for v in calls],'Every current borrowed source CALL has exact actual ordinal/IAT/frame projection');computed=[tuple(v)for v in result['accesses']if 0x400000<=v[0]<0x9f5000 and v[0]not in(0x5abd1a,0x5abd26)];need(computed==wanted,'Every physical game constructor component operand in actual source order; typed borrowed trampolines joined separately')
     cases.append(dict(branch=level,sequence=seq,root=root,whole_State=True,whole_CPU=True,whole_FX=True,entire_endpoint_regions=len(memory),whole_owner_backings=owner_count,game_source_operands=len(wanted),source_API_facts=len(inp['APIs']),source_COMPLETE=True));print(json.dumps(cases[-1]),flush=True)
   f.close();f=None
  need(len(cases)==36,'Both native levels/all6CW-TOP domains/all3constructors');passed=True
 except BaseException:write(out/'frontier.json',stage);(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if f is not None:f.close()
  pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Current native37 finite36 literal constructor equality; original18 and paired/refusal/full141 chronology separate. Own previous-checkpoint nonphase region carry physical review and first-FS-read initial-field policy remain explicit dependencies.',cases=cases,frontier=stage,source_AFTER_seed=False,canonical_reader_opened=False,ordinary_reader_closed=True,original_cases=0,initializer_credit=0,input_carry_policy_review_pending=True,files=pins),indent=2)+'\n');print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])
