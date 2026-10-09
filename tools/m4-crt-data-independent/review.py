"""Independent standard-library observer; imports no author code."""
from pathlib import Path
import hashlib, json, struct, sys, traceback

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/m4-crt-data/independent-review-r1/raw-r2'
CW = (0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
def sha(data): return hashlib.sha256(data).hexdigest()
def require(ok, why):
    if not ok: raise AssertionError(why)
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def words(b,o,n): return struct.unpack_from('<'+'I'*n,b,o)
def put(b,o,v,n=4): b[o:o+n]=v.to_bytes(n,'little')
def bind(p):
    p=Path(p).resolve(); b=p.read_bytes()
    return {'path':str(p),'size_bytes':len(b),'sha256':sha(b)}

class PE:
    def __init__(self,b):
        self.b=b; require(b[:2]==b'MZ','DOS'); pe=u32(b,60)
        require(b[pe:pe+4]==b'PE\0\0','PE signature'); self.machine=u16(b,pe+4)
        self.opt=pe+24; require(u16(b,self.opt)==0x10b,'PE32')
        self.base=u32(b,self.opt+28); self.image_size=u32(b,self.opt+56)
        self.sections=[]; count=u16(b,pe+6); osize=u16(b,pe+20)
        require(0<count<97 and self.opt+osize+count*40<=len(b),'section bounds')
        for i in range(count):
            o=self.opt+osize+40*i; vs,va,rs,rp=words(b,o+8,4); flags=u32(b,o+36)
            require(va+max(vs,rs)<=self.image_size and rp+rs<=len(b),'section extent')
            self.sections.append((va,vs,rs,rp,flags))
    def offset(self,rva,n=1):
        for va,vs,rs,rp,flags in self.sections:
            if va<=rva and rva+n<=va+rs: return rp+rva-va
        raise AssertionError('unbacked RVA '+hex(rva))
    def bytes(self,rva,n):
        o=self.offset(rva,n); return self.b[o:o+n]
    def string(self,rva):
        o=self.offset(rva); end=self.b.index(0,o); require(end-o<4096,'name bound')
        return self.b[o:end].decode('ascii')
    def imports(self):
        begin,size=words(self.b,self.opt+104,2); result=[]
        if not begin:return result
        for d in range(0,size,20):
            orig,timestamp,chain,name,iat=words(self.b,self.offset(begin+d,20),5)
            if not any((orig,timestamp,chain,name,iat)): return result
            lib=self.string(name); lut=orig or iat
            for i in range(65536):
                value=u32(self.b,self.offset(lut+4*i,4))
                if not value:break
                label=value&0xffff if value&0x80000000 else self.string(value+2)
                result.append((lib,label,self.base+iat+4*i,u32(self.b,self.offset(iat+4*i,4))))
            else:raise AssertionError('import termination')
        raise AssertionError('descriptor termination')
    def export(self,name):
        rva,size=words(self.b,self.opt+96,2); o=self.offset(rva,40)
        base,fc,nc,fa,na,oa=words(self.b,o+16,6)
        for i in range(nc):
            if self.string(u32(self.b,self.offset(na+4*i,4)))==name:
                ordinal=u16(self.b,self.offset(oa+2*i,2)); require(ordinal<fc,'ordinal')
                target=u32(self.b,self.offset(fa+4*ordinal,4))
                return base+ordinal,target,rva<=target<rva+size
        raise AssertionError('missing export '+name)

def regions_ok(regions,pointer,length):
    cursor=pointer; end=pointer+length; require(end<=1<<32,'buffer overflow')
    for base,size,allocation,state,kind,protect,ap in regions:
        require(size>0 and base<=cursor<base+size<=1<<32,'readable coverage')
        require(allocation<=base and state==0x1000 and kind in (0x20000,0x40000,0x1000000),'memory ownership')
        require(not(protect&0x101) and protect&0xee,'readable protection')
        cursor=min(end,base+size)
    require(cursor==end,'complete bounded buffer')

def observe(raw):
    require(raw[:8]==b'MW4CMD01' and len(raw)>=44,'raw magic')
    version,count,stride,length,api,allocation,pointer,pathsize,nregions=words(raw,8,9)
    require(version==1 and count==192 and stride==18636+28*nregions,'raw framing')
    require(0<length<=131072 and 0<pathsize<32768 and 0<nregions<65536,'raw bounds')
    at=44; path=raw[at:at+pathsize].decode('ascii'); at+=pathsize
    module_sha=raw[at:at+64].decode('ascii');at+=64
    ar=words(raw,at,7);at+=28
    initial=[words(raw,at+i*28,7) for i in range(nregions)];at+=28*nregions
    buffer=raw[at:at+length];at+=length
    require(len(raw)==at+count*stride,'complete stream extent')
    require(buffer[-1:]==b'\0' and b'\0' not in buffer[:-1],'single bounded NUL')
    require(path.lower()=='c:\\windows\\system32\\kernel32.dll','measured module namespace')
    # WOW64's literal process path is resolved explicitly to the x86 file view.
    mp=Path('C:/Windows/SysWOW64/kernel32.dll'); module=mp.read_bytes()
    require(sha(module)==module_sha,'actual x86 OS module identity')
    os=PE(module);require(os.machine==0x14c,'actual API x86 module')
    ordinal,rva,forwarded=os.export('GetCommandLineA')
    require(not forwarded and api-allocation==rva,'actual export target')
    require(os.bytes(rva,2)==b'\xff\x25','actual API import jump thunk')
    require(ar[0]<=api<ar[0]+ar[1] and ar[2]==allocation and ar[3]==0x1000 and ar[4]==0x1000000 and ar[5]&0xf0,'API owned RX image')
    regions_ok(initial,pointer,length)
    for index in range(count):
        r=raw[at+stride*index:at+stride*(index+1)]
        repeat=index//96; cw=CW[(index%96)//8]; top=index%8
        require(words(r,0,3)==(repeat,cw,top),'input schedule')
        seed=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,0x202,0x7800188c)
        require(words(r,12,10)==seed,'complete input CPU')
        after=(pointer,)+seed[1:9]+(0x10000100,)
        require(words(r,52,10)==after,'complete original CPU/call continuation')
        host=r[1116:1628];require(host==r[1628:2140],'complete host FX restore')
        require(r[2196:2224]==r[2224:2252],'complete host ENV restore')
        fx=bytearray(512);put(fx,0,cw,2);put(fx,2,top<<11,2);put(fx,24,0x1f80)
        # FXSAVE supplies the measured host processor's capability mask.
        fx[28:32]=host[28:32]; require(u32(fx,28)!=0 and not(u32(fx,28)&0xfffc0000),'processor MXCSR mask')
        for i in range(8):
            for j in range(10): fx[32+16*i+j]=(17+13*i+7*j)&255
        for i in range(128):fx[160+i]=(19*i+3)&255
        require(r[92:604]==fx and r[604:1116]==fx,'complete input-derived guest FX')
        env=bytearray(28)
        for o,v in [(0,cw),(2,0xffff),(4,top<<11),(6,0xffff),(8,0xffff),(10,0xffff),(16,0x23),(18,0x11d),(24,0x2b),(26,0xffff)]:put(env,o,v,2)
        put(env,12,0x11223344);put(env,20,0x55667788)
        require(r[2140:2168]==env and r[2168:2196]==env,'complete input-derived legacy ENV')
        stack=bytearray(b'\xa5'*4096);put(stack,0x800,0x10000100)
        require(r[2252:6348]==stack,'whole input stack')
        put(stack,0x7fc,0x78001892);require(r[6348:10444]==stack,'whole original CALL stack residue')
        globals=bytearray(b'\xa5'*4096);require(r[10444:14540]==globals,'whole input global page')
        put(globals,0x174,pointer);require(r[14540:18636]==globals,'whole writer global page')
        current=[words(r,18636+28*i,7) for i in range(nregions)]
        regions_ok(current,pointer,length)
        for before,after_region in zip(initial,current):
            require(before[:1]+before[2:]==after_region[:1]+after_region[2:],'stable buffer allocation/protection')
    return {'records':count,'stride':stride,'borrowed_pointer':pointer,'api':api,'api_module':bind(mp),'export_ordinal':ordinal,'export_rva':rva,'buffer_size':length,'buffer_sha256':sha(buffer),'record_begin':at,'buffer_regions':nregions,'scope':'Actual original writer only; observed process command line, no native OS/writer implementation'}

