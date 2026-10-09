"""Input-derived author observer; never used as native execution input."""
from pathlib import Path
from collections import Counter
import hashlib,json,mmap,struct,sys
ROOT=Path(__file__).resolve().parents[2]
BASES=(0x5bb000,0x78115000,0x60b000,0x20001000)
F=0x20001800;CAP=0x410a80;ROOTPC=0x4c19f0;BODY=0x4c1a00;LEAF=0x780c10f0
GPRS=(2216,2248,2264,2232,2312,2328,2280,2296,2472)
FLAGS=(2065,2067,2069,2071,2073,2075,2077);FBITS=(0,2,4,6,7,10,11)
SWPOS=(2755,2753,2751,2749,2747,2745,2757,2737,2739,2741,2743);SWBITS=(0,1,2,3,4,5,6,8,9,10,14)
CW=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
INPUTS=(0x7f7fffff,0,0x80000000,1,0x80000001,0x7fffff,0x800000,0x3f800000,0xbf800000,0x3eaaaaab,0xff7fffff,0x7f800000,0xff800000,0x7fc12345,0x7f812345,0xff812345)
OFF={'before':48,'after':4132,'checkpoint':8216,'memory_before':12300,'memory_after':28684,'host_before':45068,'host_after':45580,'host_env_before':46092,'host_env_after':46120,'events':46148,'routes':46588,'counts':46648}
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def u32(b,o=0):return struct.unpack_from('<I',b,o)[0]
def u16(b,o=0):return struct.unpack_from('<H',b,o)[0]
def p32(b,o,v):struct.pack_into('<I',b,o,v)
def p16(b,o,v):struct.pack_into('<H',b,o,v)
def memoff(a):return BASES.index(a&~4095)*4096+(a&4095)
def pe_page(raw,address):
 nt=u32(raw,0x3c);assert raw[:2]==b'MZ' and raw[nt:nt+4]==b'PE\0\0' and u16(raw,nt+4)==0x14c;opt=nt+24;assert u16(raw,opt)==0x10b;imagebase=u32(raw,opt+28);rva=address-imagebase;result=bytearray(4096);matches=0
 for i in range(u16(raw,nt+6)):
  p=opt+u16(raw,nt+20)+i*40;vs,va,rs,rp=struct.unpack_from('<4I',raw,p+8)
  if va<=rva and rva+4096<=va+max(vs,rs):
   n=max(0,min(4096,rs-(rva-va)));result[:n]=raw[rp+rva-va:rp+rva-va+n];matches+=1
 assert matches==1,(hex(address),matches)
 return bytes(result)
class Raw:
 def __init__(self,p,magic,stride):
  self.path=Path(p);self.f=self.path.open('rb');self.m=mmap.mmap(self.f.fileno(),0,access=mmap.ACCESS_READ)
  assert self.m[:8]==magic and u32(self.m,8)==1
  self.count=u32(self.m,12);self.stride=u32(self.m,16);assert self.stride==stride and u32(self.m,20)==4 and len(self.m)==24+self.count*stride
 def row(self,i):return self.m[24+i*self.stride:24+(i+1)*self.stride]
def cpu(s):
 c=[u32(s,o) for o in GPRS[:8]];fl=struct.unpack_from('<Q',s,2080)[0]&~0xcd5
 fl|=sum(s[o]<<bit for o,bit in zip(FLAGS,FBITS));return struct.pack('<10I',*c,fl,u32(s,GPRS[8]))
def project(s,c):
 c=struct.unpack('<10I',c)
 for o,v in zip(GPRS,c[:8]+c[9:]):p32(s,o,v)
 struct.pack_into('<Q',s,2080,c[8])
 for o,bit in zip(FLAGS,FBITS):s[o]=(c[8]>>bit)&1
def status(s):return (u16(s,2770)&0xb880)|sum(s[o]<<bit for o,bit in zip(SWPOS,SWBITS))
def tag(raw):
 m,e=struct.unpack('<QH',raw);e&=0x7fff
 return 1 if not e and not m else 2 if e==0x7fff or not e or not m>>63 else 0
