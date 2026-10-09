"""Actual provider/native CPU, memory, FP representations and route observations."""
import argparse,hashlib,json,mmap,pathlib,struct
ROOT=pathlib.Path(__file__).resolve().parents[2];COUNT=3264;OS=10456;NS=17596;CWS=[0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f];GPR=[2216,2248,2264,2232,2312,2328,2280,2296,2472];FLAGS=[(2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11)]
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,why):
 if not v:raise ValueError(why)
def unpack(b,o,n):return struct.unpack_from('<'+str(n)+'I',b,o)
def word(b,o=0):return struct.unpack_from('<H',b,o)[0]
def seed_state(row,i):
 s=bytearray((j*13+i+7)&255 for j in range(3504));struct.pack_into('<I',s,2120,0);struct.pack_into('<I',s,2168,0x7ffde000);struct.pack_into('<I',s,2184,0);cpu=unpack(row,24,10)
 for offset,v in zip(GPR,cpu[:8]+cpu[9:]):struct.pack_into('<I',s,offset,v)
 struct.pack_into('<Q',s,2080,cpu[8]);
 for offset,bit in FLAGS:s[offset]=(cpu[8]>>bit)&1
 s[2736:2760]=bytes(24);s[2768:3280]=row[104:616];env=row[2152:2180]
 s[2774:2776]=env[18:20];s[2776:2780]=env[12:16];s[2780:2782]=env[16:18];s[2784:2788]=env[20:24];s[2788:2790]=env[24:26]
 for r in range(8):s[2480+16*r+6:2480+16*r+16]=row[104+32+16*r:104+42+16*r];s[16+64*r:32+64*r]=row[104+160+16*r:104+176+16*r]
 return bytes(s)