def controls(raw,summary):
    at=summary['record_begin']; tests=[]
    # Independent mutations cover every protected GPR, flags, all physical FP
    # slots, both metadata views, exact stack/global pages and owner coverage.
    changes=[('magic',0),('count',12),('stride',16),('pointer',32),('api',24)]
    changes += [('tag'+str(i),at+4*i) for i in range(3)]
    changes += [('cpu-'+str(i),at+12+4*i) for i in range(10)]
    changes += [('return-'+str(i),at+52+4*i) for i in range(10)]
    changes += [('fp-slot'+str(i),at+92+32+16*i) for i in range(8)]
    changes += [(name,at+o) for name,o in [('fx-cw',92),('fx-top',94),('fx-tag',96),('fx-xmm',252),('fx-after',604),('host-fx',1628),('env-before',2152),('env-after',2180),('host-env',2224),('input-stack',2252),('call-ret',6348+0x7fc),('caller-frame',6348+0x800),('global-before',10444),('global-value',14540+0x174),('global-neighbor',14540+0x173),('coverage-size',18636+4),('coverage-owner',18636+8),('coverage-protect',18636+20)]]
    for name,o in changes:
        changed=bytearray(raw)
        if name=='coverage-size':put(changed,o,0)
        else:changed[o]^=1
        try:observe(changed)
        except (AssertionError,UnicodeError,struct.error,ValueError) as e:tests.append({'name':name,'rejected':True,'diagnostic':str(e)})
        else:raise AssertionError('observer missed mutation '+name)
    for name,b in [('truncate',raw[:-1]),('append',raw+b'X')]:
        try:observe(b)
        except AssertionError as e:tests.append({'name':name,'rejected':True,'diagnostic':str(e)})
        else:raise AssertionError('observer missed '+name)
    # VirtualQuery region extents may grow through adjacent probe allocations.
    # The allocation/base/protection and full NUL coverage must stay stable.
    changed=bytearray(raw)
    for i in range(192):put(changed,at+i*summary['stride']+18636+4,u32(changed,at+i*summary['stride']+18636+4)+4096)
    observe(changed)
    return tests,[{'name':'permitted query extent growth','accepted':True}]

