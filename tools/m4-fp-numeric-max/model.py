"""Authored observation model, never a guest executable or service producer."""
import struct
CW=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
INPUTS=(0x7f7fffff,0,0x80000000,1,0x80000001,0x7fffff,0x800000,0x3f800000,0xbf800000,0x3eaaaaab,0xff7fffff,0x7f800000,0xff800000,0x7fc12345,0x7f812345,0xff812345)
BASES=(0x5bb000,0x78115000,0x60b000,0x20001000)
FRAME=0x20001800;RETURN=0x10000100
GPRS=(2216,2248,2264,2232,2312,2328,2280,2296,2472)
INITIAL=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,FRAME,0x92837465,0x56473829,0xaabbccdd,0x202)
def get32(b,p):return struct.unpack_from('<I',b,p)[0]
def tag(b):return struct.unpack_from('<10I',b)
def schedule(directed):
 for rep in range(2):
  for inp in range(16 if directed else 1):
   for depth in (0,1,7):
    for sticky in (0,1,2):
     for cw in CW:
      for top in (0,7):
       for entry in (0x780c10f0,0x4c19f0):yield (rep,inp,entry,cw,top,depth,sticky,0,1,int(entry==0x4c19f0))
def seed_fx(t):
 _,_,_,cw,top,depth,sticky,*_=t;b=bytearray(512);sw=(top<<11)|(0 if sticky==0 else 2 if sticky==1 else 34);struct.pack_into('<HH',b,0,cw,sw);struct.pack_into('<I',b,24,0x1f80)
 for i in range(8):
  struct.pack_into('<QH',b,32+16*i,0x8000000000000000+(i<<56),0x4000|(0x8000 if i%2 else 0))
  if i<depth:b[4]|=1<<((top+i)&7)
 return b
def seed_state(t):
 rep,inp,entry,*_=t;b=bytearray((i*29+rep*71+inp*11+(i>>8)*7)&255 for i in range(3504));b[2112:2208]=bytes(96)
 for p,v in ((2090,0x2b),(2106,0x2b),(2110,0x23)):struct.pack_into('<H',b,p,v)
 cpu=INITIAL+(entry,)
 for p,v in zip(GPRS,cpu[:8]+cpu[9:]):struct.pack_into('<I',b,p,v)
 struct.pack_into('<Q',b,2080,0x202)
 for p in (2065,2067,2069,2071,2073,2075,2077):b[p]=0
 fx=seed_fx(t);b[2768:3280]=fx
 struct.pack_into('<H',b,2774,0x11d);struct.pack_into('<I',b,2776,0x11223344);struct.pack_into('<H',b,2780,0x23);struct.pack_into('<I',b,2784,0x55667788);struct.pack_into('<H',b,2788,0x2b)
 sw=struct.unpack_from('<H',fx,2)[0]
 for p,bit in ((2737,8),(2739,9),(2741,10),(2743,14),(2745,5),(2747,4),(2749,3),(2751,2),(2753,1),(2755,0),(2757,6)):b[p]=(sw>>bit)&1
 for i in range(8):b[2486+16*i:2496+16*i]=fx[32+16*i:42+16*i];b[16+64*i:32+64*i]=bytes(16)
 return b
def observed_state(before,cpu,fx,env):
 b=bytearray(before);c=struct.unpack('<10I',cpu)
 for p,v in zip(GPRS,c[:8]+c[9:]):struct.pack_into('<I',b,p,v)
 sw=struct.unpack_from('<H',fx,2)[0];old=struct.unpack_from('<H',b,2770)[0];struct.pack_into('<H',b,2770,(old&~0x3800)|(sw&0x3800));b[2772]=fx[4]
 for p,bit in ((2737,8),(2739,9),(2741,10),(2743,14),(2745,5),(2747,4),(2749,3),(2751,2),(2753,1),(2755,0),(2757,6)):b[p]=(sw>>bit)&1
 for i in range(8):b[2486+16*i:2496+16*i]=fx[32+16*i:42+16*i]
 b[2774:2776]=env[18:20];b[2776:2780]=env[12:16];b[2780:2782]=env[16:18];b[2784:2788]=env[20:24];b[2788:2790]=env[24:26]
 return bytes(b)
def checkpoint_cpu(c):return struct.pack('<10I',*(get32(c,o) for o in (176,172,168,164,196,180,160,156,192)),0x4c1a09)
def memory_offset(a):
 base=a&~4095;assert base in BASES;return BASES.index(base)*4096+(a&4095)
