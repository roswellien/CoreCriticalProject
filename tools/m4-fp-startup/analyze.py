"""Validate actual hardware captures and report measured FP outputs/metadata.

Checks structure, input/ABI/host isolation, actual writable spans and repeated
observations. This is not an oracle for native FP equivalence or all startup.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys
sys.dont_write_bytecode=True

RECORD_BYTES=75988
MEMORY_BYTES=9*4096
ROOTS=(0x4133c0,0x4adb50,0x4b5af0,0x4b7020,0x4c78f0,0x4c79d0,0x4ce5a0,0x4ce5c0,0x4ce5e0,0x4ce600)
CW=(0x007f,0x047f,0x087f,0x0c7f,0x027f,0x067f,0x0a7f,0x0e7f,0x037f,0x077f,0x0b7f,0x0f7f)
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e1000,0x5e8000,0x604000,0x60b000,0x20001000)

def require(ok,why):
    if not ok:
        raise ValueError(why)

def bind(path):
    path=Path(path).resolve()
    with path.open('rb') as f:
        sha=hashlib.file_digest(f,'sha256').hexdigest()
    return {'path':str(path),'size_bytes':path.stat().st_size,'sha256':sha}

def env_fields(env):
    return {'CW':struct.unpack_from('<H',env,0)[0],'SW':struct.unpack_from('<H',env,4)[0],
            'TW':struct.unpack_from('<H',env,8)[0],'FIP':struct.unpack_from('<I',env,12)[0],
            'FCS':struct.unpack_from('<H',env,16)[0],'FOP':struct.unpack_from('<H',env,18)[0]&0x7ff,
            'FDP':struct.unpack_from('<I',env,20)[0],'FDS':struct.unpack_from('<H',env,24)[0]}

def memory_offset(address):
    page=address&~4095
    require(page in PAGES,'Span outside captured memory')
    return PAGES.index(page)*4096+(address&4095)

def analyze(blob,spec,pack):
    require(blob[:8]==b'MW4FPO01','Output magic differs')
    require(len(blob)==24+480*RECORD_BYTES,'Output extent differs')
    require(struct.unpack_from('<4I',blob,8)==(1,480,9,4096),'Output header differs')
    require(pack[:12]==b'MW4FPK01'+struct.pack('<I',15),'Input pack header differs')
    initial=b''.join(pack[12+i*4104+8:12+(i+1)*4104] for i in range(6,15))
    initial=bytearray(initial)
    struct.pack_into('<I',initial,memory_offset(0x20001800),0x10000100)
    by_entry={r['entry']:r for r in spec['roots']}
    results=[];repeats={};metadata_distinctions=0
    for index in range(480):
        offset=24+index*RECORD_BYTES
        repeat,entry,cw,top,status=struct.unpack_from('<5I',blob,offset)
        case=index%240
        expected=(index//240,ROOTS[case//24],CW[(case%24)//2],(0,7)[case%2],0)
        require((repeat,entry,cw,top,status)==expected,'Capture case tag/order differs')
        before=struct.unpack_from('<10I',blob,offset+20)
        after=struct.unpack_from('<10I',blob,offset+60)
        wanted=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,
                0x92837465,0x56473829,0xaabbccdd,0x202,entry)
        require(before==wanted,'Actual entry CPU differs')
        wanted_after=list(before);wanted_after[4]+=4;wanted_after[9]=0x10000100
        require(after==tuple(wanted_after),'Actual preserved CPU/return differs')
        fx=[blob[offset+100+i*512:offset+100+(i+1)*512] for i in range(4)]
        env=[blob[offset+2148+i*28:offset+2148+(i+1)*28] for i in range(4)]
        require(fx[2][:5]==fx[3][:5] and fx[2][24:28]==fx[3][24:28] and env[2]==env[3],
                'Host control/legacy metadata restoration differs')
        require(all(fx[2][32+i*16:42+i*16]==fx[3][32+i*16:42+i*16] for i in range(8)) and
                fx[2][160:288]==fx[3][160:288],'Host x87/XMM restoration differs')
        require(struct.unpack_from('<HHB',fx[0])==(cw,top<<11,0) and
                fx[0][6:24]==bytes(18) and fx[0][32:288]==bytes(256) and
                struct.unpack_from('<I',fx[0],24)[0]==0x1f80,'Actual starting FP domain differs')
        eb,ea=map(env_fields,env[:2])
        require(eb=={'CW':cw,'SW':top<<11,'TW':0xffff,'FIP':0,'FCS':0,'FOP':0,'FDP':0,'FDS':0},
                'Actual starting legacy environment differs')
        require(ea['CW']==cw and (ea['SW']>>11)&7==top and ea['TW']==0xffff,
                'Original CW/TOP/empty-stack completion differs')
        require(struct.unpack_from('<H',fx[1],0)[0]==ea['CW'] and
                struct.unpack_from('<H',fx[1],2)[0]==ea['SW'] and fx[1][4]==0 and
                fx[1][24:28]==fx[0][24:28] and fx[1][160:288]==fx[0][160:288],
                'Actual FX/ENV or vector preservation differs')
        root=by_entry[entry]
        last_fp=next(r for r in reversed(root['instructions']) if r['mnemonic'].startswith('f'))
        code=bytes.fromhex(last_fp['bytes'])
        last_write=next(r for r in reversed(root['write_spans']) if r['mnemonic']=='fstp')
        require(ea['FIP']==last_fp['pc'] and ea['FOP']==((code[0]&7)<<8|code[1]) and
                ea['FDP']==last_write['address'] and ea['FCS']!=0 and ea['FDS']!=0,
                'Actual legacy last-instruction/operand metadata differs')
        # Record the distinction; do not replace actual FX metadata with ENV.
        fx_metadata={'FOP':struct.unpack_from('<H',fx[1],6)[0]&0x7ff,
                     'FIP':struct.unpack_from('<I',fx[1],8)[0],
                     'FDP':struct.unpack_from('<I',fx[1],16)[0]}
        distinction=any(fx_metadata[k]!=ea[k] for k in fx_metadata)
        metadata_distinctions+=distinction
        memory_before=blob[offset+2260:offset+2260+MEMORY_BYTES]
        memory_after=blob[offset+2260+MEMORY_BYTES:offset+RECORD_BYTES]
        require(memory_before==initial,'Actual data/stack input differs')
        allowed=set()
        outputs=[]
        for span in root['write_spans']:
            start=memory_offset(span['address']);allowed.update(range(start,start+span['size']))
            value=memory_after[start:start+span['size']]
            outputs.append({'address':span['address'],'bytes':value.hex(),
                            'float32':struct.unpack('<f',value)[0] if span['size']==4 else None})
        require(all(a==b or i in allowed for i,(a,b) in enumerate(zip(memory_before,memory_after))),
                'Observed write escaped exact root spans')
        guest=(before,after,fx[0],fx[1],env[0],env[1],memory_before,memory_after)
        if repeat==0:
            repeats[case]=guest
        else:
            require(guest==repeats[case],'Repeated original guest observations differ')
        results.append({'case':index,'entry':entry,'CW':cw,'TOP':top,'repeat':repeat,
                        'legacy_ENV':ea,'FX_metadata':fx_metadata,'metadata_distinction':distinction,
                        'outputs':outputs})
    return {'passed':True,'scope':'Actual original FP research only; no native equivalence, full startup or menu proof',
            'records':480,'roots':10,'repeat_comparisons':240,'metadata_distinctions':metadata_distinctions,
            'domain':'Exact PE constants/BSS inputs; 12 masked CW; empty x87; TOP0/7; fixed ABI and address pages',
            'exclusions':['nonempty x87 input','all8TOP','directed alternate constants/integers','unmasked traps',
                          'other hardware configurations','native FP computation/serialization','connected initializer ordering',
                          'protected Remill State/events unavailable on original hardware'],
            'observations':results}

def main():
    extraction,run,output=map(Path,sys.argv[1:4])
    require(not output.exists(),'Fresh analysis report required')
    spec=json.loads((extraction/'extraction.json').read_text())
    pack=(extraction/'pages.bin').read_bytes()
    require(hashlib.sha256(pack).hexdigest()==spec['pack']['sha256'],'Input pack binding changed')
    result=analyze((run/'original.bin').read_bytes(),spec,pack)
    result['inputs']=[bind(extraction/n) for n in ('extraction.json','pages.bin')]+[bind(run/n) for n in ('original.bin','execution.log')]
    result['analyzer']=bind(__file__)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','records','roots','repeat_comparisons','metadata_distinctions')}))

if __name__=='__main__':
    main()