def view(s):
 fx=bytearray(s[2768:3280]);sw=status(s);p16(fx,2,sw);fx[6:24]=bytes(18);top=(sw>>11)&7;ft=0xffff
 for i in range(8):
  raw=s[2486+i*16:2496+i*16];fx[32+i*16:42+i*16]=raw;fx[160+i*16:176+i*16]=s[16+i*64:32+i*64]
  phys=(top+i)&7
  if fx[4]&(1<<phys):ft=(ft&~(3<<(phys*2)))|(tag(raw)<<(phys*2))
 env=struct.pack('<7I',0xffff0000|u16(s,2768),0xffff0000|sw,0xffff0000|ft,u32(s,2776),u16(s,2780)|(u16(s,2774)<<16),u32(s,2784),0xffff0000|u16(s,2788))
 return cpu(s)+s+fx+env
def initial(t,fx=None,env=None,c=None):
 rep,inp,_,cw,top,depth,sticky,*_=t;s=bytearray((i*29+rep*71+inp*11+(i>>8)*7)&255 for i in range(3504));s[2112:2208]=bytes(96);p32(s,2168,0x7ffde000)
 for o,v in ((2090,0x2b),(2106,0x2b),(2110,0x23)):p16(s,o,v)
 if c is None:c=struct.pack('<10I',0x13579bdf,0x2468ace0,0x81726354,0x10293847,F,0x92837465,0x56473829,0xaabbccdd,0x202,ROOTPC)
 project(s,c)
 if fx is None:
  fx=bytearray(512);p16(fx,0,cw);p16(fx,2,(top<<11)|(0,2,34)[sticky]);p32(fx,24,0x1f80)
  for i in range(8):
   struct.pack_into('<QH',fx,32+16*i,0x8000000000000000+(i<<56),0x4000|(0x8000 if i%2 else 0))
   if i<depth:fx[4]|=1<<((top+i)&7)
  env=struct.pack('<7I',0xffff0000|cw,0xffff0000|u16(fx,2),0xffff0000,0x11223344,0x011d0023,0x55667788,0xffff002b)
 s[2768:3280]=fx;p16(s,2774,u16(env,18));p32(s,2776,u32(env,12));p16(s,2780,u16(env,16));p32(s,2784,u32(env,20));p16(s,2788,u16(env,24));sw=u16(fx,2)
 for o,bit in zip(SWPOS,SWBITS):s[o]=(sw>>bit)&1
 for i in range(8):s[2486+i*16:2496+i*16]=fx[32+i*16:42+i*16];s[16+i*64:32+i*64]=fx[160+i*16:176+i*16]
 return s
def promote(bits):
 sign=bits>>31;exp=(bits>>23)&255;frac=bits&0x7fffff;ie=int(exp==255 and frac!=0 and not frac&0x400000);de=int(exp==0 and frac!=0)
 if exp==255:m=(0x800000|frac)<<40;e=0x7fff;m|=0x4000000000000000 if frac else 0
 elif exp:m=(0x800000|frac)<<40;e=exp-127+16383
 elif frac:n=frac.bit_length();m=frac<<(64-n);e=n-1-149+16383
 else:m=e=0
 return struct.pack('<QH',m,e|(sign<<15)),bits|(0x400000 if ie else 0),ie,de
