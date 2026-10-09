"""Direct call-boundary observed architectural/ABI preservation checks."""
import argparse,json,pathlib,struct
from validate_native import ROOT,BASE,need,read,sha
CAPTURE=544;ROW=1092
def validate(row):
    mode=struct.unpack_from('<I',row)[0];need(mode in(0,1),'Positive/fault boundary case');before=row[4:548];after=row[548:1092]
    need(before[512:540]==after[512:540],'Whole actual ENV28 across real C++ return')
    for begin,end in((0,5),(24,28),*((32+16*i,42+16*i)for i in range(8)),*((160+16*i,176+16*i)for i in range(6,16))):need(before[begin:end]==after[begin:end],'Actual call-boundary architectural/ABI-defined field preservation')
    for i in range(6,16):need(before[160+16*i:176+16*i]==bytes((i*31+j*17+mode+1)&255 for j in range(16)),'Nonzero authored ABI sentinel actually captured at boundary')
    need(not any(before[540:])and not any(after[540:]),'Zero unused Capture padding')
def main(out):
    out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh private boundary validation');out.mkdir();bp=BASE/'native-boundary-r3/build.json';m=read(bp);need(m['passed'],'Frozen actual outside-boundary build');bindings={str(bp):sha(bp),str(pathlib.Path(__file__).resolve()):sha(__file__),str(ROOT/'tools/m4-crt-fdiv/validate_native.py'):sha(ROOT/'tools/m4-crt-fdiv/validate_native.py')};checks=0;volatile=0
    for level in('O0','O2'):
        p=bp.parent/f'boundary-{level}.bin';b=p.read_bytes();need(len(b)==2*ROW,'Exact observed outside boundary extent');bindings[str(p)]=sha(p)
        for mode in range(2):
            row=b[mode*ROW:(mode+1)*ROW];need(struct.unpack_from('<I',row)[0]==mode,'Literal actual boundary order');validate(row)
            for offset in(548,548+2,548+4,548+24,548+32,548+32+7*16,548+256,548+400,548+512,548+528):
                bad=bytearray(row);bad[offset]^=1
                try:validate(bad)
                except ValueError:checks+=1
                else:raise ValueError('Required architectural/ABI mutation admitted')
            bad=bytearray(row);bad[548+160]^=1;validate(bad);volatile+=1
    report={'passed':True,'scope':'Direct assembly capture before and after actual Registry.initialize C++ return, before harness host cleanup','observed_rows':4,'required_preservation_corruptions_rejected':checks,'volatile_SIMD_distinctions_accepted':volatile,'preserved':'Actual x87 CW/SW/FTW/raw80, complete ENV28, MXCSR and ABI XMM6..15','volatile_XMM0_5_equality_claimed':False,'original_execution':False,'whole_M4_complete':False}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bindings[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(bindings,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();main(a.out)
