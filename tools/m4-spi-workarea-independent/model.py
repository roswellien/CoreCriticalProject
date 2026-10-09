"""Independent byte model, using only Python's standard library."""
from pathlib import Path
import struct,hashlib,json,traceback
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m4-spi-workarea/independent-review-r1/raw-r3'
CW=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
FRAME=0x20001800;ENTRY=0x482cf0;OBJECT=0x608f88;OUTPUT=OBJECT+24;RET=0x482ff0;CALL=0x482cdd;RESUME=0x482ce3;IAT=0x5bb6dc
def require(b,w):
    if not b:raise AssertionError(w)
def sha(b):return hashlib.sha256(b).hexdigest()
def w(b,o,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def u16(b,o):return struct.unpack_from('<H',b,o)[0]
def u32(b,o):return w(b,o)[0]
def put(b,o,v,n=4):b[o:o+n]=v.to_bytes(n,'little')

class PE:
    def __init__(self,b):
        self.b=b;require(b[:2]==b'MZ','DOS');pe=u32(b,60);require(b[pe:pe+4]==b'PE\0\0','PE signature')
        self.machine=u16(b,pe+4);self.opt=pe+24;self.magic=u16(b,self.opt)
        require(self.magic in (0x10b,0x20b),'PE optional format')
        self.base=u32(b,self.opt+28) if self.magic==0x10b else int.from_bytes(b[self.opt+24:self.opt+32],'little')
        self.dirs=self.opt+(96 if self.magic==0x10b else 112);self.sections=[]
        for i in range(u16(b,pe+6)):
            o=self.opt+u16(b,pe+20)+40*i;vs,va,rs,rp=w(b,o+8,4);require(rp+rs<=len(b),'section bounds');self.sections.append((va,vs,rs,rp,u32(b,o+36)))
    def offset(self,r,n=1):
        for va,vs,rs,rp,flags in self.sections:
            if va<=r and r+n<=va+rs:return rp+r-va
        raise AssertionError('unbacked RVA '+hex(r))
    def bytes(self,r,n):o=self.offset(r,n);return self.b[o:o+n]
    def mapped(self,r,n):
        for va,vs,rs,rp,flags in self.sections:
            if va<=r and r+n<=va+max(vs,rs):
                off=r-va;raw=max(0,min(n,rs-off));return self.b[rp+off:rp+off+raw]+bytes(n-raw)
        raise AssertionError('unmapped RVA')
    def string(self,r):o=self.offset(r);end=self.b.index(0,o);require(end-o<4096,'name bounds');return self.b[o:end].decode('ascii')
    def import_owner(self,slot):
        require(self.magic==0x10b,'import PE32');r,size=w(self.b,self.dirs+8,2)
        for j in range(0,size,20):
            orig,ts,chain,name,iat=w(self.b,self.offset(r+j,20),5)
            if not any((orig,ts,chain,name,iat)):break
            for i in range(65536):
                value=u32(self.b,self.offset((orig or iat)+4*i,4))
                if not value:break
                if self.base+iat+4*i==slot:return self.string(name),self.string(value+2),u32(self.b,self.offset(iat+4*i,4))
        raise AssertionError('missing import owner')
    def export(self,name):
        r,size=w(self.b,self.dirs,2);o=self.offset(r,40);base,nf,nn,fa,na,oa=w(self.b,o+16,6)
        for i in range(nn):
            if self.string(u32(self.b,self.offset(na+4*i,4)))==name:
                index=u16(self.b,self.offset(oa+2*i,2));require(index<nf,'export index');value=u32(self.b,self.offset(fa+4*index,4));return base+index,value,r<=value<r+size
        raise AssertionError('missing export')

def cpu(v):return [0x13579bdf+v,0x2468ace0+v,0x81726354+v,0x10293847+v,FRAME,0x92837465+v,0x56473829+v,0xaabbccdd+v,[0x202,0xad7,0x293][v],ENTRY]
def fxseed(cw,top,v):
    b=bytearray(512);put(b,0,cw,2);put(b,2,top<<11,2);put(b,24,0x1f80)
    for i in range(128):b[160+i]=(i*13+v*17)&255
    return b
def envseed(cw,top):
    b=bytearray(28)
    for o,value in [(0,cw),(2,0xffff),(4,top<<11),(6,0xffff),(8,0xffff),(10,0xffff),(26,0xffff)]:put(b,o,value,2)
    return b
GPR=(2216,2248,2264,2232,2312,2328,2280,2296,2472)
def state_seed(cw,top,v,repeat):
    b=bytearray((i*29+cw+v*91+repeat*3571+(i>>8)*7)&255 for i in range(3504))
    b[2112:2208]=bytes(96);put(b,2168,0x7ffde000)
    for o,s in [(2110,0x23),(2106,0x2b),(2094,0x2b),(2090,0x2b)]:put(b,o,s,2)
    f=fxseed(cw,top,v);b[2768:3280]=f
    for i in range(8):b[2486+16*i:2496+16*i]=bytes(10);b[16+64*i:32+64*i]=f[160+16*i:176+16*i]
    for o in range(2737,2758,2):b[o]=0
    c=cpu(v)
    for o,value in zip(GPR,c[:8]+c[9:]):put(b,o,value)
    put(b,2080,c[8],8)
    for o,bit in zip(range(2065,2078,2),(0,2,4,6,7,10,11)):b[o]=(c[8]>>bit)&1
    return b
def pages_before(source,v):
    obj=bytearray(4096)
    if v:obj=bytearray((i*37+v*71+(i>>8)*5)&255 for i in range(4096))
    stack=bytearray(b'\xa5'*4096);put(stack,0x800,RET)
    return bytearray(source)+obj+stack
def memory_after(before,v,rect):
    b=bytearray(before);s=cpu(v)
    b[4096+0xf88:4096+0xfa0]=b[:24];b[4096+0xfa0:4096+0xfb0]=rect
    for off,value in [(0x7fc,s[3]),(0x7f8,s[6]),(0x7f4,s[7]),(0x7f0,0),(0x7ec,OUTPUT),(0x7e8,0),(0x7e4,0x30),(0x7e0,RESUME)]:put(b,8192+off,value)
    return b
def host_restore(r,native):
    before=r[1140:1652];after=r[1652:2164]
    require(before[:5]==after[:5] and before[24:28]==after[24:28],'restored host x87 core/MXCSR')
    for i in range(8):require(before[32+16*i:42+16*i]==after[32+16*i:42+16*i],'restored host raw80')
    require(before[160:160+(256 if native else 128)]==after[160:160+(256 if native else 128)],'restored host SIMD')
    require(r[2220:2248]==r[2248:2276],'restored whole host legacy ENV')
def events(before,v,rect):
    rows=[];c=cpu(v)
    def e(pc,a,value,op):rows.append((pc,a,value,4,op))
    for pc,a,value in [(0x482cc0,FRAME-4,c[3]),(0x482cc3,FRAME-8,c[6]),(0x482cc4,FRAME-12,c[7]),(0x482cc8,FRAME-16,0),(0x482cd6,FRAME-20,OUTPUT),(0x482cd7,FRAME-24,0),(0x482cd9,FRAME-28,0x30)]:e(pc,a,value,1)
    for i in range(6):value=u32(before,4*i);e(0x482cdb,0x5e6000+4*i,value,0);e(0x482cdb,OBJECT+4*i,value,1)
    e(CALL,FRAME-32,RESUME,1);e(CALL,IAT,0x1df20c,0)
    for i,value in enumerate((RESUME,0x30,0,OUTPUT,0)):e(CALL,FRAME-32+4*i,value,0)
    for i in range(4):e(CALL,OUTPUT+4*i,u32(rect,4*i),1)
    for pc,a,value in [(RESUME,FRAME-12,c[7]),(0x482ce6,FRAME-8,c[6]),(0x482ce7,FRAME-4,c[3]),(0x482ce8,FRAME,RET)]:e(pc,a,value,0)
    require(len(rows)==34,'complete event schedule');return rows

def check_record(r,index,native,source):
    repeat=index//72;cw=CW[(index%72)//6];top=(0,7)[(index%6)//3];v=index%3
    require(w(r,0,9)==(index,repeat,cw,top,v,0,1,int(native),0x2f9),'record tags/domain')
    c=cpu(v);require(list(w(r,36,10))==c,'whole input CPU')
    sb=list(w(r,33860,10));sa=list(w(r,33900,10));called,result,cleanup,pbefore,pafter=w(r,35052,5)
    service_before=[OUTPUT,0,c[2],OBJECT,FRAME-32,c[5],0x5e6018,OUTPUT,c[8],CALL]
    require(sb==service_before,'complete service-entry CPU')
    require(called==1 and cleanup==16 and sa[0]==result,'actual BOOL and logical cleanup')
    require([sa[i] for i in (3,4,5,6,7,9)]==[OBJECT,FRAME-12,c[5],0x5e6018,OUTPUT,RESUME] and not(sa[8]&0x400),'nonvolatile service return and forward DF')
    if native:
        require(sa[1]==0 and sa[2]==c[2] and sa[8]==c[8] and pbefore==pafter==0,'native representative policy/separate x64 host ABI')
    else:require(pbefore>0 and pbefore+20==pafter and pbefore!=FRAME-32,'actual physical original stdcall16 evidence')
    final=[OBJECT,sa[1],sa[2],c[3],FRAME+4,c[5],c[6],c[7],sa[8],RET]
    require(list(w(r,76,10))==final,'whole caller CPU with observed volatility carry')
    original_fx=r[116:628];guest_after=r[628:1140]
    if native:
        f=fxseed(cw,top,v);require(original_fx==f and guest_after==f,'complete representative guest FX')
        # These are hardware observations of the real host query, separate
        # from the software guest FP policy. In these records the legacy host
        # environment happened to stay unchanged across the query.
        require(r[34964:34992]==r[2220:2248] and r[34992:35020]==r[34964:34992],'observed native host-query legacy ENV')
        for fo,eo in ((33940,34964),(34452,34992)):
            require(r[fo:fo+4]==r[eo:eo+2]+r[eo+4:eo+6] and r[fo+4]==0,'actual host-query FX/ENV core coherence')
    else:
        f=fxseed(cw,top,v);f[28:32]=r[1140+28:1140+32];require(u32(f,28)>0 and not(u32(f,28)&0xfffc0000),'hardware capability mask')
        require(original_fx==f,'complete input-derived original FX')
        require(r[33940:34452]==original_fx,'original integer caller to service FX carry')
        require(r[34452:34964]==guest_after,'actual service-to-caller full FX carry')
        # The captured x87/MXCSR fields happened to be unchanged in this gate.
        # This observation is separate from the unspecified SIMD output policy.
        require(original_fx[:160]==guest_after[:160] and original_fx[288:]==guest_after[288:],'observed original x87/MXCSR unchanged')
    en=envseed(cw,top);require(r[2164:2192]==en and r[2192:2220]==en,'observed original / representative native legacy ENV')
    if not native:require(r[34964:34992]==en and r[34992:35020]==en,'actual original service legacy ENV carry')
    host_restore(r,native)
    before=pages_before(source,v);require(r[2276:14564]==before,'three entire input pages')
    rect_before=r[35020:35036];rect=r[35036:35052]
    require(rect_before==before[4096+0xfa0:4096+0xfb0],'owned initial RECT bytes')
    after=memory_after(before,v,rect);require(r[14564:26852]==after,'three entire final pages / actual RECT transport')
    count,completed=w(r,35072,2);require(completed==1,'completed')
    if native:
        state=state_seed(cw,top,v,repeat);require(r[26852:30356]==state,'whole seeded State')
        for o,value in zip(GPR,final[:8]+final[9:]):put(state,o,value)
        require(r[30356:33860]==state,'whole final State including protected bytes')
        ev=events(before,v,rect);require(count==34,'event count')
        for i,row in enumerate(ev):require(w(r,35080+20*i,5)==row,'ordered event '+str(i))
        require(r[35080+20*34:]==bytes(20*30),'unused event storage zero')
    else:require(count==0 and r[26852:33860]==bytes(7008) and r[35080:]==bytes(1280),'original State/events remain unobserved')
    return {'rectangle':list(struct.unpack('<4i',rect)),'BOOL':result,'service_ecx':sa[1],'service_edx':sa[2],'service_flags':sa[8]}

def read_stream(b,native,source):
    require(b[:8]==(b'MW4SPIN1' if native else b'MW4SPIO1') and w(b,8,4)==(1,144,36360,3),'stream framing')
    require(len(b)==24+144*36360,'complete raw extent')
    return [check_record(b[24+i*36360:24+(i+1)*36360],i,native,source) for i in range(144)]
def causal(original,native,source):
    negative=[];positive=[];base=24
    offsets=[('tag',0),('inputEAX',36),('inputflags',68),('definedEAX',76),('returnESP',92),('returnPC',112),('originalvolatilecarry',80),('inputx87',116),('inputvector',276),('fxcarry',628+160),('legacyinput',2164),('legacyafter',2192),('hostrestore',1652+24),('sourcepage',2276),('unrelatedobject',2276+4096),('inputframe',2276+8192+0x800),('wholeafterpage',14564),('savedreg',14564+8192+0x7fc),('callerRET',14564+8192+0x800),('RECTtransport',14564+4096+0xfa0),('serviceentry',33860+4),('serviceBOOL',35056),('servicecleanup',35060),('RECTinput',35020),('completed',35076)]
    for level,data,isnative in [('original',original,False),('native',native,True)]:
        local=list(offsets) if not isnative else [x for x in offsets if x[0]!='fxcarry']
        local+= [('Stateprotected',26852+1000),('StatehighGPR',30356+2220),('Statelegacy',30356+2776),('eventPC',35080),('eventaddress',35084),('eventvalue',35088),('eventwidth',35092),('eventorder',35096),('eventcount',35072),('unusedEvent',35080+34*20),('host-query-FX',33940),('host-query-ENV',34964)] if isnative else [('physicalProviderESP',35064),('serviceSIMDcarry',34452+160)]
        for name,offset in local:
            changed=bytearray(data);changed[base+offset]^=1
            try:read_stream(changed,isnative,source)
            except AssertionError as e:negative.append({'name':level+'-'+name,'rejected':True,'diagnostic':str(e)})
            else:raise AssertionError('missed causal corruption '+level+'-'+name)
    for name in ['ECX','EDX','flags','XMM','discarded BOOL']:
        changed=bytearray(original)
        if name in ('ECX','EDX'):
            i=1 if name=='ECX' else 2;changed[base+33900+4*i]^=17;changed[base+76+4*i]^=17
        if name=='flags':changed[base+33900+32]^=0x45;changed[base+76+32]^=0x45
        if name=='XMM':changed[base+34452+160+6*16]^=17;changed[base+628+160+6*16]^=17
        if name=='discarded BOOL':put(changed,base+33900,0);put(changed,base+35056,0)
        read_stream(changed,False,source);positive.append({'name':'synchronized unspecified '+name,'accepted':True})
    return negative,positive

def run():
    OUT.mkdir(parents=True,exist_ok=False);report={'passed':False}
    try:
        game=PE((ROOT/'MW3/Mech3.exe').read_bytes());require(game.machine==0x14c and game.base==0x400000,'game PE32')
        require(game.import_owner(IAT)==('USER32.dll','SystemParametersInfoA',0x1df20c),'exact real import owner')
        require(u32(game.bytes(0x1e0110,4),0)==ENTRY,'actual initializer table root')
        body=bytes.fromhex('538bd956578d43186a00b906000000be00605e008bfb506a006a30f3a5ff15dcb65b005f8bc35e5bc3')
        require(game.bytes(0x82cc0,len(body))==body,'complete exact nineteen body instructions')
        require(game.bytes(0x82cf0,5)==bytes.fromhex('e90b000000') and game.bytes(0x82d00,10)==bytes.fromhex('b9888f6000e9b6ffffff'),'three exact wrapper tail-route instructions')
        source=game.mapped(0x1e6000,4096)
        provider=[]
        for path,machine in [('C:/Windows/SysWOW64/user32.dll',0x14c),('C:/Windows/System32/user32.dll',0x8664)]:
            p=Path(path);b=p.read_bytes();pe=PE(b);require(pe.machine==machine,'actual provider architecture');ordinal,rva,forwarded=pe.export('SystemParametersInfoA');require(not forwarded,'actual named disk export');provider.append({'path':str(p),'sha256':sha(b),'machine':machine,'export_ordinal':ordinal,'export_rva':rva,'raw_api_pointer_serialized':False})
        folder=ROOT/'reports/m4-spi-workarea/capture-r4-normal-windows';original=(folder/'original.bin').read_bytes();o=read_stream(original,False,source);results=[]
        for level in ('O0','O2'):
            native=(folder/(level+'.bin')).read_bytes();n=read_stream(native,True,source)
            for i in range(144):require(o[i]['rectangle']==n[i]['rectangle'],'captured-desktop defined actual RECT output')
            negatives,positives=causal(original,native,source)
            results.append({'level':level,'records':144,'events':4896,'own_negative_controls':negatives,'own_unspecified_positive_controls':positives,'original_native_ECX_differences':sum(a['service_ecx']!=b['service_ecx'] for a,b in zip(o,n)),'original_native_EDX_differences':sum(a['service_edx']!=b['service_edx'] for a,b in zip(o,n)),'original_native_flag_differences':sum(a['service_flags']!=b['service_flags'] for a,b in zip(o,n)),'observed_rectangles':sorted({tuple(a['rectangle']) for a in n})})
        report.update(passed=True,original_records=144,native_records=288,results=results,providers=provider,source_instruction_sha256=sha(body+game.bytes(0x82cf0,5)+game.bytes(0x82d00,10)),scope='Independent actual original/provider and bounded hand translation; exact defined caller outputs, separate original volatile observations/native policy; no shared startup or Remill lift acceptance')
    except Exception:report['failure']=traceback.format_exc();(OUT/'failure.txt').write_text(report['failure']);raise
    finally:(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'model-source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({'passed':True,'original':144,'native':288,'own_negatives_each_level':len(results[0]['own_negative_controls']),'own_positives_each_level':5}))
if __name__=='__main__':run()
