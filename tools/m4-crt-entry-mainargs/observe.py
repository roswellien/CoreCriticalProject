"""Author full-buffer/source-effect and terminal-retry checks; root oracle is separate."""
import hashlib,importlib.util,json,pathlib,struct,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-mainargs'
PAGES=[0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000,0x7800b000,0x78039000,0x7803b000,0x5e0000,0x78001000]
IDENTITIES=['entry-source.bin','matherr-source.bin','control-wrapper.bin','control-thunk.bin','control-hot.bin','control-cold.bin','initterm-thunk.bin','initterm-provider.bin','mainargs-provider.bin','mainargs-builder.bin']
def data(p):return pathlib.Path(p).read_bytes()
def sha(p):return hashlib.sha256(data(p)).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def u32(b,p=0):return struct.unpack_from('<I',b,p)[0]
def put(b,p,v):struct.pack_into('<I',b,p,v)
def cpu(p):return struct.unpack('<10I',data(p))
def host(a,b):
 a=data(a);b=data(b);assert len(a)==len(b)==544
 assert a[:5]==b[:5] and a[24:28]==b[24:28] and a[512:540]==b[512:540]
 for i in range(8):assert a[32+16*i:42+16*i]==b[32+16*i:42+16*i]
 assert a[256:416]==b[256:416]
def records(row):
 job=struct.unpack('<20I',data(row/'mainargs-job.bin'));access=data(row/'mainargs-accesses.bin');events=data(row/'mainargs-events.bin')
 assert len(access)==1280 and len(events)==256 and access[job[10]*20:]==bytes(1280-job[10]*20) and events[job[11]*16:]==bytes(256-job[11]*16)
 return job,[struct.unpack_from('<5I',access,20*i)for i in range(job[10])],[struct.unpack_from('<4I',events,16*i)for i in range(job[11])]
def mainargs(row):
 before=row/'mainargs-projected';after=row/'mainargs-after';s0=data(before/'state.bin');s1=data(after/'state.bin');assert len(s0)==len(s1)==3504
 c=cpu(before/'state-cpu.bin');frame=c[4];assert frame==0x20001860 and c[9]==0x7800ba5e
 expected=[(0x7800ba5e,frame-4,c[5],4,1),(0x7800ba61,frame+20,0x20001890,4,0),(0x7800ba64,frame+16,0,4,0),(0x7800ba68,0x20001890,0,4,0),(0x7800ba6a,0x78037150,0,4,1),(0x7800ba99,frame-8,0x7800ba9e,4,1),(0x7800bbbc,frame-12,frame-4,4,1),(0x7800bbbf,frame-16,c[1],4,1),(0x7800bbc0,frame-20,c[1],4,1),(0x7800bbc1,frame-24,c[6],4,1),(0x7800bbc2,frame-28,c[7],4,1),(0x7800bbc8,frame-32,260,4,1),(0x7800bbcd,frame-36,0x7803b3f0,4,1),(0x7800bbce,frame-40,0,4,1),(0x7800bbd0,0x7802e018,0x343b0,4,0),(0x7800bbd0,frame-44,0x7800bbd6,4,1)]
 job,access,events=records(row);assert access==expected
 assert job==(0x5bb514,0x1ded02,frame,0x5ac46e,0x2000189c,0x2000188c,0x20001898,0,0x20001890,0,16,4,0,1,0,1,1,2,0x7800bbd0,0x7802e018)
 assert events==[(1,0x7800ba5e,frame,0x5ac46e),(2,0x7800ba99,0x7800bbbc,0x7800ba9e),(3,0x7800bbbc,frame-8,0x7800ba9e),(4,0x7800bbd0,0x7802e018,0x343b0)]
 predicted=bytearray(s0)
 for offset,value in [(2216,0),(2312,frame-44),(2328,frame-12),(2280,0x7803b3f0),(2472,0x343b0)]:put(predicted,offset,value)
 for offset,value in [(2065,0),(2067,1),(2069,0),(2071,1),(2073,0),(2077,0)]:predicted[offset]=value
 assert s1==predicted,'Complete source-owned State and opaque storage'
 assert cpu(after/'state-cpu.bin')==(0,c[1],c[2],c[3],frame-44,frame-12,0x7803b3f0,c[7],(c[8]&~0x8d5)|0x44,0x343b0)
 assert data(before/'runtime-cpu.bin')==data(after/'runtime-cpu.bin') and cpu(after/'runtime-cpu.bin')[4:]==(frame,c[5],c[6],c[7],c[8],0x5bb514)
 for page in PAGES:
  expected_page=bytearray(data(before/f'page-{page}.bin'))
  for pc,address,value,width,write in expected:
   if write and page<=address<page+4096:put(expected_page,address-page,value)
  assert data(after/f'page-{page}.bin')==expected_page,'Complete owned page source delta'
 for name in IDENTITIES+['fx.bin','crt-globals.bin','tib-0.bin','tib-4.bin','tib-24.bin']:
  assert data(before/name)==data(after/name)
 assert sum(len(data(before/n))for n in IDENTITIES)==1140
 assert data(row/'mainargs-reason.txt').decode().strip()=='Required KERNEL32.dll!GetModuleFileNameA remains unresolved'
 calls=read(row/'calls.json');assert len(calls)==11 and not calls[0]['completed'] and not calls[10]['completed'] and all(x['completed']for x in calls[1:10])
 assert calls[-1]=={'site':0x5ac468,'target':0x5bb514,'return_pc':0x5ac46e,'import':True,'completed':False}
 for phase in ['mainargs-before','mainargs-projected','mainargs-builder-before','mainargs-builder-projected','mainargs-builder-after','mainargs-after']:
  assert data(row/phase/'fx.bin')==data(before/'fx.bin')
 assert data(after/'state.bin')==data(row/'entry-after-fault/state.bin')
