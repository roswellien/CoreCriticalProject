"""Whole CPU/FX/ENV and normal chain audit of authentic original120 MOVs."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-next-source';NEW=BASE;ORIG=ROOT/'reports/m4-vtable-original'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh original120 FS receipt');out.mkdir(parents=True);pins={};counts=collections.Counter();frames=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Sealed physical input');pins[str(p)]=v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  source=json.loads(pin(NEW/'original-game-source-r1/report.json').read_bytes());need(source['passed']and not source['AFTER_machine_seed'],'Passed genuine BEFORE-derived source');derivations=json.loads(pin(NEW/'original-game-source-r1/FS-source-derivations.json',source['files'][str((NEW/'original-game-source-r1/FS-source-derivations.json').resolve())]).read_bytes());need(len(derivations)==360,'60 authentic source FS accesses per sequence');pin(ORIG/'validation-r1/report.json');pin(ROOT/'reports/m4-vtable-original/observer-compiled-r1/report.json')
  G=load('original120_FS_program',ROOT/'tools/m4-next-source/game_model.py');program,_=G.source_program();PE=load('original120_FS_physical_PE',ROOT/'tools/analysis/pe.py');images=[PE.PEImage(pin(p,h).read_bytes())for p,h in((ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'))];contract=json.loads(pin(NEW/'recovery-r1/instruction-contracts.json','a58e31641f42e8e37c1d66bad5e41dd57854b82a7a00bd86a02b1bc85aec9108').read_bytes());order=contract['selected_order'];D=load('original120_FS_archive',ROOT/'tools/m4-crt-allocation-root/run_v2.py');reader=D.DirectSet(ORIG/'execution-r1/original/transport.json',pin)
  try:
   for seq in range(6):
    head=None;opaque=None;active=[];pending=None;modelrows=[r for r in derivations if r['sequence']==seq];observed=0
    for phase,item in enumerate(order):
     root=item['entry'];count=words(reader.data(f'phase/{seq}/{phase}/fs-event-count.bin'))[0];data=reader.data(f'phase/{seq}/{phase}/fs-events.bin');need(len(data)==count*1216,'All complete transparent observer records');expected=6 if root==0x4d4830 else 3 if root in(0x46ab30,0x48f250,0x4b4c10,0x4c3250,0x4cfe80,0x47f5b0,0x47f6d0,0x48f210,0x47f5f0)else 9 if root==0x4b12d0 else 6 if root in(0x4ada90,0x4d84a0,0x5a7dc0)else 0;need(count==expected,'Exact physically recovered normal FS dynamic count')
     for index in range(count):
      b=data[index*1216:(index+1)*1216];v,r,pc,kind,bh,ah,address,captured=words(b,0,8);before=words(b,32,10);after=words(b,72,10);need((v,r,before[9],after[9])==(1,root,pc,pc),'True observer association and source PC');row=program[pc];image=images[int(pc>=0x78000000)];off,_=image.rva_range(pc-image.image_base,row['width']);need(image.data[off:off+row['width']]==bytes.fromhex(row['bytes_hex']),'Authentic PE source FS instruction');need(row['bytes_hex']==('64a100000000'if kind==0 else '64892500000000'if kind==1 else '64890d00000000'),'Only exact literal FS0 MOV accepted');need(before[1:]==after[1:]and after[0]==(bh if kind==0 else before[0]),'All ten CPU DWORDs with exact intrinsic MOV effect');need(ah==(bh if kind==0 else before[4]if kind==1 else before[1]),'Exact authentic FS0 MOV value');need(b[136:648]==b[648:1200]and b[1200:1188]==b[1188:1216],'Entire512B FX and28B ENV unchanged');need(b[112:124]==b[124:136],'Entire12B record unchanged by observation and MOV');need(address==(before[4]if kind==1 else bh)and captured==int(0x20001000<=address and address+12<=0x20002000),'Actual owned stack record dereference bound');d=modelrows[observed];need((d['phase'],d['root'],d['PC'],d['kind'],d['before_head'],d['after_head'],d['source_ESP'],d['record_address'])==(phase,root,pc,kind,bh,ah,before[4],address),'Every actual full event joins sealed genuine-BEFORE literal derivation');need(d['record_hex']==(b[112:124].hex()if captured else None),'All captured bytes join complete source12B prediction');observed+=1
      if head is None:head=opaque=bh;need(not captured and bh not in(0,0xffffffff),'Actual first Windows predecessor retained opaque')
      need(bh==head,'Actual normal FS head carries from prior source MOV')
      if kind==0:
       need(pending is None,'No overlapping uninstalled frame');pending=dict(sequence=seq,phase=phase,root=root,read_PC=pc,record_address=before[4]-4,predecessor=bh,parent_record=active[-1]['record_address']if active else None)
       if active:need(captured and address==active[-1]['record_address'],'Nested saved head observes genuine active parent');counts['nested_saved_head_reads']+=1
      elif kind==1:
       need(pending is not None and address==pending['record_address']and captured,'Exact source push/install record');a=words(b,112,3);need(a[0]==pending['predecessor']and ((a[1],a[2])==(0x7800ef03,0x7802e260)if pc>=0x78000000 else a[2]==0xffffffff),'Actual source predecessor and initial scope push');pending.update(handler=a[1],install_PC=pc,install_record_hex=b[112:124].hex());active.append(pending);pending=None;counts['installed_records']+=1
      else:
       need(kind==2 and pending is None and active,'Matched normal restore');f=active.pop();a=words(b,112,3);need(captured and bh==f['record_address']and ah==f['predecessor']and a[:2]==(f['predecessor'],f['handler']),'LIFO saved predecessor/full actual record restore');f.update(restore_PC=pc,restore_record_hex=b[112:124].hex());frames.append(f);counts['restored_records']+=1
      head=ah;counts['full_CPU_MOV_relations']+=1;counts['whole_FX_ENV_relations']+=1;counts['actual_FS_events']+=1;counts['actual12B_snapshot_relations']+=captured
     need(not active and pending is None and(head is None or head==opaque),'Every root restores its genuine Windows chain')
    need(observed==60,'Complete15game+5nestedNULL-free frames per sequence')
   need(counts['actual_FS_events']==360 and counts['installed_records']==120 and counts['restored_records']==120,'Complete actual120 normal observer scope');pin(__file__);passed=True
  finally:reader.close()
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'frames.json').write_text(json.dumps(frames,indent=2)+'\n');pin(out/'frames.json');r=dict(passed=passed,scope='Actual original120 all60 FS0 accesses per sequence: complete CPU MOV effect, entire FX/ENV, full12B snapshots from sealed genuine BEFORE source, fifteen normal game frames and five genuine nested CRTfree(NULL) frames, exact LIFO restoration.',counts=dict(counts),first_Windows_FS0_preserved=True,AFTER_machine_seed=False,actual_Windows_TEB_base_claimed=False,handler_execution=False,unwind_or_exception_dispatch=False,allocation_ownership_gate_separate=True,files=pins);(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