def actual_original(row,i):
 need(len(row)==OS,'Original record extent');repeat=i//1632;entry=(i//816)%2;case=(i//12)%68;cw=CWS[i%12];tag=unpack(row,0,6)
 if case==0:q=(0,0)
 elif case==1:q=(0,0xffffffff)
 elif case==2:q=(0xffffffff,0xffffffff)
 elif case==3:q=(0x35ab96d2,0x8c75ea31)
 else:bit=1<<((case-4)//2);q=(0 if case&1 else bit,bit)
 need(tag==(repeat,entry,case,cw,*q),'Actual exact directed original input order');before=unpack(row,24,10);after=unpack(row,64,10)
 need(before==(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,0x202,(0x780042e1,0x780042f7)[entry]),'Actual original CPU entry domain');need(after[4]==0x20001804 and after[9]==0x10000100 and all(after[j]==before[j] for j in (3,5,6,7)),'Actual original cdecl/nonvolatile return')
 fx0=row[104:616];fx1=row[616:1128];env0=row[2152:2180];env1=row[2180:2208]
 need(word(fx0)==cw and word(fx0,2)==0 and fx0[4]==0 and unpack(fx0,24,1)==(0x1f80,),'Actual original empty masked CW domain');need(word(fx1)==word(env1) and fx0[2:]==fx1[2:] and env0[2:]==env1[2:],'Actual guest non-CW FP preservation');need(row[1128:1640]==row[1640:2152] and row[2208:2236]==row[2236:2264],'Full actual original host restoration')
 memory=bytearray([0xa5]*4096);struct.pack_into('<3I',memory,0x800,0x10000100,*q);need(row[2264:6360]==memory,'Actual complete original stack input');return tag,after
def expected_events(entry):
 outer=(0x780042e1,0x780042f7)[entry];s=0x20001800;rows=[(1,outer,s,0x10000100)]
 if entry==0:s-=12;rows.append((1,0x780042f7,s,0x780042f4))
 rows.extend([(1,0x7800432c,s-20,0x78004308),(2,0x78004308,s-16,0x78004308),(1,0x7800439f,s-24,0x7800431f),(2,0x7800431f,s-20,0x7800431f)])
 if entry==0:rows.append((2,0x780042f4,s+4,0x780042f4))
 rows.append((2,0x10000100,0x20001804,0x10000100));return rows
def differential(original,native,i):
 tag,after=actual_original(original,i);need(len(native)==NS,'Native record extent');need(native[:64]==original[:64],'Actual native input tag/CPU');cpu=unpack(native,64,10);need(cpu[:8]==after[:8] and cpu[9]==after[9] and ((cpu[8]^after[8])&~0x10)==0,'Actual complete CPU and all defined/preserved FLAGS differential')
 need(native[104:616]==original[104:616] and native[616:1128]==original[616:1128],'Separate actual FX512 differential');need(native[1128:1156]==original[2152:2180] and native[1156:1184]==original[2180:2208],'Separate actual legacy ENV28 differential')
 before=seed_state(original,i);need(native[1184:4688]==before,'Complete3504 native prestate identity');post=bytearray(before)
 for offset,v in zip(GPR,after[:8]+after[9:]):struct.pack_into('<I',post,offset,v)
 for offset,bit in FLAGS:post[offset]=0 if bit==4 else (after[8]>>bit)&1
 post[2768:2770]=original[616:618];need(native[4688:8192]==post,'Complete native State architectural writes/hidden preservation');need(native[8192:12288]==original[2264:6360] and native[12288:16384]==original[6360:10456],'Complete4096-byte guest stack differential')
 events=expected_events(tag[1]);need(unpack(native,16384,1)==(len(events),),'Actual complete CALL/RET ledger count');expected=struct.pack('<'+str(len(events)*4)+'I',*(x for row in events for x in row))+bytes(128-len(events)*16);need(native[16388:16516]==expected,'Actual compiled CALL/RET sequence/PC/ESP differential')
 need(native[16516:17028]==native[17028:17540] and native[17540:17568]==native[17568:17596],'Full actual native host FX/ENV restoration')
def controls(o,n):
 result=[]
 locations=[('native',x,y) for x,y in [('tag',0),('GPR-EAX',64),('ECX',68),('EDX',72),('EBX',76),('ESP',80),('EBP',84),('ESI',88),('EDI',92),('FLAGS-CF',96),('FLAGS-PF',96),('FLAGS-ZF',96),('FLAGS-SF',96),('FLAGS-DF',97),('FLAGS-OF',97),('EIP',100),('FX-CW',616),('FX-SW',618),('FX-tags',620),('FX-MXCSR',640),('FX-FIP',624),('legacy-CW',1156),('legacy-FOP',1174),('legacy-FIP',1168),('legacy-FDP',1176),('state-CW',4688+2768),('state-hidden',4688+3400),('state-FS',4688+2168),('before-stack',8192),('after-stack',12288),('after-RETword',12288+0x7f4),('route-count',16384),('route-target',16392),('route-ESP',16396),('route-return',16400),('host-CW',17028),('host-ENV',17568)]]
 locations+=[('original','host-FX',1640),('original','host-ENV',2236),('original','actual-input',16),('original','guest-after-CW',616)]
 for kind,start,label in [('native',616+32,'FX-raw80'),('native',616+160,'FX-XMM'),('native',4688+2768+32,'State-raw80'),('native',4688+16,'State-vector'),('native',17028+32,'host-raw80'),('native',17028+160,'host-XMM')]:
  for j in range(8):locations.append((kind,label+'-'+str(j),start+16*j if label!='State-vector' else start+64*j))
 for kind,name,offset in locations:
  oo,nn=bytearray(o),bytearray(n);b=nn if kind=='native' else oo;mask={'FLAGS-PF':4,'FLAGS-ZF':64,'FLAGS-SF':128,'FLAGS-DF':4,'FLAGS-OF':8}.get(name,1);b[offset]^=mask
  try:differential(oo,nn,0)
  except (ValueError,struct.error) as e:result.append({'name':kind+'-'+name,'rejected':True,'diagnostic':str(e)});continue
  raise ValueError('Observer accepted '+kind+'-'+name)
 changed=bytearray(o);changed[96]^=0x10;differential(changed,n,0);result.append({'name':'architecturally-undefined-original-AF','accepted_only_explicit_exclusion':True});return result
def main(out,native_report):
 need(not out.exists() and out.is_relative_to(ROOT/'reports/m4-crt-control'),'Fresh private comparison');op=ROOT/'reports/m4-crt-control/original-run-r1/report.json';np=native_report;om=json.loads(op.read_text());nm=json.loads(np.read_text());need(om['passed'] and nm['passed'] and len(om['actual_controls'])==8 and len(nm['actual_controls'])==16,'Actual complete worker control reports');raw=pathlib.Path(om['raw']['path']);need(sha(raw)==om['raw']['sha256'],'Exact actual original identity');observer=[]
 event_totals={}
 with raw.open('rb')as of,mmap.mmap(of.fileno(),0,access=mmap.ACCESS_READ)as o:
  need(o[:8]==b'MW4CFC01' and unpack(o,8,4)==(1,COUNT,OS,4096) and len(o)==24+COUNT*OS,'Original raw header')
  for level in ('O0','O2'):
   p=pathlib.Path(nm['raws'][level]['path']);need(sha(p)==nm['raws'][level]['sha256'],'Exact actual native identity')
   with p.open('rb')as nf,mmap.mmap(nf.fileno(),0,access=mmap.ACCESS_READ)as n:
    need(n[:8]==b'MW4CFN01' and unpack(n,8,4)==(1,COUNT,NS,3504) and len(n)==24+COUNT*NS,'Native raw header')
    event_totals[level]=0
    for i in range(COUNT):
     row=n[24+i*NS:24+(i+1)*NS];differential(o[24+i*OS:24+(i+1)*OS],row,i);event_totals[level]+=unpack(row,16384,1)[0]
    observer+=controls(o[24:24+OS],n[24:24+NS])
  for i in range(COUNT//2):
   a=o[24+i*OS:24+(i+1)*OS];b=o[24+(i+COUNT//2)*OS:24+(i+COUNT//2+1)*OS];need(a[4:96]==b[4:96] and ((unpack(a,96,1)[0]^unpack(b,96,1)[0])&~0x10)==0 and a[100:1128]==b[100:1128] and a[2152:2208]==b[2152:2208] and a[2264:]==b[2264:],'Actual original guest exact repeat excluding undefined AF')
 out.mkdir(parents=True);report={'passed':True,'scope':'Actual original versus four-body static native control provider within empty TOP0/SW0 measured domain; independent review/integration pending','original_records':COUNT,'native_records':2*COUNT,'differences':0,'actual_exact_guest_repeats':COUNT//2,'actual_worker_controls':24,'observer_controls':observer,'defined_exit_FLAGS_mask':0x8c5,'full_FLAGS_excluded_undefined_mask':0x10,'State_bytes':3504,'separate_FX_bytes':512,'legacy_ENV_bytes':28,'guest_stack_bytes':4096,'actual_native_CALL_RET_events':sum(event_totals.values()),'actual_native_CALL_RET_events_per_optimization':event_totals,'runtime_r9_mutated':False,'whole_M4_complete':False};rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');paths=[op,np,raw,pathlib.Path(__file__),rp]+[pathlib.Path(nm['raws'][x]['path']) for x in ('O0','O2')];(out/'pins.json').write_text(json.dumps({'files':{str(p.resolve()):sha(p) for p in paths}},indent=2)+'\n');print('3264 original /6528 native passed;',len(observer),'observer controls')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('native_report',type=pathlib.Path);a.add_argument('output',type=pathlib.Path);v=a.parse_args();main(v.output.resolve(),v.native_report.resolve())