def causal(row,mode):
 job,access,events=records(row);assert job[12]==job[14]==0 and job[13]==job[15]==1 and not job[16]
 specifications={49:(0,0,1,0x7800ba5e,0),50:(6,2,2,0x7800bbbc,0),51:(0,0,1,0x7800ba5e,0),52:(14,3,2,0x7800bbd0,0x7802e018),53:(4,1,1,0x7800ba6a,0x78037150),54:(0,1,1,0x7800ba5e,0x2000185c),55:(6,1,1,0x7800ba99,0x20001858),56:(5,1,1,0x7800ba6a,0x78037150),57:(6,2,1,0x7800ba71,0x7800b3b4),58:(6,2,2,0x7800bbbc,0x7802e018),59:(0,0,1,0x7800ba5e,0),60:(6,3,2,0x7800bbbc,0x20001854)}
 assert (job[10],job[11],job[17],job[18],job[19])==specifications[mode]
 state=data(row/'mainargs-after/state.bin')
 if mode==54:assert u32(state,2312)==0x20001860
 if mode==60:assert u32(state,2312)==0x20001858
 if mode==55:assert u32(state,2312)==0x20001858 and u32(state,2472)==0x7800bbbc
 if mode==52:assert u32(state,2312)==0x20001838 and u32(state,2472)==0x7800bbd0
 if mode==56:
  assert access[-1]==(0x7800ba6a,0x78037150,0x13579bdf,4,1)
  assert u32(data(row/f'mainargs-after/page-{0x78037000}.bin'),0x150)==0x13579bdf
 if mode==57:
  assert access[-1]==(0x7800ba71,0x20001858,0x7800ba76,4,1) and events[-1]==(7,0x7800ba71,0x7800b3b4,0x7800ba76)
