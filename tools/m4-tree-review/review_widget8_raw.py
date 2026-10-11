"""Independent raw widget refusal byteflows and full exported machine retries."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir()
 pins={};counts=collections.Counter();passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower() not in('.zip','.mwb')
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v,(p,h,v)
  assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def raw(p):return pin(p).read_bytes()
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def words(p,n):return struct.unpack('<'+'I'*n,raw(p))
 def memory(d):
  regions={int(p.stem.split('-')[-1]):bytearray(raw(p))for p in d.glob('game-region-*.bin')}
  assert len(regions)==5 and all(len(b)%4096==0 for b in regions.values())
  regions[0x20001000]=bytearray(raw(d/'stack.bin'));assert len(regions[0x20001000])==4096
  tib=words(d/'TIB.bin',5);assert tib[0]==tib[4] and tib[2:4]==(0x20002000,0x20001000)
  for o,v in((0,tib[1]),(4,tib[2]),(8,tib[3]),(24,tib[4])):regions[tib[0]+o]=bytearray(struct.pack('<I',v))
  return regions,tib
 def region(m,a,n):
  xs=[(p,b)for p,b in m.items()if p<=a and a+n<=p+len(b)];assert len(xs)==1,(hex(a),n);return xs[0]
 def load(m,a,n):p,b=region(m,a,n);return bytes(b[a-p:a-p+n])
 def store(m,a,b):p,v=region(m,a,len(b));v[a-p:a-p+len(b)]=b
 try:
  semantic=read(R/'reports/m4-widget-native/controls-verification-r2/report.json','44760b4e05decc5a63204fa24fab93158c390be0b7d5a4b17d338e15546936ab')
  independent=read(R/'reports/m4-widget-original-review/controls-r1/report.json','c2fa9ae4ba2a2f03748addea77f0855d920d412e9b2f6059309829b4dc14fd6e')
  assert semantic['passed']and independent['passed']and independent['legacy_checker_predicates_preserved']
  for p,h in independent['files'].items():pin(p,h)
  execution=read(R/'reports/m4-widget-native/controls-execution-r1/report.json',semantic['execution_sha256'])
  assert execution['passed']and execution['all_workers_terminal']and execution['actual_workers_launched']==16
  contract=read(R/'reports/m4-widget-native/preparation-r6/contracts.json')
  pcs={r['pc']:r for r in contract['instructions']}
  spec=importlib.util.spec_from_file_location('widget_raw_pe',pin(R/'tools/analysis/pe.py'));pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe)
  game=pe.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  sentinel=[(0x5ac3d8,0x9a17ec),(0x5ac3e2,0x9a17f0)]
  for pc,a in sentinel:
   off,_=game.rva_range(pc-game.image_base,10);assert game.data[off:off+10]==b'\xc7\x05'+struct.pack('<II',a,0xffffffff)
   counts['whole_physical_bootstrap_stores']+=1
  seen=set()
  for run in execution['runs']:
   level,mode=run['level'],run['mode'];assert(level,mode)not in seen;seen.add((level,mode));d=Path(run['capture'])
   stage=read(run['stage'],run['stage_sha256']);assert stage['passed']
   current,tib=memory(d/'control/authored-before');initial,_=memory(d/'initial-own-input')
   ledger=list(struct.iter_unpack('<IIQII',raw(d/'retry-before/locale-source-accesses.bin')))
   for pc,a in sentinel:
    assert [r for r in ledger if r[0]==pc]==[(pc,a,0xffffffff,4,1)]and load(initial,a,4)==bytes(4)
    store(initial,a,struct.pack('<I',0xffffffff));counts['actual_physical_sentinel_joins']+=1
   if mode==3:store(initial,0x5bb070,bytes(4))
   if mode==4:store(initial,0x40e250,bytes([load(initial,0x40e250,1)[0]^1]))
   game_keys=[a for a in current if a!=0x20001000 and not tib[0]<=a<=tib[0]+24]
   for a in game_keys:assert current[a]==initial[a]
   target=0x40ef50 if mode==8 else 0x40e250
   cpu=words(d/'control/authored-before/CPU.bin',10);frame=cpu[4]-4;assert frame==0x20001800
   components=list((d/'retry-before').glob('root-*/component'))+list((d/'retry-before').glob('bootstrap/component'));assert len(components)==1
   c=components[0];accesses=list(struct.iter_unpack('<IIQII',raw(c/'accesses.bin')))
   if mode!=6:store(current,frame,struct.pack('<I',0xfffffff0))
   for i,(pc,a,v,n,writing)in enumerate(accesses):
    assert pc in pcs and n in(1,2,4)and writing in(0,1)
    row=pcs[pc];source=bytes.fromhex(row['bytes_hex']);off,_=game.rva_range(pc-game.image_base,len(source));assert game.data[off:off+len(source)]==source
    if not writing:assert int.from_bytes(load(current,a,n),'little')==v
    elif mode in(5,7)and i==len(accesses)-1:
     assert (a==tib[0]and n==4)if mode==7 else a==0x5f4d78
     counts['actual_denied_uncommitted_writes']+=1
    else:store(current,a,v.to_bytes(n,'little'))
   fault,ftib=memory(d/'retry-before/runtime')
   for a in game_keys:assert current[a]==fault[a];counts['complete_fault_game_regions']+=1
   assert current[0x20001000]==fault[0x20001000]and struct.unpack('<I',current[tib[0]])[0]==ftib[1];counts['complete_stack_and_FS_byteflows']+=1
   # The existing strict checker retains all 47,968 private-file comparisons.
   # Independently recompute every whole observable machine region here.
   for logical in ('State.bin','CPU.bin','FX.bin','stack.bin','TIB.bin',*[f'game-region-{a}.bin'for a in game_keys]):
    assert raw(d/'retry-before/runtime'/logical)==raw(d/'retry-after/runtime'/logical);counts['whole_machine_retry_files']+=1
   assert words(d/'cleanup/status.bin',8)==(1,mode,1,1,1,1,1,1)
   assert not raw(c/'APIs.bin')and not raw(c/'fonts.bin')
   for logical in('control/caller-hardware.bin','control/retry-hardware.bin','cleanup/font-caller-hardware.bin'):
    b=raw(d/logical);assert len(b)==1632 and b[:512]==b[1088:1600]and b[512:540]==b[1600:1628];counts['complete_raw_hardware_restores']+=1
   summary=struct.unpack('<32Q',raw(d/'cleanup/registry-summary.bin'));assert summary[:5]==(1,1,0,1,1)and summary[5]==summary[10]==summary[11]==summary[15]==0
   counts['actual_cleaned_poisoned_contexts']+=1
  assert seen=={(l,m)for l in('O0','O2')for m in range(1,9)}
  pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for p,h in pins.items():
   with Path(p).open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h
  report=dict(passed=passed,scope='Independent complete own-input/fault machine byteflows, whole machine poisoned retries and actual raw hardware/resource closure; full private export equality retained by the separately source-reviewed strict checker',counts=dict(counts),semantic_validation_sha256='44760b4e05decc5a63204fa24fab93158c390be0b7d5a4b17d338e15546936ab',archive_reader_opened=False,initializer_credit=0,hidden_Runtime_or_permissions_bytes_claim=False,files=pins)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=hashlib.sha256(q.read_bytes()).hexdigest(),counts=dict(counts),files=len(pins))))
if __name__=='__main__':main(sys.argv[1])

