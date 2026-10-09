"""Root offline source/input model of frozen matherr reference observations.

Only PE metadata is imported. No original process is run, and no author
comparator, fixture generator, executor or model is imported.
"""
import hashlib, importlib.util, json, struct, subprocess, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-matherr';PINS={}
STRIDE=26836;CPU=struct.Struct('<10I');ENTRY=0x7800b38f;FRAME=0x200017fc;RETURN=0x5ac42e;CAPTURE=0x10000100
CWS=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
ARGS=(0,0x51e7b0,0xffffffff,0x10000001,0x30000000,ENTRY,0x80000000,0x12345678)
DEPTH=(0,1,7,8,0,1,7,8)

def need(ok,why):
    if not ok:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,want=None):
    p=Path(p).resolve();got=sha(p);need(want is None or got==want,'Exact source/observation identity '+str(p))
    need(str(p) not in PINS or PINS[str(p)]==got,'Conflicting identity');PINS[str(p)]=got;return p
def read(p):return json.loads(pin(p).read_text(encoding='utf-8-sig'))
def word(b,o=0):return struct.unpack_from('<I',b,o)[0]
def put(b,o,v,size=4):b[o:o+size]=v.to_bytes(size,'little')

def static(out):
    p=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
    spec=importlib.util.spec_from_file_location('metadata_only_matherr',p);pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe)
    provider_path=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    game_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    provider_raw=provider_path.read_bytes();game_raw=game_path.read_bytes();provider=pe.PEImage(provider_raw);game=pe.PEImage(game_raw)
    def at(image,raw,address,size):return raw[image.rva_range(address-image.image_base,size)[0]:][:size]
    need(provider.image_base==0x78000000 and game.image_base==0x400000,'Actual preferred PE bases')
    export=[x for x in provider.exports() if '__setusermatherr' in x['names']]
    need(len(export)==1 and export[0]['ordinal']==132 and export[0]['rva']==0xb38f and 'forwarder' not in export[0],'Actual complete named provider export/ordinal')
    imported=[(lib['library'],x) for lib in game.imports() for x in lib['symbols'] if x['iat_rva']+game.image_base==0x5bb50c]
    need(len(imported)==1 and imported[0][0]=='MSVCRT.dll' and imported[0][1]['name']=='__setusermatherr','Actual named game IAT metadata')
    source=at(provider,provider_raw,ENTRY,17)
    need(hashlib.sha256(source).hexdigest()=='db28fc73ef336b9925b6cd56a37615599cc224d6a38cdd3b3cf5851c72e77bc9','Complete source identity')
    caller=at(game,game_raw,0x5ac423,11)
    need(hashlib.sha256(caller).hexdigest()=='ed4e3e4ef3536ad0d20aab36b55f011878b9bc1e9bd9760631ee5a4fb5b4456e','Exact private static caller span identity')
    need(caller[0]==0x68 and word(caller,1)==0x51e7b0 and caller[5]==0xff and caller[6]==0x15 and word(caller,7)==0x5bb50c,'Actual PUSH callback and named indirect CALL operands')
    dump=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
    command=[str(dump),'--disassemble','--x86-asm-syntax=intel','--start-address=0x7800b38f','--stop-address=0x7800b3a0',str(provider_path)]
    result=subprocess.run(command,capture_output=True,text=True);need(result.returncode==0,'Fresh static provider decode')
    dest=out/'provider-decode.txt';dest.write_text(result.stdout,encoding='utf-8');pin(dest)
    import re
    decoded=[]
    for line in result.stdout.splitlines():
        match=re.match(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)$',line)
        if match:
            address=int(match[1],16);body=bytes.fromhex(match[2]);need(at(provider,provider_raw,address,len(body))==body,'Fresh decode matches exact private bytes');decoded.append((address,len(body),match[3],match[4].strip()))
    need(decoded==[(ENTRY,4,'mov','eax, dword ptr [esp + 0x4]'),(ENTRY+4,7,'and','dword ptr [0x780392b8], 0x0'),(ENTRY+11,5,'mov','dword ptr [0x7803b0c4], eax'),(ENTRY+16,1,'ret','')],'Complete independently decoded four-instruction source operands')
    pack=pin(BASE/'paired-preparation-r1/pack.bin').read_bytes();need(pack[:8]==b'MW4MTK01' and word(pack,8)==2 and len(pack)==8220,'Frozen reference pack framing')
    for i,(base,image,raw) in enumerate(((0x5ac000,game,game_raw),(0x7800b000,provider,provider_raw))):
        offset=12+i*4104;need(struct.unpack_from('<2I',pack,offset)==(base,1),'Exact RX reference code page role')
        expected=bytearray(at(image,raw,base,4096))
        if not i:expected[0x42e:0x433]=b'\xe9'+struct.pack('<I',(CAPTURE-0x5ac433)&0xffffffff)
        need(pack[offset+8:offset+4104]==expected,'Full actual source code page with sole explicit capture patch')
    return dict(export=export[0],imported=imported[0],source_hex=source.hex(),raw_IAT_DWORD=word(at(game,game_raw,0x5bb50c,4)),command=command,static_game_caller_executed=False)

def incoming(index):
    return (0x13579bdf^index,0x2468ace0,0x81726354,0x10293847,FRAME,0x92837465,0x56473829,0xaabbccdd,0x202|(0xcd5 if index&1 else 0),ENTRY)
def pages(index,arg):
    b=bytearray((index+j*7+k*19)&255 for k in range(3) for j in range(4096));put(b,0x7fc,RETURN);put(b,0x800,arg);return b