def main(run_name,out_name):
 run=BASE/run_name;out=BASE/out_name;assert not out.exists();out.mkdir();files={}
 for p,h in read(run/'report.json')['input_files'].items():assert sha(p)==h;files[p]=h
 # Frozen prefix observer functions are copied with only additional last-call positioning.
 old=ROOT/'tools/m4-crt-entry-initterm/observe.py';source=old.read_text()
 source=source.replace('assert len(calls)==10 and not calls[0][\'completed\'] and all(x[\'completed\']for x in calls[1:])','assert len(calls)==11 and not calls[0][\'completed\'] and all(x[\'completed\']for x in calls[1:10])')
 source=source.replace('calls[-4]==','calls[-5]==').replace('calls[-3]==','calls[-4]==').replace('calls[-2]==','calls[-3]==').replace('calls[-1]==','calls[-2]==')
 source=source.replace('u32(final,2472)==0x1ded02 and u32(final,2312)==0x20001860','u32(final,2472)==0x343b0 and u32(final,2312)==0x20001834')
 # The function globals resolve helpers without running the old main.
 prefix={'__file__':str(old),'__name__':'frozen_prefix_observer'};exec(compile(source,str(old),'exec'),prefix)
 (out/'frozen-prefix-observer-adapted.py').write_text(source)
 positives=denials=hostpairs=0
 for level in ('O0','O2'):
  for i in range(84):
   row=run/level/f'row-{i}';r=read(row/'result.json');assert r['passed'] and r['poisoned_retry'] and not r['whole_M4_complete'];host(row/'writer-host-before.bin',row/'writer-host-after.bin');hostpairs+=1
   if not r['entry_executed']:
    assert 1<=r['control']<=3
    for p in(row/'writer-after').iterdir():assert data(p)==data(row/'retry-after'/p.name)
    denials+=1;continue
   host(row/'entry-host-before.bin',row/'entry-host-after.bin');hostpairs+=1
   assert data(row/'writer-after/state.bin')==data(row/'entry-before-invoke/state.bin') and data(row/'writer-after/fx.bin')==data(row/'entry-before-invoke/fx.bin')
   for p in(row/'entry-after-fault').iterdir():assert data(p)==data(row/'retry-after'/p.name)
   assert struct.unpack('<20I',data(row/'mainargs-job.bin'))[12]==0 and struct.unpack('<20I',data(row/'mainargs-job.bin'))[14]==0
   assert struct.unpack('<16I',data(row/'initterm-job.bin'))[9]==struct.unpack('<16I',data(row/'initterm-job.bin'))[11]==0
   if not r['control']:
    assert (r['fault_reason'],r['fault_site'],r['fault_target'])==(1,0x7800bbd0,0x7802e018) and r['source_events']==48 and r['writer_events']==97
    prefix['positive'](row);prefix['initterm'](row);mainargs(row);positives+=1
   else:
    assert (r['fault_site'],r['fault_target'])!=(0x7800bbd0,0x7802e018)
    if r['control']>=49:assert (r['fault_reason'],r['fault_site'],r['fault_target'])==(4,0x5bb514,0x5bb514);causal(row,r['control'])
    denials+=1
 assert (positives,denials,hostpairs)==(48,120,330)
 for p in run.rglob('*'):
  if p.is_file():files[str(p.resolve())]=sha(p)
 files[str(pathlib.Path(__file__).resolve())]=sha(__file__);files[str(old.resolve())]=sha(old)
 report=dict(passed=True,scope='Author complete source-owned State/page effects and carry/retry checks; independent root instruction oracle is separate',positive_sequences=positives,causal_denials=denials,host_direct_pairs=hostpairs,whole_State_bytes=3504,separate_FX_bytes=512,owned_pages=16,source_identity_bytes=1140,mainargs_accesses=48*16,mainargs_routes=48*4,next_stop_PC=0x7800bbd0,next_stop_target=0x7802e018,new_pages=0,State_reseed_inside_mainargs=False,Runtime_provider_translation_registered=False,Runtime_provider_import_registered=False,argc_argv_environment_outputs_admitted=False,native_game_executed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json');files[str(out/'frozen-prefix-observer-adapted.py')]=sha(out/'frozen-prefix-observer-adapted.py');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main(*sys.argv[1:])