def run():
    OUT.mkdir(parents=True,exist_ok=False)
    report={'passed':False,'scope':'Independent bounded reference-only CRT writer and projection ownership review; full M4 remains open'}
    try:
        author=ROOT/'reports/m4-crt-data/author-review-r1'
        require(sha((author/'report.json').read_bytes())=='b0f26788bf5adca5196778cae2b89e0e15b35f943ec016f64c6a73ad49ec6350','author report identity')
        require(sha((author/'pins.json').read_bytes())=='8af9f365e95d58cd2b02983626c1ab51a6c273d5e4ebef2aa0f00315484251f4','author pins identity')
        bindings=json.loads((author/'pins.json').read_text())['files'];require(len(bindings)==738,'physical count')
        for p,h in bindings.items(): require(sha(Path(p).read_bytes())==h,'physical binding '+p)
        auth=json.loads((author/'report.json').read_text());hist=auth['historical_source_resolutions'];require(len(hist)==7,'historical count')
        for row in hist:
            require(sha(Path(row['physical_path']).read_bytes())==row['recorded_sha256'],'literal historical source')
            require(sha(Path(row['historical_map']).read_bytes())==row['historical_map_sha256'],'historical map')
            old=json.loads(Path(row['historical_map']).read_text());require(old['source_files'][row['original_path']]==row['recorded_sha256'],'old source-map association')
        provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';game=ROOT/'MW3/Mech3.exe'
        require(sha(provider.read_bytes())=='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7','provider')
        require(sha(game.read_bytes())=='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf','game')
        pp=PE(provider.read_bytes());gp=PE(game.read_bytes())
        require(pp.machine==0x14c and pp.base==0x78000000,'provider PE')
        writer=pp.bytes(0x188c,11);require(writer==bytes.fromhex('ff1534e00278a374710378'),'complete actual writer instructions')
        require(pp.bytes(0x37174,4)==b'\0'*4,'file-backed global identity')
        require([(lib,name) for lib,name,slot,v in pp.imports() if slot==0x7802e034]==[('KERNEL32.dll','GetCommandLineA')],'provider API named import')
        actual_data=[(lib,name,slot,v) for lib,name,slot,v in gp.imports() if slot in (0x5bb518,0x5bb508)]
        require({(lib.lower(),name,slot) for lib,name,slot,v in actual_data}=={('msvcrt.dll','_acmdln',0x5bb518),('msvcrt.dll','_adjust_fdiv',0x5bb508)},'real owning game data imports')
        pack=(ROOT/'reports/m4-crt-data/commandline-research-r1/pack.bin').read_bytes()
        require(pack[:8]==b'MW4CMPK1' and words(pack,8,2)==(0x78001000,4096),'pack layout')
        require(pack[16+0x88c:16+0x897]==writer,'pack actual source bytes')
        require(pack[16+0x897]==0xe9 and (0x7800189c+u32(pack,16+0x898))&0xffffffff==0x10000100,'declared authored capture jump')
        rawpath=ROOT/'reports/m4-crt-data/commandline-run-r1/original.bin';raw=rawpath.read_bytes()
        result=observe(raw);negative,positive=controls(raw,result)
        report.update(original=result,own_observer_negative_controls=negative,own_observer_positive_controls=positive,physical_author_bindings=738,literal_historical_resolutions=7,source_instruction_sha256=sha(writer),exact_game_data_imports=actual_data)
        report['passed']=True
    except Exception:
        report['failure']=traceback.format_exc();(OUT/'failure.txt').write_text(report['failure']);raise
    finally:
        (OUT/'raw-review.json').write_text(json.dumps(report,indent=2)+'\n')
        (OUT/'review-source.py').write_bytes(Path(__file__).read_bytes())
    print(json.dumps({'passed':True,'original_rows':result['records'],'negative_controls':len(negative),'positive_controls':len(positive)}))
if __name__=='__main__':run()
