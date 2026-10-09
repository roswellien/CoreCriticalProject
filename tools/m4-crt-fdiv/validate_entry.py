"""Exact before-only native fixture and literal source admission validation."""
import argparse,hashlib,json,pathlib,struct
from validate_native import ROOT,BASE,CW,GPR,AF,PE,STRIDE,PAGES,need,put,read,sha

def seed(cw,repeat):
    s=bytearray((i*31+repeat*17+3)&255 for i in range(3504));s[2112:2208]=bytes(96);put(s,2168,0x7ffde000)
    for name,v in zip(GPR,(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,0x78004254)):put(s,GPR[name],v)
    put(s,2080,0x202,8)
    for offset,bit in AF:s[offset]=0
    put(s,2768,cw,2);put(s,2770,0,2);s[2772]=0;put(s,2792,0x1f80);put(s,2796,0x2ffff)
    put(s,2774,0x11d,2);put(s,2776,0x11223344);put(s,2780,0x23,2);put(s,2784,0x55667788);put(s,2788,0x2b,2)
    for i in range(11):s[2737+2*i]=0
    fx=bytearray(s[2768:3280]);fx[6:24]=bytes(18)
    stack=bytearray((i*7+repeat*19+0xa5)&255 for i in range(4096));put(stack,0x800,0x78004232)
    return bytes(s),bytes(fx),bytes(stack)

def validate_row(b,pack,game):
    ident,repeat,cw=struct.unpack_from('<3I',b);need(ident<24 and repeat==ident%2 and cw==CW[ident//2],'Native entry corpus identity');s,fx,stack=seed(cw,repeat)
    need(b[28:3532]==s and b[7036:7548]==fx,'Every dirty entry State3504 and separateFX512 byte is exact authored fixture; no hidden reseed')
    pages=b[9140:46004]
    for i,address in enumerate(PAGES[:7]):
        offset=12+i*4104;need(struct.unpack_from('<I',pack,offset)[0]==address and pages[i*4096:(i+1)*4096]==pack[offset+8:offset+4104],'Literal admitted source/IAT/uninitialized data page exact')
    need(pages[7*4096:8*4096]==stack and pages[8*4096:]==game.bytes(0x5bb000,4096),'Full authored stack/callback return and actual game IAT page entry identity')

def main(build,out):
    build=pathlib.Path(build).resolve();out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh private entry validation output');out.mkdir();m=read(build);need(m['passed'],'Actual native build');game=PE(ROOT/'MW3/Mech3.exe');packpath=BASE/'native-derived-r1/pack.bin';pack=packpath.read_bytes();report=read(packpath.parent/'report.json');need(sha(packpath)==report['pack_sha256'],'Exact private literal pack');bindings={str(build):sha(build),str(packpath):sha(packpath),str(game.path):sha(game.path),str(pathlib.Path(__file__).resolve()):sha(__file__),str(ROOT/'tools/m4-crt-fdiv/validate_native.py'):sha(ROOT/'tools/m4-crt-fdiv/validate_native.py')};count=0;controls=0
    for level in('O0','O2'):
        path=build.parent/f'native-{level}.bin';raw=path.read_bytes();bindings[str(path)]=sha(path)
        for i in range(24):
            row=raw[24+i*STRIDE:24+(i+1)*STRIDE];validate_row(row,pack,game);count+=1
            for offset in(28,28+2168,28+2768,28+2774,28+3280,7036,7036+6,9140,9140+3*4096+0x98,9140+6*4096+0xc28,9140+6*4096+0xc2c,9140+7*4096+0x800,9140+8*4096+0x508):
                bad=bytearray(row);bad[offset]^=1
                try:validate_row(bad,pack,game)
                except ValueError:controls+=1
                else:raise ValueError('Before-only corruption admitted')
    result={'passed':True,'scope':'Before-only authored fixture and literal source admission; no original execution','native_rows':count,'State_bytes':3504,'separate_FX_bytes':512,'pages':9,'causal_observers':controls,'opaque_storage_and_legacy_distinction_verified':True,'original_execution':False,'whole_M4_complete':False}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');bindings[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(bindings,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--out',required=True);a=p.parse_args();main(a.build,a.out)