def expected(s,mem):
 s=bytearray(s);mem=bytearray(mem);incoming=struct.unpack('<10I',cpu(s));bits=u32(mem,memoff(0x78115004));raw,out,ie,de=promote(bits);top=(u16(s,2770)>>11)&7
 cp=bytearray(s);cc=list(incoming);cc[4]=F-12;cc[5]=F-12;cc[9]=0x4c1a09;project(cp,struct.pack('<10I',*cc));p16(cp,2770,(u16(cp,2770)&~0x3800)|(((top-1)&7)<<11));cp[2772]|=1<<((top-1)&7)
 cp[2755]|=ie;cp[2753]|=de
 for i in range(7,0,-1):cp[2486+i*16:2496+i*16]=s[2486+(i-1)*16:2496+(i-1)*16]
 cp[2486:2496]=raw;p16(cp,2774,0x105);p32(cp,2776,LEAF);p32(cp,2784,0x78115004);p16(cp,2780,0x23);p16(cp,2788,0x2b)
 after=bytearray(cp);ac=list(incoming);ac[4]=F+4;ac[9]=CAP;project(after,struct.pack('<10I',*ac));p16(after,2770,(u16(after,2770)&~0x3800)|(top<<11));after[2772]=s[2772]
 for i in range(7):after[2486+i*16:2496+i*16]=cp[2486+(i+1)*16:2496+(i+1)*16]
 after[2598:2608]=raw;p16(after,2774,0x11d);p32(after,2776,0x4c1a09);p32(after,2784,0x60b368)
 ev=[]
 def w(pc,a,v):p32(mem,memoff(a),v);ev.append((pc,a,v,4,1))
 def r(pc,a):ev.append((pc,a,u32(mem,memoff(a)),4,0))
 w(ROOTPC,F-4,incoming[5]);w(0x4c19f3,F-8,0x4c19f8);w(BODY,F-12,F-4);r(0x4c1a03,0x5bb4fc);w(0x4c1a03,F-16,0x4c1a09);r(LEAF,0x78115004);r(LEAF+6,F-16);w(0x4c1a09,0x60b368,out)
 for i in range(10):w(0x4c1a0f+i*10,0x60b36c+i*4,0)
 for pc,a in ((0x4c1a73,F-12),(0x4c1a74,F-8),(0x4c19f8,F-4),(0x4c19f9,F)):r(pc,a)
 routes=struct.pack('<15I',CAP,ROOTPC,CAP,0,1,0x4c19f3,BODY,0x4c19f8,0,1,0x4c1a03,0x5bb4fc,0x4c1a09,1,1)
 return view(after),view(cp),bytes(mem),b''.join(struct.pack('<5I',*e) for e in ev),routes
def check(n,before=None,mem=None):
 errors=[]
 def eq(label,a,b):
  if a!=b:errors.append(label)
 b=n[48:4132];s=b[40:3544];m=n[12300:28684]
 eq('BEFORE_CPU_FX_ENV_whole_State_coherence',b,view(s))
 if before is not None:eq('whole_expected_BEFORE_State',s,before)
 if mem is not None:eq('whole_expected_BEFORE_memory',m,mem)
 a,cp,ma,ev,rt=expected(s,m)
 eq('whole_protected_and_defined_State_CPU_FX_ENV',n[4132:8216],a);eq('actual_provider_checkpoint_complete_State_CPU_FX_ENV',n[8216:12300],cp);eq('ordered_stores_whole_four_pages',n[28684:45068],ma);eq('22_exact_source_memory_events',n[46148:46588],ev);eq('3_actual_r9_CALL_RET_routes',n[46588:46648],rt);eq('actual_complete_counts',struct.unpack_from('<8I',n,46648),(22,1,0,0,3,1,1,2));hb=n[45068:45580];ha=n[45580:46092];eq('direct_numerical_host_FX_before_cleanup',[hb[:5],hb[24:28]]+[hb[32+i*16:42+i*16] for i in range(8)],[ha[:5],ha[24:28]]+[ha[32+i*16:42+i*16] for i in range(8)]);eq('direct_host_BEFORE_CW_SW_tags_MXCSR',(u16(hb),u16(hb,2),hb[4],u32(hb,24)),(struct.unpack_from('<10I',n)[3],0x3a20,0x81,0x1f80));eq('direct_host_BEFORE_raw80',[hb[32+i*16:42+i*16] for i in range(8)],[struct.pack('<QH',0x8000000000000000+(i<<56),0x4000|(0x8000 if i%2 else 0)) for i in range(8)]);eq('direct_host_BEFORE_legacy_ENV',n[46092:46120],struct.pack('<7I',0xffff0000|struct.unpack_from('<10I',n)[3],0xffff3a20,0xffff3ffc,0x11223344,0x011d0023,0x55667788,0xffff002b));eq('direct_actual_host_ENV_before_cleanup',n[46092:46120],n[46120:46148]);return errors