def fp(cw,top,argindex):
    sw=(top<<11)|(0x25 if argindex>=4 else 0);ftw=0;tags=0xffff
    for i in range(DEPTH[argindex]):p=(top+i)&7;ftw|=1<<p;tags&=~(3<<(2*p))
    f=bytearray(512);put(f,0,cw,2);put(f,2,sw,2);f[4]=ftw;put(f,24,0x1f80);put(f,28,0x2ffff)
    for i in range(8):put(f,32+16*i,0x8000000000000000+0x0101010101010101*i,8);put(f,40+16*i,0x3fff+i,2)
    f[160:288]=bytes((i*19+3+argindex)&255 for i in range(128))
    e=struct.pack('<7I',0xffff0000|cw,0xffff0000|sw,0xffff0000|tags,0x11223344,0x11d0023,0x55667788,0xffff002b)
    return bytes(f),e
def observe(row,index):
    need(len(row)==STRIDE,'Whole reference record')
    repeat=index//768;cw=CWS[(index%768)//64];top=(index%64)//8;ai=index%8;arg=ARGS[ai]
    need(struct.unpack_from('<5I',row)==(repeat,index,arg,cw,top),'Exact1536 scheduled tags')
    before=incoming(index);need(CPU.unpack_from(row,20)==before,'Complete original entry CPU/flags/cdecl frame')
    memory=pages(index,arg);need(row[2260:14548]==memory,'All three patterned input pages and actual return/argument words')
    after=list(before);after[0]=arg;after[4]=FRAME+4;after[8]=(before[8]&~0x8c5)|0x44;after[9]=CAPTURE
    actual=CPU.unpack_from(row,60)
    need(actual[:8]==tuple(after[:8]) and actual[9]==after[9] and not ((actual[8]^after[8])&~0x10),'Complete MOV/AND/MOV/RET CPU; only undefined AF excluded')
    put(memory,4096+0x2b8,0);put(memory,8192+0xc4,arg)
    need(row[14548:26836]==memory,'Only exact AND zero-global and MOV callback-global writes across all three pages')
    fx,env=fp(cw,top,ai)
    need(row[100:612]==row[612:1124]==fx,'Entire coherent original FX512 preserved with live tags/TOP/sticky status/raw80/SIMD')
    need(row[2148:2176]==row[2176:2204]==env,'Entire original legacy ENV28 preserved')
    need(row[1124:1636]==row[1636:2148] and row[2204:2232]==row[2232:2260],'Actual full original host FX512/ENV28 restoration')
    return tuple(after),bytes(memory),arg,cw,top

def main(out):
    need(out.is_relative_to(BASE) and not out.exists(),'Fresh offline independent output')
    out.mkdir(parents=True);(out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
    try:
        metadata=static(out)
        pin(BASE/'paired-original-r1-normal-windows/report.json','9d9e253a8c7f263c57477bf5d483502a4848583c6627b4a35cd4d85bb9683c4f')
        raw=pin(BASE/'paired-original-r1-normal-windows/original.bin','50adc9316afe26f0deb78cac3aeb737bc5c0810324897031c3bd548fec30c472').read_bytes()
        need(struct.unpack_from('<8s4I',raw)==(b'MW4MOR01',1,1536,STRIDE,12288) and len(raw)==24+1536*STRIDE,'Entire original stream and exactextent')
        for index in range(1536):observe(raw[24+index*STRIDE:24+(index+1)*STRIDE],index)
        controls=[]
        for index in (0,1,4,63):
            row=raw[24+index*STRIDE:24+(index+1)*STRIDE]
            for off in (0,4,8,12,16,20,52,56,60,76,92,96,100,102,104,128,132,260,612,614,616,644,1124,1636,2148,2160,2176,2188,2204,2232,2260,2260+0x7fc,2260+0x800,14548,14548+4096+0x2b8,14548+8192+0xc4):
                changed=bytearray(row);changed[off]^=1
                try:observe(bytes(changed),index)
                except (ValueError,struct.error) as ex:controls.append(dict(index=index,offset=off,rejected=True,reason=str(ex)))
                else:raise ValueError('Independent observer accepted corruption '+str((index,off)))
            changed=bytearray(row);changed[92]^=0x10;observe(bytes(changed),index)
            controls.append(dict(index=index,case='original_undefined_AF_positive',accepted=True,rejected=False))
        report=dict(passed=True,scope='Offline independent four-instruction source/input model of actual frozen original matherr observations only',original_records=1536,complete_three_page_observations=1536*2,masked_CW_words=list(CWS),all_TOP_values=list(range(8)),coherent_profile_depths=list(DEPTH),sticky_status_words=[0,0x25],static=metadata,independent_observer_controls=controls,native_accepted=False,callback_invoked=False,full_CRT_caller_executed=False,original_process_executed_by_reviewer=False,primary_executor_or_model_imported=False,whole_M4_complete=False,limitations=['Entry frame/argument/initial memory and FP are authored fixtures. Actual full original CPU/pages/hardwareFX/legacyENV outputs are independently modeled.','Original softwareState/events/routes unobserved; no native equivalence credit in this stage.','AND AF is undefined and excluded only for the original output flags. The native IR representative must be independently modeled, not copied from original output AF.','Only exact owned5AC42E captureJMP is executed after originalRET; actual static PUSH/CALL game CRT caller and callback target are not executed.'])
        rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp);pin(Path(__file__))
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,records=1536,controls=len(controls),report_sha256=sha(rp),pins_sha256=sha(out/'pins.json'))))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
