"""Recover the remaining fourteen import-free integer CRT roots as one batch."""
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage,read_binary,load_manifest,validate_identity
from bindings import FUNCTIONS as PINNED,INVENTORY_SHA
IMAGE_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
ROOTS={**{0x43aec0+i*0x20:26 for i in range(8)},0x467490:17,0x4674b0:17,0x4674d0:17,0x4b5b20:49,0x4c7940:27,0x4cfef0:29}
FUNCTIONS={**ROOTS,0x43ae30:25}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,text):
    if not ok:raise ValueError(text)
def recover(image,out,decoder):
    require(out.resolve().is_relative_to((ROOT/'reports/m4-integer-startup').resolve()),'Private integer recovery required')
    targets=[out/'report.json',out/'code.bin']+[out/f'{kind}-{entry:x}.{suffix}' for entry in FUNCTIONS for kind,suffix in (('code','bin'),('disassembly','txt'))]
    require(not any(p.exists() for p in targets),'Fresh integer recovery artifacts required')
    raw=read_binary(image);pe=PEImage(raw);validate_identity(raw,load_manifest(ROOT/'games/mw3/config/supported-binaries.json'),pe)
    require(hashlib.sha256(raw).hexdigest()==IMAGE_SHA,'Wrong admitted image')
    require(sha(decoder)=='a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a','Wrong pinned decoder')
    inventory=ROOT/'reports/m4-initializer-inventory/r1/report.json';data=json.loads(inventory.read_text())
    require(sha(inventory)==INVENTORY_SHA,'Frozen all-144 inventory differs')
    admitted=[r for r in data['roots'] if r.get('direct_branch_graph_import_free') and not r['FP_instruction_count'] and not r['FS_instruction_count'] and not r['unclassified_executable_literals']]
    remaining=[r for r in admitted if r['entry'] not in (0x410910,0x410940)]
    require([r['entry'] for r in remaining]==list(ROOTS),'Exact reviewed remaining integer root set differs')
    out.mkdir(parents=True,exist_ok=True);records=[];chunks=[]
    for entry,size in FUNCTIONS.items():
        offset,_=pe.rva_range(entry-pe.image_base,size);code=raw[offset:offset+size]
        path=out/f'code-{entry:x}.bin';path.write_bytes(code)
        cmd=[str(decoder),'--disassemble','--x86-asm-syntax=intel',f'--start-address={entry}',f'--stop-address={entry+size}',str(image)]
        run=subprocess.run(cmd,capture_output=True,check=True,timeout=30);disasm=out/f'disassembly-{entry:x}.txt';disasm.write_bytes(run.stdout)
        instructions=[]
        for line in run.stdout.decode().splitlines():
            m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*(\S.*)$',line)
            if m:instructions.append({'pc':int(m[1],16),'bytes':m[2].split(),'instruction':m[3]})
        require(instructions and instructions[0]['pc']==entry and instructions[-1]['pc']+len(instructions[-1]['bytes'])==entry+size,'Whole body boundary decode differs')
        require(not any(re.search(r'\b(call|fs:|fld|fst|fadd|fmul|fdiv|fsin|fcos|fpatan|fsqrt)\b',i['instruction']) for i in instructions),'Unexpected outgoing/service/FP/FS instruction')
        slot=next((r['slot'] for r in remaining if r['entry']==entry),None)
        require(sha(path)==PINNED[entry]['code_sha256'],'Complete body literal identity differs')
        records.append({'entry':entry,'entry_va':entry,'end_va':entry+size,'size_bytes':size,'file_offset':offset,'code_path':str(path.resolve()),'code_sha256':sha(path),'guest_ir_sha256':PINNED[entry]['guest_ir_sha256'],
                        'bundle_offset':sum(map(len,chunks)),'table_slot':slot,'instructions':instructions,
                        'decoder_command':cmd,'disassembly_sha256':sha(disasm)})
        chunks.append(code)
    bundle=out/'code.bin';bundle.write_bytes(b''.join(chunks))
    report={'schema_version':1,'profile':'m4-integer-startup-fourteen-roots','passed':True,'scope':'Exact complete body and direct-tail recovery only; no native/original comparison credit',
            'image_path':str(image.resolve()),'image_sha256':IMAGE_SHA,'inventory_path':str(inventory),'inventory_sha256':sha(inventory),
            'source_path':str(Path(__file__).resolve()),'source_sha256':sha(__file__),'decoder_path':str(decoder.resolve()),'decoder_sha256':sha(decoder),
            'code_path':str(bundle.resolve()),'code_sha256':sha(bundle),'code_bytes':len(bundle.read_bytes()),'roots':remaining,'functions':records,
            'shared_tail_entry':0x43ae30,'global_pages':[0x605000,0x60b000],
            'flags_scope':'Final XOR AF undefined for eight shared-tail roots and 4B5B20/4CFEF0; other flags observed, DF preserved; MOV/RET-only roots preserve flags'}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':True,'roots':len(remaining),'functions':len(records),'code_bytes':report['code_bytes'],'code_sha256':report['code_sha256']}))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--image',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--decoder',type=Path,required=True)
    a=p.parse_args();recover(a.image,a.out,a.decoder)