def old_projected_memory(o,raw_iat):
 b=bytearray(o[2280:18664]);p32(b,memoff(0x5bb4fc),raw_iat);p32(b,memoff(F),CAP);return bytes(b)
def paired(o,n):
 e=[]
 def eq(k,a,b):
  if a!=b:e.append(k)
 eq('paired_tags',o[:40],n[:40]);eq('paired_before_CPU',o[40:80],n[48:88]);c=bytearray(o[80:120]);p32(c,36,CAP);eq('paired_after_CPU_broker_projection',bytes(c),n[4132:4172]);
 for name,oo,no in [('before',120,48),('after',632,4132)]:
  of=o[oo:oo+512];nf=n[no+3544:no+4056]
  # Hardware implementation storage and metadata are not silently masked.
  eq('hardware_zero_FX_metadata_'+name,of[6:24],bytes(18));eq('paired_meaningful_FX_'+name,[of[:5],of[24:28],of[160:288]]+[of[32+i*16:42+i*16] for i in range(8)],[nf[:5],nf[24:28],nf[160:288]]+[nf[32+i*16:42+i*16] for i in range(8)])
 eq('paired_full_legacy_ENV_before',o[2168:2196],n[48+4056:4132]);eq('paired_full_legacy_ENV_after',o[2196:2224],n[4132+4056:8216]);raw_iat=u32(n,12300+memoff(0x5bb4fc));eq('paired_four_whole_pages_before',old_projected_memory(o,raw_iat),n[12300:28684]);oa=bytearray(o[18664:35048]);p32(oa,memoff(0x5bb4fc),raw_iat);p32(oa,memoff(F),CAP);eq('paired_four_whole_pages_after',bytes(oa),n[28684:45068])
 c=o[35048:35764];cc=struct.pack('<10I',*(u32(c,x) for x in (176,172,168,164,196,180,160,156,192)),0x4c1a09);eq('measured_actual_checkpoint_CPU',cc,n[8216:8256]);of=c[204:716];nf=n[8216+3544:8216+4056];eq('measured_actual_checkpoint_FX',[of[:5],of[24:28],of[160:288]]+[of[32+i*16:42+i*16] for i in range(8)],[nf[:5],nf[24:28],nf[160:288]]+[nf[32+i*16:42+i*16] for i in range(8)]);eq('measured_debugger_trap_EIP',u32(c,184),0x4c1a0a);return e
