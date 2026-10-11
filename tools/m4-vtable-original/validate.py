"""Execute frozen actual original120 into direct strict canonical archives."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];BASE=ROOT/'reports/m4-vtable-original'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
CASES=((0,0x7f,0),(0,0x37f,7),(0,0xf7f,0),(1,0x47f,7),(1,0xa7f,0),(1,0xe7f,7))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(buildpath,digest,name):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);files={};passed=False
 def pin(p,h=None):
  p=Path(p).absolute();v=sha(p);assert h is None or h==v,(p,h,v);files[str(p)]=v;return p
 try:
  b=json.loads(pin(buildpath,digest).read_text(encoding='utf-8-sig'));assert b['passed']
  for p,h in json.loads(pin(Path(buildpath).parent/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(p,h)
  worker=pin(b['worker'],b['worker_sha256']);pack=pin(b['pack']);game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a');pin(__file__);pin(sys.executable);pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
  capture=BASE/'execution-r1/original';stage=BASE/'execution-r1/run';verify_stage(stage,sha(pin(stage/'stage.json')));st=json.loads((stage/'stage.json').read_text());assert st['passed'],'Actual original120 stage failed'
  p=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('onexit_original_direct',p);ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds);records=ds.DirectSet(capture/'transport.json',pin)
  try:
   assert records.data('COMPLETE.txt')==b'complete';head=records.data('header.bin');assert head[:8]==b'MW4J120O'and struct.unpack_from('<6I',head,8)==(1,6,120,720,40,332416)
   prep=json.loads(pin(Path(b['preparation'])/'report.json',b['preparation_sha256']).read_bytes());order=prep['order'];roots=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-strings-source/recovery-r7/string-roots.json').read_bytes());roots+=json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes());roots+=json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes());roots+=json.loads(pin(ROOT/'reports/m4-container-source/recovery-r3/container-roots.json').read_bytes());roots+=json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/instruction-contracts.json').read_bytes())['roots'];roots.sort(key=lambda r:r['slot']);callbacks=[r['registration']['callback']for r in roots]
   for seq,(repeat,cw,top)in enumerate(CASES):
    seen=[]
    for phase,row in enumerate(order):
     data=records.data(f'phase/{seq}/{phase}.bin');assert len(data)==332416;assert struct.unpack_from('<9I',data)==(seq,repeat,phase,row['slot'],row['entry'],cw,top,0,1);assert struct.unpack_from('<I',data,92)[0]==0x20001804 and struct.unpack_from('<I',data,112)[0]==0x410a80
     begin,nxt,capacity,mode=struct.unpack_from('<4I',data,331888);assert begin and begin<=nxt and(nxt-begin)%4==0 and nxt-begin<=capacity<=512;assert mode==1,'Actual source-established mode1 provider domain'
     count=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/api-count.bin'))[0];assert count<=32 and len(records.data(f'phase/{seq}/{phase}/api-ledger.bin'))==count*104;found=next((r for r in roots if r['entry']==row['entry']),None)
     if found:seen.append(found['registration']['callback'])
     assert nxt-begin==len(seen)*4;assert struct.unpack_from('<'+str(len(seen))+'I',data,331904)==tuple(seen)
    assert records.data(f'cleanup/{seq}/registry.bin')==struct.pack('<92I',*callbacks)
   imports=json.loads(pin(Path(b['preparation'])/'mfc-import-bindings.json').read_bytes());ledger=records.data('mfc-import-ledger.bin');assert len(ledger)==511*28;loaded=bytearray(records.data('mfc-loaded-page.bin'));raw=records.data('mfc-raw-page.bin');assert len(loaded)==len(raw)==4096
   for k,expected in enumerate(imports):
    slot,bound,target,declared,owner,named,ordinal=struct.unpack_from('<7I',ledger,k*28);assert(slot,bound,ordinal)==(expected['slot'],expected['raw'],expected['ordinal'])and target==named and declared and owner;assert struct.unpack_from('<I',loaded,slot&4095)[0]==target;struct.pack_into('<I',loaded,slot&4095,bound)
    for base in set((declared,owner)):
     path=records.data(f'mfc-modules/{base}/path.bin').decode('utf-16-le').rstrip('\0');observed=records.data(f'mfc-modules/{base}/image.bin');physical=Path(path);physical=Path(re.sub(r'(?i)system32',lambda m:'SysWOW64',str(physical))) if str(physical).lower().startswith('c:\\windows\\system32\\') else physical;assert physical.read_bytes()==observed,(path,physical);pin(physical)
   assert bytes(loaded)==raw,'Every complete nonimport page byte exact after only authenticated511 import projections'
   bindings=prep['mfc_bindings']
   for seq in range(6):
    for mi,item in enumerate(bindings):
     actual=struct.unpack('<8I',records.data(f'phase/{seq}/119/mfc/{mi}/meta.bin'));assert actual[:5]==tuple(item[k]for k in('root','CALL_pc','requested_size','object','publication'))and actual[5]and actual[6]>=item['requested_size']and actual[7]==mi;assert len(records.data(f'phase/{seq}/119/mfc/{mi}/bytes.bin'))==actual[6];assert records.data(f'cleanup/{seq}/mfc-{mi}-before.bin')==struct.pack('<8I',*actual);assert records.data(f'cleanup/{seq}/mfc-{mi}-returned.bin')==struct.pack('<I',1)
   contracts=json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/instruction-contracts.json','a58e31641f42e8e37c1d66bad5e41dd57854b82a7a00bd86a02b1bc85aec9108').read_bytes());specs=contracts['static_indirect_inputs'];pair_count=0
   ret_PC={0x40e820:0x40e827,0x59ff00:0x59ff0d,0x59ff80:0x59ffa1}
   for seq in range(6):
    seq_pairs=0
    for phase,row in enumerate(order):
     count=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/vtable-count.bin'))[0];raw=records.data(f'phase/{seq}/{phase}/vtable-snapshots.bin');expected=[r for r in specs if r['root']==row['entry']]
     assert count==2*len(expected) and len(raw)==count*660
     for k,spec in enumerate(expected):
      first,last=raw[k*1320:k*1320+660],raw[k*1320+660:k*1320+1320];a=struct.unpack_from('<16I',first);z=struct.unpack_from('<16I',last);ca=struct.unpack_from('<10I',first,64);cz=struct.unpack_from('<10I',last,64)
      assert a[:5]==(1,2*k,row['entry'],0,spec['target']) and z[:5]==(1,2*k+1,row['entry'],1,ret_PC[spec['target']])
      assert a[5:9]==z[5:9]==tuple(spec[t]for t in('target','CALL_pc','slot','target'))
      assert a[9:]==z[9:] and a[10]==spec['source_object'] and a[11]==spec.get('source_vtable',0) and a[13:15]==(spec['return_pc'],spec['RET_cleanup'])
      assert ca[1]==cz[1]==spec['entry_ECX'] and ca[4]==cz[4]==a[12] and ca[9]==spec['target'] and cz[9]==ret_PC[spec['target']]
      assert first[644:660]==last[644:660] and struct.unpack_from('<I',first,644)[0]==spec['return_pc']
      if spec['argument']is not None:assert struct.unpack_from('<I',first,648)[0]==spec['argument']==0
      for reg in(3,5,6,7):assert ca[reg]==cz[reg],'Original helper preserved actual nonvolatile register'
      if spec['target']==0x40e820:assert cz[0]==0 and ca[8]==cz[8]
      if spec['target']==0x59ff80:assert cz[0]==0 and cz[8]&0x8c1==0x40,'Actual zero-pointer TEST flags without pointee path'
      # All ordinary helper effects are integer; authentic hardware floating images carry exactly.
      assert first[104:644]==last[104:644],'Full actual helper FX512/ENV28 carry'
      pair_count+=1;seq_pairs+=1
    assert seq_pairs==6
   assert pair_count==36
   passed=True
  finally:records.close()
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual original120 x86 persistent40observedpages, original sentinel/producer and real32MSVCRTregistration; actual indirect target entry/preRET observations, no nativeattach/exitcallbacks',original_executed=True,native_executed=False,phases=720 if passed else 0,build_path=str(buildpath),build_sha256=digest,original_capture=str(BASE/'execution-r1/original/transport.json'),capture_reused_from_completed_fresh_original_run=True,record_bytes=332416,indirect_CALL_RET_pairs=pair_count if passed else 0,indirect_postRET_source_derived_only=True,per_phase_reseed=False,files=files);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).absolute(),sys.argv[2],sys.argv[3])