def events(original):
 b=bytearray(original[2280:18664]);out=[];leaf=tag(original)[2]==0x780c10f0
 def r(a):v=get32(b,memory_offset(a));out.append((a,v,4,0));return v
 def w(a,v):struct.pack_into('<I',b,memory_offset(a),v);out.append((a,v,4,1))
 if leaf:r(0x78115004);r(FRAME)
 else:
  w(FRAME-4,INITIAL[5]);w(FRAME-8,0x4c19f8);w(FRAME-12,FRAME-4);r(0x5bb4fc);w(FRAME-16,0x4c1a09);r(0x78115004);r(FRAME-16)
  w(0x60b368,get32(original,18664+memory_offset(0x60b368)))
  for a in range(0x60b36c,0x60b394,4):w(a,0)
  for a in (FRAME-12,FRAME-8,FRAME-4,FRAME):r(a)
 assert bytes(b)==original[18664:35048],'Ordered bus replay failed to produce actual whole pages'
 return out
def cpu_frame(esp,ebp,pc):c=list(INITIAL)+[pc];c[4]=esp;c[5]=ebp;return struct.pack('<10I',*c)
def routes(original):
 if tag(original)[2]==0x780c10f0:return bytes(192)
 c=checkpoint_cpu(original[35048:35764]);return struct.pack('<4I',0x4c1a00,0x4c19f8,0,1)+cpu_frame(FRAME-8,FRAME-4,0x4c1a00)+cpu_frame(FRAME-4,FRAME-4,0x4c19f8)+struct.pack('<4I',0x780c10f0,0x4c1a09,0,1)+cpu_frame(FRAME-16,FRAME-12,0x780c10f0)+c
def fixture(pack,t):
 b=bytearray().join(pack[12+i*4104+8:12+(i+1)*4104] for i in (3,4,5,6));struct.pack_into('<I',b,memory_offset(0x78115004),INPUTS[t[1]]);b[memory_offset(0x60b368):memory_offset(0x60b368)+44]=b'\xa5'*44;struct.pack_into('<I',b,memory_offset(FRAME),RETURN);return bytes(b)
def fx_arch(f):return [f[:5],f[24:28]]+[f[32+i*16:42+i*16] for i in range(8)]+[f[160:288]]
def checks(o,n,paired_leaf=None,pack=None):
 errors=[]
 def eq(name,a,b):
  if a!=b:errors.append(name)
 t=tag(o);base=seed_state(t);eq('actual_before_CPU_fixture',o[40:80],struct.pack('<10I',*(INITIAL+(t[2],))));eq('actual_before_FX_fixture',fx_arch(o[120:632]),fx_arch(seed_fx(t)))
 fx=seed_fx(t);sw=struct.unpack_from('<H',fx,2)[0];tags=0xffff
 for phys in range(8):
  if fx[4]&(1<<phys):tags&=~(3<<(phys*2))
 env=struct.pack('<7I',0xffff0000|t[3],0xffff0000|sw,0xffff0000|tags,0x11223344,0x011d0023,0x55667788,0xffff002b);eq('actual_before_ENV_fixture',o[2168:2196],env)
 if pack is not None:eq('actual_whole_memory_fixture',o[2280:18664],fixture(pack,t))
 eq('actual_after_CPU_frame',o[80:120],cpu_frame(FRAME+4,INITIAL[5],RETURN));eq('native_all16_host_XMM_restored',n[1304:1560],n[1816:2072]);eq('entire_seeded_State',bytes(base),n[35764:39268]);eq('whole_defined_and_protected_State',observed_state(base,o[80:120],o[632:1144],o[2196:2224]),n[39268:42772])
 expected=events(o);packed=b''.join(struct.pack('<4I',*e) for e in expected);eq('ordered_typed_memory_events',n[46888:47240],packed+bytes(352-len(packed)))
 leaf=t[2]==0x780c10f0;eq('typed_counts',struct.unpack_from('<8I',n,46856),(2,2,0,0,0,1,0,0) if leaf else (22,7,15,1,1,3,2,0));eq('real_CALL_RET_routes',n[47240:47432],routes(o));eq('native_no_counterfeit_CONTEXT',n[35048:35764],bytes(716))
 if leaf:eq('unused_native_checkpoint',n[42772:46856],bytes(4084));eq('actual_leaf_no_checkpoint',o[35048:35764],bytes(716))
 else:
  assert paired_leaf is not None
  context=o[35048:35764];fx=context[204:716];cp=checkpoint_cpu(context);env=paired_leaf[2196:2224]
  eq('provider_ST0_return_raw80',fx[32:42],paired_leaf[664:674]);eq('physical_provider_push_tags',fx[4],paired_leaf[636]);eq('connected_checkpoint_State',observed_state(base,cp,fx,env),n[43352:46856]);eq('checkpoint_legacy_paired_inference',env,n[43324:43352])
 return errors
