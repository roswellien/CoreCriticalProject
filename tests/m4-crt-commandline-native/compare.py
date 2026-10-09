"""Actual own OS inputs and typed address-domain relational observer, not a worker."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-commandline-native'
SIZE=56456;CW=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
CPU=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,0x202,0x7800188c)
GPR=(2216,2248,2264,2232,2312,2328,2280,2296);AF=((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))
FX=4588;ENV=7660;MB=7828;MA=28308;SB=48788;SA=52292;ROUTE=55796;EV=55816

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,msg):
 if not ok:raise AssertionError(msg)
def equal(a,b,msg):
 if a!=b:
  if isinstance(a,(bytes,bytearray)) and len(a)==len(b):msg+=f' firstbyte{next(i for i,(x,y) in enumerate(zip(a,b)) if x!=y)}'
  raise AssertionError(msg)
def words(b,o,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def put(b,o,v):struct.pack_into('<I',b,o,v&0xffffffff)
def initialfx(cw,top,metadata):
 b=bytearray(512);struct.pack_into('<HH',b,0,cw,top<<11);put(b,24,0x1f80)
 for i in range(8):b[32+i*16:42+i*16]=bytes((17+i*13+j*7)&255 for j in range(10))
 b[160:288]=bytes((i*19+3)&255 for i in range(128))
 if metadata:struct.pack_into('<H',b,6,0x11d);put(b,8,0x11223344);struct.pack_into('<H',b,12,0x23);put(b,16,0x55667788);struct.pack_into('<H',b,20,0x2b)
 return b
def env(cw,top):return struct.pack('<7I',0xffff0000|cw,0xffff0000|(top<<11),0xffffffff,0x11223344,0x11d0023,0x55667788,0xffff002b)
def state_seed(cw,top,repeat):
 b=bytearray((i*29+cw+repeat*3571+(i>>8)*7)&255 for i in range(3504));b[2112:2208]=bytes(96);put(b,2168,0x7ffde000)
 for o in (2090,2094,2106):struct.pack_into('<H',b,o,0x2b)
 struct.pack_into('<H',b,2110,0x23);b[2768:3280]=initialfx(cw,top,True)
 for i in range(8):b[2486+16*i:2496+16*i]=b[2800+16*i:2810+16*i];b[16+64*i:32+64*i]=b[2928+16*i:2944+16*i]
 for o in (2737,2739,2741,2743,2745,2747,2749,2751,2753,2755,2757):b[o]=0
 for o,v in zip(GPR,CPU):put(b,o,v)
 put(b,2472,CPU[9]);struct.pack_into('<Q',b,2080,CPU[8])
 for o,bit in AF:b[o]=(CPU[8]>>bit)&1
 return b
def pe_reader(data):
 def u(o):return words(data,o)[0]
 p=u(0x3c);equal(data[p:p+4],b'PE\0\0','PE signature');count=struct.unpack_from('<H',data,p+6)[0];os=struct.unpack_from('<H',data,p+20)[0];op=p+24;magic=struct.unpack_from('<H',data,op)[0];require(magic in(0x10b,0x20b),'PE32/64');base=u(op+28) if magic==0x10b else struct.unpack_from('<Q',data,op+24)[0]
 sections=[words(data,op+os+i*40+8,8) for i in range(count)]
 def get(r,n):
  matches=[s for s in sections if s[1]<=r and r+n<=s[1]+s[2]];require(len(matches)==1,'Complete PE file-backed span');s=matches[0];return data[s[3]+r-s[1]:s[3]+r-s[1]+n]
 export=words(data,op+(96 if magic==0x10b else 112),2)
 def named(name):
  e=words(get(export[0],40),0,10);found=[]
  for i in range(e[6]):
   nr=words(get(e[8]+4*i,4),0)[0];s=bytearray()
   for j in range(4096):
    c=get(nr+j,1)[0]
    if not c:break
    s.append(c)
   if s.decode('ascii')==name:
    slot=struct.unpack('<H',get(e[9]+2*i,2))[0];require(slot<e[5],'Export ordinal bounds');found.append(words(get(e[7]+4*slot,4),0)[0])
  require(len(found)==1,'Unique actual named Windows export');require(not(export[0]<=found[0]<sum(export)),'Recorded target cannot be forwarder text');return found[0]
 return base,get,named
API_CACHE={}
def api(b,o,native):
 raw=b[o:o+2184];target,named,owner,owner_named=struct.unpack_from('<4Q',raw)
 require(target==named==owner_named and owner<target,'Coherent actual target/named-owner association');rb,sz,ra,state,typ,protect,ap=struct.unpack_from('<3Q4I',raw,32);require(ra==owner and rb<=target<rb+sz and state==0x1000 and typ==0x1000000 and protect&0xf0 and not(protect&0x101),'Actual target RX loaded-image region')
 hs=raw[72:136].decode('ascii');path=raw[136:].decode('utf-16-le').split('\0')[0];require(path and len(hs)==64 and raw[136+2*len(path):]==bytes(2048-2*len(path)),'Bounded zero-padded API path')
 disk=Path(path)
 # A WOW6432 module reports its logical System32 path. The32-bit file open
 # in its worker redirected to SysWOW64; this64-bit observer binds that file.
 if not native and '/system32/' in str(disk).replace('\\','/').lower():disk=Path(str(disk).replace('System32','SysWOW64').replace('system32','SysWOW64'))
 key=(str(disk),hs)
 if key not in API_CACHE:
  require(disk.is_file(),'Measured API path readable actual owning file');equal(sha(disk),hs,'Current owning provider file identity');data=disk.read_bytes();base,get,nm=pe_reader(data);API_CACHE[key]=(nm('GetCommandLineA'),str(disk),hs)
 rva,_,_=API_CACHE[key];equal(target-owner,rva,'Actual loaded pointer matches exact named disk export RVA');require((target<=0xffffffff)==(not native),'Observed API pointer architecture');return raw

def stream(path,native):
 b=Path(path).read_bytes();equal(b[:8],b'MW4CMNN1' if native else b'MW4CMNO1','Stream magic');v,count,size,pages,ns,na=words(b,8,6);equal((v,count,size,pages),(1,48,SIZE,5),'Stream framing');at=32;sup=b[at:at+ns];at+=ns;observed=b[at:at+na];at+=na;require(observed and observed[-1]==0 and b'\0' not in observed[:-1] and na<=131072,'Actual bounded OS input');rows=[]
 for i in range(count):
  raw=b[at:at+SIZE];at+=SIZE;require(len(raw)==SIZE,'Full raw record');nb,nr=words(raw,28,2);require(nb==na and 0<nr<65536,'Per-record input/region extent');regions=b[at:at+nr*40];at+=nr*40;owned=b[at:at+nb];at+=nb;rows.append((raw,regions,owned))
 equal(at,len(b),'No trailing/short records');return sup,observed,rows

def validate(row,index,native,pages,worker_pe):
 b,regions,owned=row;repeat=index//24;cw=CW[(index%24)//2];top=(0,7)[index%2];tags=words(b,0,13);equal(tags[:7],(index,repeat,cw,top,int(native),0,1),'Tag/case/host restoration');equal(tags[7],len(owned),'Own buffer byte count');equal(tags[8]*40,len(regions),'Own source region count');equal(tags[9],0x78037174,'Actual data-import resulting global');ptr=struct.unpack_from('<Q',b,212)[0];v=tags[10];equal(v,0x33000000 if native else ptr,'Explicit guest/host address-domain output');equal(tags[11:],(5 if native else 0,1),'Native events/authored capture');require(ptr and (native or ptr<=0xffffffff),'Actual host pointer width')
 a0=api(b,220,native);equal(a0,api(b,2404,native),'API association unchanged before/after actual query')
 end=ptr
 for i in range(len(regions)//40):
  start,n,allocation,state,typ,p,ap=struct.unpack_from('<3Q4I',regions,40*i);require(start<=end<start+n and state==0x1000 and p&0xee and not(p&0x101) and allocation<=start,'Original/native source readable region coverage');end=start+n
 require(ptr+len(owned)<=end and owned[-1]==0 and b'\0' not in owned[:-1],'Actual own OS bytes complete/terminated')
 before=words(b,52,10);after=words(b,92,10);svb=words(b,132,10);sva=words(b,172,10);equal(before,CPU,'Complete actual input CPU');c=list(CPU);c[4]-=4;c[9]=0x10000200;equal(svb,tuple(c),'Actual compiled/broker service incoming CALL frame');c[0]=v
 if native:c[4]+=4;c[9]=0x78001892;equal(sva,tuple(c),'Native service representative/actual return policy')
 else:
  for j in(0,3,4,5,6,7):equal(sva[j],c[j],'Original real service defined CPU');require(not(sva[8]&0x400),'Original DF clear');equal(sva[9],0x10000200,'Original transport capture PC')
 c=list(sva);c[4]=0x20001800;c[9]=0x10000100;equal(after,tuple(c),'Actual returned pointer/source store/final continuation CPU')
 equal(words(b,ROUTE,5),(0x10000200,0x78001892,0x200017fc,0x20001800,1),'Actual CALL/RET0/authored capture route')
 initial=bytearray(pages)
 if not native:put(initial,4096+0x34,0x10000200)
 initial+=bytes([0xa5])*4096;put(initial,16384+0x800,0x10000100);equal(b[MB:MA],initial,'Whole five initial source/provider/data-IAT/stack pages')
 final=bytearray(initial);put(final,8192+0x174,v);put(final,16384+0x7fc,0x78001892)
 if not native:
  ret=words(b,MA+16384+0x7f8)[0];base,get,nm=worker_pe;equal(get(ret-base-6,2),b'\xff\x15','Actual original inner API transport CALL encoding');require(ret>base and ret<base+0x200000,'Original transport return points into actual worker');put(final,16384+0x7f8,ret)
 equal(b[MA:SB],final,'Whole final five pages / source writes / declared original transport slot')
 for i in range(8):equal(b[FX+1024+32+i*16:FX+1024+42+i*16],b[FX+1536+32+i*16:FX+1536+42+i*16],'Full host raw80 restoration')
 equal(b[FX+1024:FX+1029],b[FX+1536:FX+1541],'Host FP core restoration');equal(b[FX+1048:FX+1052],b[FX+1560:FX+1564],'Host MXCSR restoration');equal(b[FX+1184:FX+1184+(256 if native else 128)],b[FX+1696:FX+1696+(256 if native else 128)],'Host SIMD restoration');equal(b[ENV+56:ENV+84],b[ENV+84:ENV+112],'Host full legacy ENV restoration')
 if native:
  f=initialfx(cw,top,True);equal(b[FX:FX+512],f,'Full native input software FX projection');equal(b[FX+512:FX+1024],f,'Full native output software FX representative policy');seed=state_seed(cw,top,repeat);equal(b[SB:SA],seed,'Full seeded3504 State');put(seed,2216,v);put(seed,2472,0x10000100);equal(b[SA:ROUTE],seed,'Full final3504 State/opaque/upperGPR preservation')
  events=[words(b,EV+j*20,5) for j in range(5)];equal(events,[(0x7800188c,0x7802e034,0x3442e,4,0),(0x7800188c,0x200017fc,0x78001892,4,1),(0x7800188c,0x200017fc,0x78001892,4,0),(0x7800188c,0x33000000,0,len(owned),2),(0x78001892,0x78037174,0x33000000,4,1)],'Five ordered actual native semantic/transfer events');equal(b[EV+100:],bytes(540),'Unused event storage')
 else:
  f=initialfx(cw,top,False);f[28:32]=b[FX+28:FX+32];require(words(f,28)[0]!=0,'Original separate actual FX MXCSR-mask');equal(b[FX:FX+512],f,'Full original actual hardware FX before');equal(b[FX+512:FX+1024],b[FX+2560:FX+3072],'Original actual API FX carried through source MOV');equal(b[FX:FX+512],b[FX+2048:FX+2560],'Original actual service incoming FX');equal(b[SB:ROUTE],bytes(7008),'Original software State unobserved');equal(b[EV:],bytes(640),'Original access events unobserved')
 for o in(ENV,ENV+28):equal(b[o:o+28],env(cw,top),'Separate input/output guest legacy ENV')
 for o in(ENV+112,ENV+140):equal(b[o:o+2]+b[o+4:o+6],b[FX+2048+(0 if o==ENV+112 else 512):FX+2052+(0 if o==ENV+112 else 512)],'Separate real API/helper hardware CW/SW ENV representation')
 return tags

def main(capture,out):
 out=Path(out);require(not out.exists(),'Fresh comparison report');out.mkdir();capture=Path(capture);cmd=json.loads((capture/'capture.json').read_text());require(cmd['passed'],'Complete actual capture');p=ROOT/'tools/analysis/pe.py';s=importlib.util.spec_from_file_location('cmd_model_pe',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);game=m.PEImage((ROOT/'MW3/Mech3.exe').read_bytes());at,_=game.rva_range(0x1bb000,4096);gamepage=game.data[at:at+4096];pack=(BASE/'static-r1/pack.bin').read_bytes();pages=b''.join(pack[20+i*4104:4116+i*4104] for i in range(3))+gamepage
 exe=next(x['executable'] for x in cmd['commands'] if x['kind']=='original');worker_pe=pe_reader(Path(exe).read_bytes());counts={'original':0,'native':0};alterations=[];controls=[];positives=[];passed=False
 try:
  for index in range(8):
   supplied,observed,original=stream(capture/f'original-{index}.bin',False);equal(supplied.decode(),cmd['commands'][index*3]['supplied_logical_commandline'],'Actual supplied logical input identity')
   for j,row in enumerate(original):validate(row,j,False,pages,worker_pe);equal(row[2],observed,'Original own OS bytes');counts['original']+=1
   if index==0:
    for label,offset in [('initialCPU',52),('definedEAX',92),('finalESP',108),('CALLesp',148),('APIreturn',172),('actualGlobal',MA+8192+0x174),('rawGameIAT',MA+12288),('actualCALLword',MA+16384+0x7fc),('innerTransport',MA+16384+0x7f8),('legacyCarry',ENV+28),('hostENV',ENV+84),('originalStateUnobserved',SB),('originalEventsUnobserved',EV),('volatileCarry',96)]:
     raw,reg,owned=original[0];mut=bytearray(raw);mut[offset]^=1
     try:validate((mut,reg,owned),0,False,pages,worker_pe)
     except AssertionError as e:controls.append(dict(level='original',label=label,rejected=True,reason=str(e)))
     else:raise AssertionError('Original observer mutation accepted '+label)
    for label,offsets in [('coherentECX',(176,96)),('coherentEDX',(180,100)),('coherentArithmeticZF',(204,124)),('coherentSIMD0',(FX+2560+160,FX+512+160))]:
     raw,reg,owned=original[0];mut=bytearray(raw)
     for offset in offsets:mut[offset]^=0x40 if label=='coherentArithmeticZF' else 1
     validate((mut,reg,owned),0,False,pages,worker_pe);positives.append(dict(label=label,accepted=True,scope='Unconsumed actual original volatility coherent carry; no fixed equality to native'))
   for level in('O0','O2'):
    ns,no,rows=stream(capture/f'{level}-{index}.bin',True);equal(ns,supplied,'Same independently supplied logical input');alterations.append(dict(index=index,level=level,original_matches_logical=observed[:-1]==supplied,native_matches_logical=no[:-1]==ns,actual_original_native_equal=observed==no,original_observed_sha256=hashlib.sha256(observed).hexdigest(),native_observed_sha256=hashlib.sha256(no).hexdigest()))
    for j,row in enumerate(rows):validate(row,j,True,pages,worker_pe);equal(row[2],no,'Native actual owning snapshot bytes');counts['native']+=1
    if index==0:
     for label,offset in [('initialCPU',52),('outputPointer',92),('nonvolatile',104),('CALLesp',148),('serviceReturn',172),('hostPointer',219),('APIexport',228),('APIowner',236),('APIdiskhash',292),('APIpath',356),('seedCW',FX),('legacyEnv',ENV),('hostENV',ENV+84),('wholeIAT',MA+4096),('globalStore',MA+8192+0x174),('CALLstore',MA+16384+0x7fc),('opaqueState',SA+1),('upperGPR',SA+2220),('softwareVector',SA+16),('eventOrder',EV),('eventValue',EV+8),('eventCount',44),('unusedEvent',EV+101),('actualCapture',48)]:
      raw,reg,owned=rows[0];mut=bytearray(raw);mut[offset]^=1
      try:validate((mut,reg,owned),0,True,pages,worker_pe)
      except AssertionError as e:controls.append(dict(level=level,label=label,rejected=True,reason=str(e)))
      else:raise AssertionError('Observer mutation accepted '+label)
     for label,change in [('ownBuffer',1),('sourceRegion',2)]:
      raw,reg,owned=rows[0];owned=bytearray(owned);reg=bytearray(reg)
      if change==1:owned[-1]^=1
      else:reg[24]^=1
      try:validate((raw,reg,owned),0,True,pages,worker_pe)
      except AssertionError as e:controls.append(dict(level=level,label=label,rejected=True,reason=str(e)))
      else:raise AssertionError('Observer mutation accepted '+label)
  passed=True
 finally:
  (out/'report.json').write_text(json.dumps(dict(passed=passed,counts=counts,observed_input_differences=alterations,observer_controls=controls,coherent_unspecified_positives=positives,scope='Per-process own-input writer/store/CALL/data results with typed pointer domains; native full3504 State representative policy; actual original volatility/FP observations; no full attach/menu',script_sha256=sha(__file__),capture_manifest_sha256=sha(capture/'capture.json'),owning_windows_files=list(API_CACHE.values()),input_files={str(p):sha(p) for p in capture.iterdir() if p.is_file()}),indent=2))
 print(json.dumps(dict(passed=passed,counts=counts,observer_controls=len(controls))))
if __name__=='__main__':main(*sys.argv[1:])
