"""Actual connected records; only the declared original capture-PC projection."""
import hashlib,json,pathlib,struct,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-control-integration';COUNT=192;OS=10444;NS=17764
CWS=[0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f];SP=[0x100,0x1fc,0x200,0x7f0,0x7fc,0x800,0x808,0xff0];REQUESTED_FLAGS=[0x202,0x203,0x212,0x246,0x282,0xa02,0x242,0x802]
GPR=[2216,2248,2264,2232,2312,2328,2280,2296,2472];FLAGS=[(2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11)]
def sha(p):
 with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def need(v,w):
 if not v:raise ValueError(w)
def u(b,o,n=1):return struct.unpack_from('<'+str(n)+'I',b,o)
def w(b,o=0):return struct.unpack_from('<H',b,o)[0]
def original(row,i):
 need(len(row)==OS,'Original exact connected row extent');tag=(i//96,CWS[(i%96)//8],i%8);need(u(row,0,3)==tag,'Exact requested connected order');scenario=tag[2];q=0x1020304*scenario;before=u(row,12,10);after=u(row,52,10)
 expected=tuple(x^q for x in [0x13579bdf,0x2468ace0,0x81726354,0x10293847])+(0x20001000+SP[scenario],)+tuple(x^q for x in [0x92837465,0x56473829,0xaabbccdd])+(REQUESTED_FLAGS[scenario]|0x200,0x5ac5a0);need(before==expected,'Actual connected CPU domain; CPL3 POPFD cannot clear IF')
 need(after[4]==before[4]+4 and after[9]==0x10000100 and all(after[j]==before[j]for j in [3,5,6,7]),'Actual wrapper cdecl/nonvolatile return at literal capture PC')
 s=before[4];x=s-8;arith=(1 if s<x else 0)|(((s&255).bit_count()%2==0)<<2)|(((x^8^s)&16))|((s==0)<<6)|(((s>>31)&1)<<7)|((bool(~(x^8)&(x^s)&0x80000000))<<11);need(after[8]==(before[8]&~0x8d5)|arith,'Actual wrapper ADD ESP,8 defines all arithmetic flags including AF')
 fx0=row[92:604];fx1=row[604:1116];env0=row[2140:2168];env1=row[2168:2196];need(w(fx0)==tag[1] and w(fx0,2)==0 and fx0[4]==0 and u(fx0,24)==(0x1f80,),'Actual original empty TOP0/SW0/CW domain');need(fx0[6:24]==bytes(18),'Actual current FXSAVE legacy metadata is zero')
 for j in range(8):need(fx0[32+16*j:42+16*j]==bytes((17+j*13+k*7)&255 for k in range(10)),'Actual nonzero raw80 input storage')
 need(fx0[160:288]==bytes((j*19+3)&255 for j in range(128)),'Actual complete seeded XMM0..7 input')
 seedenv=struct.pack('<6H',tag[1],0xffff,0,0xffff,0xffff,0xffff)+struct.pack('<IHHIHH',0x11223344,0x23,0x11d,0x55667788,0x2b,0xffff);need(env0==seedenv,'Actual complete legacy seeded metadata')
 need(w(fx1)==w(env1)==(tag[1]&~0x300)|0x200 and fx0[2:]==fx1[2:] and env0[2:]==env1[2:],'Only measured wrapper-requested guest precision bits change')
 need(row[1116:1628]==row[1628:2140] and row[2196:2224]==row[2224:2252],'Complete actual original host FX/legacy restoration')
 stack=bytearray([0xa5]*4096);struct.pack_into('<I',stack,SP[scenario],0x5ac436);need(row[2252:6348]==stack,'Complete actual original stack input');mem=row[6348:10444];need(u(mem,SP[scenario]-12,3)==(0x5ac5af,0x10000,0x30000) and u(mem,SP[scenario])==(0x5ac436,),'Actual wrapper CALL return/arguments and unchanged original caller frame')
 return before,after,tag
def seed_state(row,i):
 s=bytearray((j*13+i+7)&255 for j in range(3504));struct.pack_into('<I',s,2120,0);struct.pack_into('<I',s,2168,0x7ffde000);struct.pack_into('<I',s,2184,0);cpu=u(row,12,10)
 for offset,v in zip(GPR,cpu[:8]+cpu[9:]):struct.pack_into('<I',s,offset,v)
 struct.pack_into('<Q',s,2080,cpu[8])
 for offset,bit in FLAGS:s[offset]=(cpu[8]>>bit)&1
 s[2736:2760]=bytes(24);s[2768:3280]=row[92:604];env=row[2140:2168];s[2774:2776]=env[18:20];s[2776:2780]=env[12:16];s[2780:2782]=env[16:18];s[2784:2788]=env[20:24];s[2788:2790]=env[24:26]
 for j in range(8):s[2480+16*j+6:2480+16*j+16]=row[92+32+16*j:92+42+16*j];s[16+64*j:32+64*j]=row[92+160+16*j:92+176+16*j]
 return s
def events(s):
 p=s-12;q=p-12;return [(1,0x5ac5a0,s,0x5ac436),(3,0x5ac5d6,p,0x5ac5af),(4,0x1ded8a,p,0x5ac5af),(1,0x780042e1,p,0x5ac5af),(1,0x780042f7,q,0x780042f4),(1,0x7800432c,q-20,0x78004308),(2,0x78004308,q-16,0x78004308),(1,0x7800439f,q-24,0x7800431f),(2,0x7800431f,q-20,0x7800431f),(2,0x780042f4,q+4,0x780042f4),(2,0x5ac5af,p+4,0x5ac5af),(5,0x5ac5af,p+4,0x5ac5af),(2,0x5ac436,s+4,0x5ac436)]
def differential(o,n,i):
 before,after,tag=original(o,i);need(len(n)==NS and n[:52]==o[:52],'Actual native tags and BEFORE CPU');cpu=u(n,52,10);need(cpu[:9]==after[:9] and cpu[9]==0x5ac436,'All actual CPU/GPR/full FLAGS differential; literal admitted native return PC')
 need(n[92:1116]==o[92:1116] and n[1116:1144]==o[2140:2168] and n[1144:1172]==o[2168:2196],'Separate complete FX512 and ENV28 actual differential')
 s=seed_state(o,i);need(n[1172:4676]==s,'Complete3504 native BEFORE State identity');post=bytearray(s)
 for offset,v in zip(GPR,cpu[:8]+cpu[9:]):struct.pack_into('<I',post,offset,v)
 for offset,bit in FLAGS:post[offset]=(after[8]>>bit)&1
 post[2768:2770]=o[604:606];need(n[4676:8180]==post,'Complete3504 State architectural writes and hidden/FS/legacy preservation')
 need(n[8180:12276]==o[2252:6348] and n[12276:16372]==o[6348:10444],'Complete4096 stack differential including already-pushed tail frame')
 e=events(before[4]);need(u(n,16372)==(len(e),),'Actual ordered phase count');packed=b''.join(struct.pack('<4I',*r)for r in e)+bytes(256-16*len(e));need(n[16376:16632]==packed,'Actual complete compiled CALL/RET/tail entry observations')
 need(n[16632:17144]==n[17144:17656] and n[17656:17684]==n[17684:17712],'Complete actual native host FX/ENV restoration');need(u(n,17712)==(2,) and u(n,17716,12)==(0x5ac431,0x5ac5a0,0x5ac436,0,1,0,0x5ac5aa,0x5bb578,0x5ac5af,1,1,1),'Actual r9 completed outer route and single import orchestration records')
def observers(o,n):
 result=[];locations=[('native','input-tag',0),('original','input-CW',4),('original','requested-CPU',12),('original','actual-IF-policy',44),('original','actual-capture-PC',88),('original','actual-AF',84),('original','input-stack',2252),('original','actual-tail-returnword',6348+0xf4),('original','host-FX',1628),('original','host-ENV',2224)]
 locations += [('native',name,off)for name,off in [('EAX',52),('ECX',56),('EDX',60),('EBX',64),('ESP',68),('EBP',72),('ESI',76),('EDI',80),('all-FLAGS',84),('defined-AF',84),('native-return-PC',88),('guest-FX',604),('legacy-FOP',1144+18),('legacy-FIP',1144+12),('legacy-FDP',1144+20),('State-CW',4676+2768),('State-hidden',4676+3400),('State-FS',4676+2168),('before-stack',8180),('after-stack',12276),('already-pushed-return',12276+0xf4),('route-count',16372),('actual-thunk-entry',16376+16+4),('actual-raw-IAT-read',16376+32+4),('actual-tail-ESP',16376+32+8),('provider-entry',16376+48+4),('host-FX',17144),('host-ENV',17684),('r9-record-count',17712),('r9-original-CALLsite',17716),('r9-import-slot',17716+24+4),('r9-import-completion',17716+24+16)]]
 for label,start,step in [('FX-raw80',604+32,16),('FX-XMM',604+160,16),('State-raw80',4676+2480+6,16),('State-vectors',4676+16,64),('host-raw80',17144+32,16),('host-XMM',17144+160,16)]:
  locations += [('native',label+'-'+str(j),start+j*step)for j in range(8)]
 for kind,name,off in locations:
  oo,nn=bytearray(o),bytearray(n);b=oo if kind=='original'else nn;b[off]^=0x10 if 'AF' in name else 1
  try:differential(oo,nn,0)
  except(ValueError,struct.error)as e:result.append({'name':kind+'-'+name,'rejected':True,'diagnostic':str(e)});continue
  raise ValueError('Observer accepted '+kind+' '+name)
 return result
def main(native_report,out):
 need(not out.exists() and out.is_relative_to(BASE),'Fresh connected comparison');nm=read(native_report);op=pathlib.Path(nm['original_report_path']);om=read(op);need(nm['passed'] and om['passed'] and len(nm['actual_controls'])==20 and len(om['actual_controls'])==9,'Actual complete worker controls');raw=pathlib.Path(om['raw']['path']);need(sha(raw)==om['raw']['sha256'],'Exact actual original identity');o=raw.read_bytes();need(o[:8]==b'MW4CIC01' and u(o,8,4)==(1,COUNT,OS,4096) and len(o)==24+COUNT*OS,'Exact original raw header');controls=[];totals={}
 for level in ('O0','O2'):
  p=pathlib.Path(nm['raws'][level]['path']);need(sha(p)==nm['raws'][level]['sha256'],'Exact actual native identity');n=p.read_bytes();need(n[:8]==b'MW4CIN01' and u(n,8,4)==(1,COUNT,NS,3504) and len(n)==24+COUNT*NS,'Exact actual native header');totals[level]=0
  for i in range(COUNT):row=n[24+i*NS:24+(i+1)*NS];differential(o[24+i*OS:24+(i+1)*OS],row,i);totals[level]+=u(row,16372)[0]
  controls+=observers(o[24:24+OS],n[24:24+NS])
 for i in range(96):a=o[24+i*OS:24+(i+1)*OS];b=o[24+(i+96)*OS:24+(i+97)*OS];need(a[4:1116]==b[4:1116] and a[2140:2196]==b[2140:2196] and a[2252:]==b[2252:],'Actual complete guest exact repeats')
 out.mkdir();report={'passed':True,'scope':'Connected actual game wrapper/thunk/provider via typed r9 tail-frame port within serial empty TOP0/SW0 domain; independent review pending','original_records':192,'native_records':384,'differences':0,'actual_guest_exact_repeats':96,'worker_controls':29,'observer_controls':controls,'all_defined_FLAGS_mask':0xcd5,'undefined_FLAG_exclusions':0,'original_literal_capture_PC':0x10000100,'native_literal_admitted_return_PC':0x5ac436,'instrumentation_projection':'Only original authored capture10000100 versus real native game return5AC436; both exact PCs individually required, all other CPU/FP/State/memory unchanged','actual_requested_IF_clear_observations':24,'actual_CPL3_IF_preserved':True,'State_bytes':3504,'FX_bytes':512,'legacy_ENV_bytes':28,'stack_bytes':4096,'actual_native_phase_events':sum(totals.values()),'actual_native_phase_events_per_level':totals,'actual_Runtime_call_records':768,'shared_Runtime_r9_changed':False,'following_numerical_callback_integrated':False,'full_CRT_startup_executed':False,'whole_M4_complete':False};rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');paths=[rp,native_report,op,raw,pathlib.Path(__file__)]+[pathlib.Path(nm['raws'][l]['path'])for l in ('O0','O2')];(out/'pins.json').write_text(json.dumps({'files':{str(p.resolve()):sha(p)for p in paths}},indent=2)+'\n');print('192 original/384 native connected records pass;',len(controls),'observer controls;',sha(rp))
if __name__=='__main__':main(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve())
