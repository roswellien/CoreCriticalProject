"""Author leaf/carry and raw failure observer; root models the complete composition."""
import hashlib,json,pathlib,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-entry-matherr'
PAGES=(0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000,0x7800b000,0x78039000,0x7803b000)
REGS=(2216,2248,2264,2232,2312,2328,2280,2296,2080,2472)
AF=((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def words(b):return struct.unpack('<'+'I'*(len(b)//4),b)
def put(b,o,v,n=4):b[o:o+n]=int(v).to_bytes(n,'little')
def dword(b,o):return int.from_bytes(b[o:o+4],'little')
def phase(row,name):return {p.name:p.read_bytes()for p in(row/name).iterdir()if p.is_file()}
def statecpu(s):
 c=[dword(s,o)for o in REGS];flags=int.from_bytes(s[2080:2088],'little')
 for o,bit in AF:flags=(flags&~(1<<bit))|((s[o]&1)<<bit)
 c[8]=flags;return c
def project(s,c):
 s=bytearray(s)
 for o,v in zip(REGS,c):put(s,o,v,8 if o==2080 else 4)
 for o,bit in AF:s[o]=(c[8]>>bit)&1
 return s
def addflags(a,b,f):
 v=(a+b)&0xffffffff;bits=int(a+b>0xffffffff)|(int((v&255).bit_count()%2==0)<<2)|(int(bool((a^b^v)&16))<<4)|(int(v==0)<<6)|(int(bool(v&0x80000000))<<7)|(int(bool((~(a^b)&(a^v))&0x80000000))<<11)
 return (f&~0x8d5)|bits
def positive(row):
 before=phase(row,'matherr-before');projected=phase(row,'matherr-projected');after=phase(row,'matherr-after');stopped=phase(row,'entry-after-fault')
 c=list(words(before['runtime-cpu.bin']));assert c[9]==0x5bb50c
 frame=c[4];pages={a:bytearray(before[f'page-{a}.bin'])for a in PAGES}
 assert dword(pages[0x20001000],frame-0x20001000)==0x5ac42e and dword(pages[0x20001000],frame+4-0x20001000)==0x51e7b0
 c[9]=0x7800b38f;s=project(before['state.bin'],c);assert projected['state.bin']==s
 for name in before:
  if name not in('state.bin','state-cpu.bin'):assert before[name]==projected[name],name
 assert projected['state-cpu.bin']==struct.pack('<10I',*statecpu(s))
 source=bytes.fromhex('8b4424048325b892037800a3c4b00378c3');assert before['matherr-source.bin']==source
 zero=dword(pages[0x78039000],0x2b8)
 events=((frame+4,0x51e7b0,4,0),(0x780392b8,zero,4,0),(0x780392b8,0,4,1),(0x7803b0c4,0x51e7b0,4,1),(frame,0x5ac42e,4,0))
 assert (row/'matherr-events.bin').read_bytes()==b''.join(struct.pack('<4I',*e)for e in events)
 for o,v in((2216,0x51e7b0),(2312,frame+4),(2472,0x5ac42e)):put(s,o,v)
 for o,v in((2065,0),(2067,1),(2069,0),(2071,1),(2073,0),(2077,0)):s[o]=v
 assert after['state.bin']==s and after['state-cpu.bin']==struct.pack('<10I',*statecpu(s)) and after['runtime-cpu.bin']==after['state-cpu.bin']
 put(pages[0x78039000],0x2b8,0);put(pages[0x7803b000],0xc4,0x51e7b0)
 for address in PAGES:assert after[f'page-{address}.bin']==pages[address]
 for name in('fx.bin','crt-globals.bin','tib-0.bin','tib-4.bin','tib-24.bin','entry-source.bin','matherr-source.bin'):assert after[name]==before[name]
 job=words((row/'matherr-job.bin').read_bytes());raw=dword(pages[0x5bb000],0x50c)
 assert job==(0x5bb50c,raw,frame,0x5ac42e,0x51e7b0,5,1,0,0,1,0,0)
 c=statecpu(s);s=project(s,c);flags=addflags(c[4],4,c[8]);put(s,2312,frame+4);put(s,2472,0x5ac5a0)
 for o,bit in AF:s[o]=(flags>>bit)&1
 assert stopped['state.bin']==s and stopped['state-cpu.bin']==struct.pack('<10I',*statecpu(s))
 c=statecpu(s);c[4]+=4;c[9]=0x5ac431;assert stopped['runtime-cpu.bin']==struct.pack('<10I',*c)
 put(pages[0x20001000],frame+4-0x20001000,0x5ac436)
 for address in PAGES:assert stopped[f'page-{address}.bin']==pages[address]
 for name in('fx.bin','crt-globals.bin','tib-0.bin','tib-4.bin','tib-24.bin','entry-source.bin','matherr-source.bin'):assert stopped[name]==after[name]
 calls=read(row/'calls.json');assert len(calls)==6 and not calls[0]['completed']and all(c['completed']for c in calls[1:])
 assert calls[-1]=={'site':0x5ac428,'target':0x5bb50c,'return_pc':0x5ac42e,'import':True,'completed':True}
 events=(row/'entry-events.bin').read_bytes();assert len(events)==35*20 and words(events[-20:])==(0x5ac431,frame+4,0x5ac436,4,1)
 assert phase(row,'retry-after')==stopped
def host(row):
 for name in('writer','entry'):
  p=row/(name+'-host-before.bin')
  if not p.exists():continue
  a=p.read_bytes();b=(row/(name+'-host-after.bin')).read_bytes();assert len(a)==len(b)==544
  assert a[512:540]==b[512:540]and a[:5]==b[:5]and a[24:28]==b[24:28]and a[256:416]==b[256:416]
  for i in range(8):assert a[32+16*i:42+16*i]==b[32+16*i:42+16*i]
def main(run_name,out_name):
 run=BASE/run_name;out=BASE/out_name;assert not out.exists();out.mkdir();files={};positive_count=negative_count=0;passed=False
 try:
  manifest=read(run/'report.json');assert manifest['passed']
  for category in('input_files','artifacts'):
   for p,h in manifest[category].items():assert sha(p)==h,p;files[p]=h
  for level in('O0','O2'):
   for index in range(48):
    row=run/level/f'row-{index}';r=read(row/'result.json');host(row);assert r['passed']and r['poisoned_retry']
    if index<24:positive(row);positive_count+=1
    else:
     mode=index-23;negative_count+=1;assert phase(row,'retry-after')==phase(row,'writer-after'if mode<4 else'entry-after-fault')
     if mode>=13:
      job=words((row/'matherr-job.bin').read_bytes());assert not job[7]and not job[9]
      expected={15:(2,0x7800b393,0x780392b8),16:(3,0x7800b39a,0x7803b0c4),18:(4,0x7800b39f,job[2]),19:(5,0x5ac42e,0),20:(5,0x5ac42e,0),21:(4,0x7800b393,0x780392b8)}
      if mode in expected:assert (job[5],job[10],job[11])==expected[mode]and job[8]
      if mode in(13,14,17,22,23):assert not job[6]and not job[5]
      if mode==24:assert job[6]and not job[7]and not job[5]and not job[8]
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  files[str(run/'report.json')]=sha(run/'report.json');files[str(pathlib.Path(__file__).resolve())]=sha(__file__)
  report=dict(passed=passed,scope='Author complete matherr leaf/caller-continuation model and actual causal prefix observer; independent root full FDIV/game source model still required',positive_sequences=positive_count,causal_denials=negative_count,State_bytes=3504,whole_pages=14,matherr_events_per_positive=5,game_events_per_positive=35,matherr_callback=0x51e7b0,callback_invoked=False,guest_FP_opaque_preserved=True,direct_host_FP_ENV_and_ABI_XMM6_15_preserved=True,root_oracle_imported=False,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
 if passed:print(json.dumps(report))
if __name__=='__main__':main(*sys.argv[1:])
