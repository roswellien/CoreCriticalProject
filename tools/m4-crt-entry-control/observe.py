"""Author whole-buffer carry checks; independent instruction oracle is separate."""
import hashlib,json,pathlib,struct,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-entry-control'
PAGES=[0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000,0x7800b000,0x78039000,0x7803b000]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def data(p):return pathlib.Path(p).read_bytes()
def u16(b,o=0):return struct.unpack_from('<H',b,o)[0]
def u32(b,o=0):return struct.unpack_from('<I',b,o)[0]
def host(a,b):
 a=data(a);b=data(b);assert len(a)==len(b)==544
 assert a[:5]==b[:5] and a[24:28]==b[24:28] and a[512:540]==b[512:540]
 for i in range(8):assert a[32+16*i:42+16*i]==b[32+16*i:42+16*i]
 assert a[256:416]==b[256:416]
def positive(row):
 before=row/'control-projected';after=row/'control-after'
 s0=data(before/'state.bin');s1=data(after/'state.bin');f0=data(before/'fx.bin');f1=data(after/'fx.bin')
 assert len(s0)==len(s1)==3504 and len(f0)==len(f1)==512
 old=u16(f0);expected=(old&~0x300)|0x200
 assert u16(s0,2768)==old and u16(f1)==u16(s1,2768)==expected
 assert f1[2:]==f0[2:]
 allowed={*range(2065,2081),*range(2080,2088),*range(2768,2770)}
 for offset in [2216,2248,2264,2232,2312,2328,2280,2296,2472]:allowed.update(range(offset,offset+4))
 assert all(a==b or i in allowed for i,(a,b)in enumerate(zip(s0,s1)))
 # Only source-owned control stack operands change during control execution.
 for page in PAGES:
  a=data(before/f'page-{page}.bin');b=data(after/f'page-{page}.bin');assert len(a)==len(b)==4096
  if page!=0x20001000:assert a==b
 assert data(before/'crt-globals.bin')==data(after/'crt-globals.bin')
 for name in ['entry-source.bin','matherr-source.bin','control-wrapper.bin','control-thunk.bin','control-hot.bin','control-cold.bin','tib-0.bin','tib-4.bin','tib-24.bin']:
  assert data(before/name)==data(after/name)
 job=struct.unpack('<12I',data(row/'control-job.bin'));assert job==(0x1ded8a,13,52,0,0,0,0,1,0,0,0,0)
 events=[struct.unpack_from('<4I',data(row/'control-events.bin'),i*16)for i in range(13)]
 pcs=[0x5ac5a0,0x5ac5d6,0x1ded8a,0x780042e1,0x780042f7,0x7800432c,0x78004308,0x7800439f,0x7800431f,0x780042f4,0x5ac5af,0x5ac5af,0x5ac436]
 assert [x[1]for x in events]==pcs and [x[0]for x in events]==[1,3,4,1,1,1,2,1,2,2,2,5,2]
 assert data(row/'control-events.bin')[13*16:]==bytes(48)
 access=data(row/'control-accesses.bin');assert len(access)==5120 and access[52*20:]==bytes(4080)
 typed=[struct.unpack_from('<5I',access,i*20)for i in range(52)if u32(access,i*20+12)==2]
 assert typed==[(0x780042fd,0x20001854,old,2,1),(0x78004324,0x20001864,expected&~0x40,2,0)]
 calls=read(row/'calls.json');assert len(calls)==8 and not calls[0]['completed'] and all(x['completed']for x in calls[1:])
 assert calls[-2]=={'site':0x5ac431,'target':0x5ac5a0,'return_pc':0x5ac436,'import':False,'completed':True}
 assert calls[-1]=={'site':0x5ac5aa,'target':0x5bb578,'return_pc':0x5ac5af,'import':True,'completed':True}
 assert u32(s1,2472)==0x5ac436 and u32(s1,2312)==0x20001878
 final=data(row/'entry-after-fault/state.bin');assert u32(final,2472)==0x5ac598 and u32(final,2312)==0x2000186c
def main(run_name,out_name):
 run=BASE/run_name;out=BASE/out_name;assert not out.exists();out.mkdir();files={}
 for p,h in read(run/'report.json')['input_files'].items():assert sha(p)==h;files[p]=h
 positives=negatives=boundaries=0
 for level in ('O0','O2'):
  for i in range(60):
   row=run/level/f'row-{i}';r=read(row/'result.json');assert r['passed'] and r['poisoned_retry'] and not r['whole_M4_complete']
   host(row/'writer-host-before.bin',row/'writer-host-after.bin');boundaries+=1
   if not r['entry_executed']:
    assert 1<=r['control']<=3
    for p in(row/'writer-after').iterdir():assert data(p)==data(row/'retry-after'/p.name)
    negatives+=1;continue
   host(row/'entry-host-before.bin',row/'entry-host-after.bin');boundaries+=1
   assert data(row/'writer-after/state.bin')==data(row/'entry-before-invoke/state.bin')
   assert data(row/'writer-after/fx.bin')==data(row/'entry-before-invoke/fx.bin')
   for p in(row/'entry-after-fault').iterdir():assert data(p)==data(row/'retry-after'/p.name)
   job=struct.unpack('<12I',data(row/'control-job.bin'));assert job[4]==job[5]==0
   if not r['control']:
    assert r['fault_reason']==0 and r['fault_site']==0x5ac440 and r['fault_target']==0x5ac598
    assert r['source_events']==38 and r['writer_events']==97 and r['data_routes']==1
    positive(row);positives+=1
   else:
    assert (r['fault_site'],r['fault_target'])!=(0x5ac440,0x5ac598);negatives+=1
 assert (positives,negatives,boundaries)==(48,72,234)
 for p in run.rglob('*'):
  if p.is_file():files[str(p.resolve())]=sha(p)
 files[str(pathlib.Path(__file__).resolve())]=sha(__file__)
 report=dict(passed=True,scope='Author complete buffer carry/integrity/terminal retry checks; independent source-derived architectural oracle remains separate',positive_sequences=positives,causal_denials=negatives,host_direct_pairs=boundaries,whole_State_bytes=3504,owned_pages=14,control_events=48*13,control_accesses=48*52,actual_compiled_native_control=True,actual_game_entry_continuation=True,next_stop_PC=0x5ac440,next_stop_target=0x5ac598,State_reseed_after_writer=False,State_reseed_after_control=False,original_game_executed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json')
 (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main(*sys.argv[1:])
