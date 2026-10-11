"""Read-only audit of genuine original109 FS MOV observations and API owners."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fs-source'
GROUPS={0x4e78d7:dict(entry=0x4e78d0,install=0x4e78de,restore=0x4e799f,handler=0x5b986b,restore_delta=28,scope=0xffffffff,saved_load=0x4e7997),0x48f297:dict(entry=0x48f290,install=0x48f29e,restore=0x48f360,handler=0x5b5233,restore_delta=24,scope=1,saved_load=0x48f353),0x4d48f7:dict(entry=0x4d48f0,install=0x4d48fe,restore=0x4d4948,handler=0x5b8538,restore_delta=24,scope=0,saved_load=0x4d492a)}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh additive receipt');out.mkdir(parents=True);pins={};counts=collections.Counter();frames=[];owners=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Physical receipt identity '+str(p));pins[str(p)]=v;return p
 def module(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  pin(__file__);pin(BASE/'original-run-r2/report.json','a3b998395e1ed1e75a3fe50eb4fd60da822781bf85a82e368053561b816c3961');pin(BASE/'original-validation-r1/report.json','a419e9a7819ba38077621efdda6da5440c0f00042c6c492d7dc672ebeab632b4');pin(BASE/'observer-attribution-r1/report.json','9a12c0d4c8e6c77f5a7cf6388b9e6ad208fdb648cd16146343756698852269ff');pin(BASE/'original-preparation-r5/reference.cpp')
  contract=json.loads(pin(BASE/'recovery-r3/instruction-contracts.json').read_bytes());program={r['pc']:r for r in contract['instructions']};order=contract['selected_order'];bindings=json.loads(pin(BASE/'allocation-interface-r1/allocation-inputs.json','a3fb27e6f16c12bbc7499c912415b2c294d74e97c7600dbaeb3be4770ab492ff').read_bytes());need(len(bindings)==10,'Exact ten BEFORE-derived source allocation sites')
  pe_module=module(ROOT/'tools/analysis/pe.py','fs_observed_PE');game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=pe_module.PEImage(game)
  for row in program.values():
   off,_=pe.rva_range(row['pc']-0x400000,row['width']);need(game[off:off+row['width']]==bytes.fromhex(row['bytes_hex']),'Every interface instruction physically exact')
  # These source loads close the normal path immediately before FS0 restores.
  for read,g in GROUPS.items():
   need(program[read]['bytes_hex']=='64a100000000'and program[g['install']]['bytes_hex']=='64892500000000'and program[g['restore']]['bytes_hex']=='64890d00000000','Literal FS:[0] MOV group')
   need(program[g['entry']]['bytes_hex']=='6aff','Literal initial scope push -1');handler=program[g['entry']+2];need(handler['mnemonic']=='push'and handler['decoded_operands'][0]['value']==g['handler'],'Literal handler DWORD push');saved=program[g['saved_load']];need(saved['mnemonic']=='mov'and saved['operands'].startswith('ecx, dword ptr [esp + '),'Literal saved predecessor load')
  D=module(ROOT/'tools/m4-crt-allocation-root/run_v2.py','fs_original_archive');reader=D.DirectSet(BASE/'original-run-r2/original/transport.json',pin)
  try:
   for seq in range(6):
    head=None;active=[];pending=None;seqframes=[];acquired={};opaque=None
    for phase,item in enumerate(order):
     root=item['entry'];count=words(reader.data(f'phase/{seq}/{phase}/fs-event-count.bin'))[0];data=reader.data(f'phase/{seq}/{phase}/fs-events.bin');need(len(data)==1216*count,'Exact bounded event record length');expected_count=6 if root==0x4d4830 else 3 if root in(0x46ab30,0x48f250,0x4b4c10,0x4c3250,0x4cfe80)else 0;need(count==expected_count,'Source normal dynamic FS event count')
     for index in range(count):
      row=data[index*1216:(index+1)*1216];v,r,pc,kind,bh,ah,ra,captured=words(row,0,8);before=words(row,32,10);after=words(row,72,10);need((v,r,before[9],after[9])==(1,root,pc,pc),'Actual event/root/source PC association');need(pc in program,'Physical source FS PC');need(before[8]==after[8]and before[1:8]==after[1:8],'Whole original flags and seven nonEAX GPRs unchanged');need(after[0]==(bh if kind==0 else before[0]),'Exact intrinsic MOV EAX effect');need(ah==(bh if kind==0 else before[4]if kind==1 else before[1]),'Exact authentic FS head MOV effect');need(row[136:648]==row[648:1160]and row[1160:1188]==row[1188:1216],'Entire512B FX and28B ENV unaffected');need(row[112:124]==row[124:136],'Actual12B frame unchanged by the MOV');need(ra==(before[4]if kind==1 else bh),'Actual record observation address');need(captured==int(0x20001000<=ra and ra+12<=0x20002000),'Only owned original stack frame dereferenced by observer')
      if head is None:head=bh;opaque=bh;need(not captured and not 0x20001000<=bh<0x20002000,'First genuine Windows FS0 remains opaque external DWORD')
      need(bh==head,'Actual chain carries from preceding original FS MOV')
      if kind==0:
       need(pc in GROUPS and pending is None,'Named source saved-head read');g=GROUPS[pc];pending=dict(sequence=seq,phase=phase,root=root,group_entry=g['entry'],entry_ESP=before[4]+8,record_address=before[4]-4,predecessor=bh,handler=g['handler'],read_PC=pc,install_PC=g['install'],restore_PC=g['restore'],saved_load_PC=g['saved_load'],restore_ESP_delta=g['restore_delta'],restore_scope=g['scope'],parent_record=active[-1]['record_address']if active else None)
       if active:need(captured and words(row,112,3)==(active[-1]['predecessor'],active[-1]['handler'],0xffffffff),'Nested read observes exact active outer12B record');counts['nested_saved_head_reads']+=1
      elif kind==1:
       need(pending is not None and pc==pending['install_PC']and before[4]==pending['record_address'],'Source three-push record geometry');need(captured and words(row,112,3)==(pending['predecessor'],pending['handler'],0xffffffff),'All12 genuine installed bytes from saved FS0 and literal pushes');active.append(pending);pending=None;counts['installed_records']+=1
      else:
       need(kind==2 and pending is None and active,'Normal matched restore');f=active.pop();need(pc==f['restore_PC']and bh==f['record_address']and ah==f['predecessor'],'LIFO actual original restore/predecessor');need(before[4]==f['entry_ESP']-f['restore_ESP_delta'],'Exact source stack-relative saved-load geometry');need(before[1]==f['predecessor'],'Actual source saved predecessor ECX');need(captured and words(row,112,3)==(f['predecessor'],f['handler'],f['restore_scope']),'Full original record with literal final scope');f['install_record_hex']=struct.pack('<3I',f['predecessor'],f['handler'],0xffffffff).hex();f['restore_record_hex']=row[112:124].hex();seqframes.append(f);counts['restored_records']+=1
      head=ah;counts['full_CPU_MOV_relations']+=1;counts['whole_FX_ENV_relations']+=1;counts['actual_FS_events']+=1;counts['actual12B_snapshot_relations']+=captured
     need(not active and pending is None and(head is None or head==opaque),'All normal frames restore authentic Windows chain before root return')
     api=reader.data(f'phase/{seq}/{phase}/api-ledger.bin')
     for j,binding in enumerate(bindings):
      key=f'phase/{seq}/{phase}/fs-allocation/{j}/meta.bin'
      if key not in reader.entries:need(j not in acquired,'No acquired owner disappears before cleanup');continue
      meta=words(reader.data(key),0,9);need(meta[:5]==(1,j,binding['root'],binding['CALL_pc'],binding['requested_size']),'Exact dynamic source owner/site/request');need(meta[7]and meta[8]>=meta[4]and len(reader.data(f'phase/{seq}/{phase}/fs-allocation/{j}/bytes.bin'))==meta[8],'Whole genuine original owned backing capacity')
      if j in acquired:need(meta==acquired[j],'Actual owner identity carries across roots');counts['persistent_owner_identity_carries']+=1;continue
      need(root==binding['root'],'Acquisition in correct source root');ai=meta[6];need((ai+1)*104<=len(api),'Actual API ledger index');fact=words(api,ai*104,26);need(fact[24]==0 and fact[4]+104==meta[5]and fact[10]==meta[7]and fact[21]==0 and fact[22]==(meta[4]+15)&~15,'Authentic actual HeapAlloc frame/return/rounded size');initial=reader.data(f'phase/{seq}/{phase}/api-initial/{ai}/bytes.bin');size=words(reader.data(f'phase/{seq}/{phase}/api-initial/{ai}/size.bin'))[0];need(size==len(initial)==meta[8],'Entire true API allocation BEFORE result backing retained');acquired[j]=meta;owners.append(dict(sequence=seq,index=j,root=root,CALL_pc=meta[3],request=meta[4],frame=meta[5],API_index=ai,pointer=meta[7],capacity=meta[8],initial_sha256=hashlib.sha256(initial).hexdigest()));counts['true_API_BEFORE_new_owners']+=1
    need(len(seqframes)==7 and len(acquired)==10,'Seven actual frames and ten successful owners per persistent109 sequence');frames.extend(seqframes)
    for j,meta in acquired.items():
     need(reader.data(f'cleanup/{seq}/fs-allocation-{j}-before.bin')==struct.pack('<9I',*meta),'Cleanup authentic owner join');need(len(reader.data(f'cleanup/{seq}/fs-allocation-{j}-owned.bin'))==meta[8],'Retained complete precleanup owner bytes');need(reader.data(f'cleanup/{seq}/fs-allocation-{j}-returned.bin')==struct.pack('<I',1),'Actual positive literal MFC825/CRTfree call returned');counts['source_cleanup_owner_returns']+=1
   need(counts['actual_FS_events']==126 and counts['installed_records']==42 and counts['restored_records']==42 and counts['true_API_BEFORE_new_owners']==60,'Exact current totals');passed=True
  finally:reader.close()
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for filename,value in(('frames.json',frames),('owners.json',owners)):(out/filename).write_text(json.dumps(value,indent=2)+'\n');pin(out/filename)
  report=dict(passed=passed,scope='Fresh read-only functional original109 observer gate: exact original FS0 MOV CPU/FX/ENV/12B record relations, nested normal chain and ten true API allocation BEFORE owners per sequence. Allocation contents require separate literal source byteflow proof.',counts=dict(counts),first_Windows_FS0_preserved=True,actual_Windows_TEB_base_claimed=False,AFTER_machine_seed=False,native_execution=False,handler_execution=False,unwind_or_exception_dispatch=False,cleanup_scope='Actual literal MFC825/CRTfree positive CALL/RET; separate original cleanup HeapFree BOOL ledger not present',files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
