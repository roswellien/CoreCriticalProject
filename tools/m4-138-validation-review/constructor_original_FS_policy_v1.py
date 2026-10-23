"""Finite original normal FS operand and immutable same-thread identity proof."""
from pathlib import Path
import hashlib,json,importlib.util,struct,sys,re,traceback
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={};passed=False;a=None;records=[];identity=[];inventory=[];asm=[];segment_writes=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(R/p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  V=json.loads(pin(R/'reports/m4-constructor-original/chronological-validation-r3/report.json','00f22911cff2ebde706df7eac235d1621127cb6bd670fd9d680c8478f19b0b95').read_bytes());assert V['passed']and V['reader_closed'];preflight=json.loads(pin(V['preflight_path'],V['preflight_sha256']).read_bytes());assert preflight['passed'];build=json.loads(pin(V['build_path'],V['build_sha256']).read_bytes());assert build['passed']
  E=load('tools/m4-joint-startup131/paired_exports.py','ex');M=load('tools/m4-constructor-native/game_model_v5.py','model');program,_=M.source_program(pin(R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json'));a=E.Facade(V['paired_exports'][0],pin)
  for pc,row in sorted(program.items()):
   op=row['mnemonic'].lower();operands=row.get('operands','').lower()
   if re.match(r'^(?:fs|gs|ds|es|ss|cs)\s*(?:,|$)',operands)and op not in('push','cmp','test')or op in('lfs','lgs','lds','les','lss','retf','iret','iretd'):segment_writes.append(dict(pc=pc,op=op,operands=operands))
   if 'fs:'in operands:inventory.append(dict(pc=pc,op=op,operands=operands,bytes_hex=row['bytes_hex'],decoded_operands=row['decoded_operands']))
  assert not segment_writes
  prep=R/'reports/m4-constructor-original/chronological-preparation-r10'
  for p in prep.glob('*.asm'):
   text=pin(p).read_text();writes=[line for line in text.splitlines()if re.search(r'(?i)\b(?:mov|pop|lfs|lgs|lds|les|lss)\s+(?:fs|gs|ds|es|ss|cs)\s*(?:,|$)',line.split(';')[0])];assert not writes;asm.append(dict(path=str(p),segment_selector_writes=writes))
  cpp=pin(prep/'reference.cpp').read_text();assert 'unsigned sequence{};'in cpp and 'for(const auto& test:cases)'in cpp and 'r->tag.status=execute();fs_phase_root=0;'in cpp;assert 'GetCurrentThreadId()'in cpp;assert not any(v in cpp for v in('CreateThread(','SetThreadContext(','SwitchToFiber(','ConvertThreadToFiber('))
  for path in preflight['files']:
   q=Path(path)
   if q.name in [v.name for v in prep.glob('*.asm')]+['reference.cpp']and q.is_relative_to(prep):pin(q,preflight['files'][path])
  for seq in range(6):
   # Scalar process/thread identity is distinct from future TEB bytes. No TEB page opened.
   domain=a.words(f'phase/{seq}/15/MFC1168/BEFORE/domain/domain.bin',10);teb=a.words(f'phase/{seq}/15/MFC1168/BEFORE/domain/TEB/metadata.bin',8);assert domain[0]==teb[0]and domain[1]and domain[0]%4096==0;identity.append((domain[0],domain[1]))
   for phase,root in((13,0x4103f0),(14,0x410440),(36,0x459b40)):
    key=f'phase/{seq}/{phase}/fs-events.bin';raw=a.data(key);assert len(raw)%1216==0 and raw;first=raw[:1216];w=struct.unpack_from('<8I',first);before=struct.unpack_from('<10I',first,32);after=struct.unpack_from('<10I',first,72);row=program[w[2]];assert w[:2]==(1,root)and w[3]==0 and w[4]==w[5]and row['mnemonic']=='mov'and 'fs:[0x0]'in row['operands'];assert before[9]==w[2]and after[0]==w[4];scopes=[]
    for i in range(len(raw)//1216):
     b=raw[i*1216:(i+1)*1216];v=struct.unpack_from('<8I',b);assert v[:2]==(1,root)and v[2]in program
     if v[3]==1:
      assert v[7]==1 and 0x20001000<=v[6]and v[6]+12<=0x20002000 and struct.unpack_from('<I',b,112)[0]==v[4];scopes.append(dict(source_PC=v[2],frame=v[6],predecessor=v[4],whole_raw12_before_hex=b[112:124].hex(),whole_raw12_after_hex=b[124:136].hex()))
    records.append(dict(sequence=seq,phase=phase,root=root,FS_base_identity=domain[0],identity_thread_id=domain[1],FS_head_observed=w[4],first_physical_FS_read_PC=w[2],first_physical_FS_read_bytes=row['bytes_hex'],first_FS_event_raw_sha256=hashlib.sha256(first).hexdigest(),first_FS_event_head_raw4_hex=struct.pack('<I',w[4]).hex(),root_FS_base_directly_observed=False,identity_observation_phase=15,identity_not_future_page_seed=True,FS_head_not_from_future_TEB=True,normal_live_raw12_installations=scopes,FS_events=len(raw)//1216,whole_TIB_claim=False,original_State_observed=False))
  assert len(set(identity))==1;passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if a is not None:a.close()
  pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Actual original first normal FS-before DWORD/physical operand/live12B stack records and immutable same-thread identity; direct root segment-base observations absent. Independent input policy required; no future TEB page data read.',cases=records,physical_FS_operand_inventory=inventory,source_segment_selector_write_inventory=segment_writes,observer_asm_inventory=asm,six_same_worker_identity_tuples=identity,canonical_reader_opened=False,ordinary_reader_closed=True,whole_TIB_claim=False,whole_original_State_claim=False,source_AFTER_seed=False,input_policy_acceptance=False,initializer_credit=0,files=pins),indent=2)+'\n');print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])