def main():
 build=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();assert out.parent==ROOT/'reports/m4-fp-numeric-max-carry' and not out.exists();out.mkdir();bindings={};reports=[];control_count=0;scope_positive_count=0
 def bind(p):bindings[str(Path(p).resolve())]=sha(p)
 game=ROOT/'MW3/Mech3.exe';provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL';bind(game);bind(provider);game_bytes=game.read_bytes();provider_bytes=provider.read_bytes();assert sha(game)=='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf' and sha(provider)=='91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'
 fresh=bytearray(pe_page(game_bytes,BASES[0])+pe_page(provider_bytes,BASES[1])+pe_page(game_bytes,BASES[2])+bytes(4096));p32(fresh,memoff(F),CAP);raw_iat_admitted=u32(fresh,memoff(0x5bb4fc))
 schema=json.loads((build/'legacy-unit-O0/schema.json').read_text());assert schema['record_bytes']==46680 and schema['raw_offsets']==dict(tag=0,sequence=40,phase=44,**OFF);bind(build/'legacy-unit-O0/schema.json')
 for level in ('O0','O2'):
  native=Raw(build/f'legacy-unit-{level}/persistent.bin',b'MW4NMI01',46680);assert native.count==432;bind(native.path);fail=Counter();samples=[];carry=0
  for i in range(432):
   n=native.row(i);t=struct.unpack_from('<10I',n);seq,phase=struct.unpack_from('<2I',n,40);assert seq==i//2 and phase==i%2
   b=initial(t) if phase==0 else bytearray(native.row(i-1)[4172:7676])
   if phase:p32(b,2312,F);p32(b,2472,ROOTPC);carry+=1
   errors=check(n,bytes(b),bytes(fresh) if not phase else native.row(i-1)[28684:45068]);fail.update(errors)
   if errors and len(samples)<12:samples.append({'index':i,'differences':errors})
  reports.append({'level':level,'corpus':'persistent','records':432,'carry_boundaries':carry,'differences':dict(fail),'samples':samples})
  for mode in ('default','directed'):
   original=Raw(ROOT/f'reports/m4-fp-numeric-max/original-r5-normal-windows/{mode}.bin',b'MW4NMO01',35764);native=Raw(build/f'legacy-replay-{mode}-{level}/replay.bin',b'MW4NMI01',46680);assert native.count==original.count//2;bind(original.path);bind(native.path);fail=Counter();samples=[]
   for i in range(native.count):
    o=original.row(2*i+1);n=native.row(i);assert u32(o,8)==ROOTPC and struct.unpack_from('<2I',n,40)==(2*i+1,0);t=struct.unpack_from('<10I',o);s=initial(t,o[120:632],o[2168:2196],o[40:80]);errors=check(n,bytes(s),old_projected_memory(o,raw_iat_admitted))+paired(o,n);fail.update(errors)
    if errors and len(samples)<12:samples.append({'index':i,'tag':t,'differences':errors})
   reports.append({'level':level,'corpus':mode,'records':native.count,'differences':dict(fail),'samples':samples})
  # Separate causal corruptions of every native scope, plus a carried-dead-bank reset.
  sample=Raw(build/f'legacy-unit-{level}/persistent.bin',b'MW4NMI01',46680).row(1);previous=Raw(build/f'legacy-unit-{level}/persistent.bin',b'MW4NMI01',46680).row(0);expected_before=bytearray(previous[4172:7676]);p32(expected_before,2312,F);p32(expected_before,2472,ROOTPC)
  for off in (40,44,48,88,88+2065,88+2600,88+2776,4132,4172+3503,8216,8256+2772,12300+0x800,28684+16383,45580+24,46120+12,46148,46148+40,46588,46648):
   q=bytearray(sample);q[off]^=1;errors=check(q,bytes(expected_before),previous[28684:45068]);errors+=[] if struct.unpack_from('<2I',q,40)==(0,1) else ['sequence_order'];assert errors,(level,off);control_count+=1
  q=bytearray(sample);reset=initial(struct.unpack_from('<10I',sample));q[48:4132]=view(reset);assert check(q,bytes(expected_before),previous[28684:45068]);control_count+=1
  # Positive scope control: volatile SIMD and reserved FX storage may change.
  for off in (45580+400,45580+5,45580+500):
   q=bytearray(sample);q[off]^=1;assert not check(q,bytes(expected_before),previous[28684:45068]);scope_positive_count+=1
 report={'passed':not any(r['differences'] for r in reports),'scope':'New explicit Session-owned outer invoke numerical boundary; direct capture before harness cleanup; guest model and original BEFORE projections unchanged; full startup incomplete','comparisons':reports,'negative_controls':control_count,'whole_State_model':'Input-derived promotion, physical tags, logical ST shifts, CPU/legacy metadata; all other bytes protected from BEFORE','legacy_provenance':'Native software ENV from actual State, original actual FNSTENV28; debugger checkpoint FX separate. No native hardware guest ENV claim.','C1_scope':'Finite input-defined zero; special and C0/C2/C3/dead storage retained observations only. Native whole-State semantics separately predicted.','host_boundary':'Required Session.invoke status-return API catches internally then restores x87/raw80/legacy ENV/CW/status/MXCSR. Direct Runtime calls and construction/borrow exceptions outside it have no preservation claim. Volatile SIMD and reserved FX storage are observed only.', 'original_after_execution_inputs':False,'whole_M4_complete':False}
 report['scope_positive_controls']=scope_positive_count
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');bind(__file__);(out/'observer-source.py').write_bytes(Path(__file__).read_bytes());bind(out/'observer-source.py');(out/'pins.json').write_text(json.dumps({'files':bindings},indent=2)+'\n');print(json.dumps(report));assert report['passed']
if __name__=='__main__':main()
