"""One-time additive author observer materialization."""
import pathlib
HERE=pathlib.Path(__file__).resolve().parent
def once(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
def main():
 p=HERE/'observe.py';s=p.read_text().replace('m4-crt-entry-control','m4-crt-entry-initterm').replace('range(60)','range(72)').replace('(48,72,234)','(48,96,282)')
 s=once(s,'0x78039000,0x7803b000]','0x78039000,0x7803b000,0x5e0000,0x78001000]')
 s=once(s,'len(calls)==8','len(calls)==10');s=once(s,'calls[-2]','calls[-4]');s=once(s,'calls[-1]','calls[-3]')
 s=once(s,'u32(final,2472)==0x5ac598 and u32(final,2312)==0x2000186c','u32(final,2472)==0x1ded02 and u32(final,2312)==0x20001860')
 s=once(s,"r['fault_reason']==0 and r['fault_site']==0x5ac440 and r['fault_target']==0x5ac598","r['fault_reason']==1 and r['fault_site']==0x5ac468 and r['fault_target']==0x5bb514")
 s=once(s,"r['source_events']==38","r['source_events']==48");s=s.replace("(r['fault_site'],r['fault_target'])!=(0x5ac440,0x5ac598)","(r['fault_site'],r['fault_target'])!=(0x5ac468,0x5bb514)")
 s=once(s,'positive(row);positives+=1','positive(row);initterm(row);positives+=1')
 s=once(s,'owned_pages=14','owned_pages=16');s=s.replace('next_stop_PC=0x5ac440,next_stop_target=0x5ac598','initterm_events=48*6,initterm_accesses=48*8,next_stop_PC=0x5ac468,next_stop_target=0x5bb514')
 s=once(s,'def main(run_name,out_name):','''def initterm(row):
 before=row/'initterm-projected';after=row/'initterm-after'
 s0=data(before/'state.bin');s1=data(after/'state.bin')
 assert data(before/'fx.bin')==data(after/'fx.bin')
 allowed={*range(2065,2081),*range(2080,2088)}
 for offset in [2216,2248,2264,2232,2312,2328,2280,2296,2472]:allowed.update(range(offset,offset+4))
 assert all(a==b or i in allowed for i,(a,b)in enumerate(zip(s0,s1)))
 for page in PAGES:
  if page!=0x20001000:assert data(before/f'page-{page}.bin')==data(after/f'page-{page}.bin')
 for name in ['initterm-thunk.bin','initterm-provider.bin','crt-globals.bin','tib-0.bin','tib-4.bin','tib-24.bin']:
  assert data(before/name)==data(after/name)
 job=struct.unpack('<16I',data(row/'initterm-job.bin'))
 assert job==(0x5bb510,0x1ded12,0x2000186c,0x5ac445,0x5e0248,0x5e024c,8,7,6,0,1,0,0,1,0,0)
 accesses=data(row/'initterm-accesses.bin');assert len(accesses)==640 and accesses[160:]==bytes(480)
 saved=u32(s0,2280)
 expected=[(0x5ac598,0x5bb510,0x1ded12,4,0),(0x780014f8,0x20001868,saved,4,1),(0x780014f9,0x20001870,0x5e0248,4,0),(0x78001502,0x20001874,0x5e024c,4,0),(0x78001508,0x5e0248,0,4,0),(0x78001502,0x20001874,0x5e024c,4,0),(0x78001512,0x20001868,saved,4,0),(0x78001513,0x2000186c,0x5ac445,4,0)]
 assert accesses[:160]==b''.join(struct.pack('<5I',*v)for v in expected)
 assert u32(s1,2472)==0x5ac445 and u32(s1,2312)==0x20001870 and u32(s1,2280)==saved
 assert data(row/'initterm-undefined.bin')==struct.pack('<I',0x7800150a)
 calls=read(row/'calls.json')
 assert calls[-2]=={'site':0x5ac440,'target':0x5ac598,'return_pc':0x5ac445,'import':False,'completed':True}
 assert calls[-1]=={'site':0x5ac598,'target':0x5bb510,'return_pc':0x5ac445,'import':True,'completed':True}
 events=[(1,0x5ac598,0x2000186c,0x5ac445),(2,0x1ded12,0x2000186c,0x5ac445),(3,0x780014f8,0x2000186c,0x5ac445),(4,0x78001508,0x5e0248,0),(5,0x5ac445,0x20001870,0x5ac445),(6,0x5ac445,0x20001870,0x5ac445)]
 assert data(row/'initterm-events.bin')==b''.join(struct.pack('<4I',*v)for v in events)+bytes(160)
def main(run_name,out_name):''')
 s=once(s,'job[4]==job[5]==0','job[4]==job[5]==0\n   initjob=struct.unpack(\'<16I\',data(row/\'initterm-job.bin\'));assert initjob[9]==initjob[11]==0')
 p.write_text(s)
if __name__=='__main__':main()
