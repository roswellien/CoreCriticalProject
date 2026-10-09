"""Extract one complete hash-admitted MW3 function into ignored local reports."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage,read_binary

IMAGE_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
CODE_SHA='fd939ea8ce1dc550fd08e7f2c2a2178ff063435cc7a8f5c5aafbf13eff32feaa'
ENTRY,END,SIZE=0x558290,0x5582bb,43
PAGE,PAGE_END=0x72c000,0x72d000
LLVM_SHA='34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb'


def require(ok,reason):
    if not ok:raise ValueError(reason)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extract(image_path,output,objdump):
    raw=read_binary(image_path);require(hashlib.sha256(raw).hexdigest()==IMAGE_SHA,'Wrong admitted MW3 image SHA256')
    image=PEImage(raw);require(image.image_base==0x400000 and image.size_of_image==0x5f5000,'Admitted image PE mapping changed')
    offset,_=image.rva_range(ENTRY-image.image_base,SIZE)
    section=next((s for s in image.sections if s['virtual_address']<=ENTRY-image.image_base and
                  END-image.image_base<=s['virtual_address']+s['virtual_size']),None)
    require(section is not None,'Complete code extent lacks one containing section')
    require(offset==0x157690 and section['executable'] and section['readable'] and not section['writable'],'Code section mapping/permissions changed')
    body=raw[offset:offset+SIZE];require(hashlib.sha256(body).hexdigest()==CODE_SHA,'Complete function code identity changed')
    global_section=next((s for s in image.sections if s['virtual_address']<=PAGE-image.image_base<
                         s['virtual_address']+s['virtual_size']),None)
    require(global_section and global_section['name']=='.data' and global_section['writable'] and global_section['readable'] and
            PAGE-image.image_base>=global_section['virtual_address']+global_section['raw_size'] and
            PAGE_END-image.image_base<=global_section['virtual_address']+global_section['virtual_size'],
            'Global guest page is not wholly admitted data zero-fill')
    call_offset,_=image.rva_range(0x5995dd-image.image_base,5);call=raw[call_offset:call_offset+5]
    require(call[0]==0xe8 and 0x5995e2+struct.unpack_from('<i',call,1)[0]==ENTRY,'Observed incoming complete CALL identity changed')
    run=subprocess.run([str(objdump),'--disassemble','--x86-asm-syntax=intel',f'--start-address={ENTRY}',f'--stop-address={END}',
                        str(image_path)],capture_output=True,text=True,check=True,timeout=30)
    instructions=[]
    for line in run.stdout.splitlines():
        match=re.fullmatch(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*(\S+)(?:\s+(.*))?',line)
        if match:
            code=bytes.fromhex(match[2]);instructions.append({'pc':int(match[1],16),'size':len(code),'mnemonic':match[3],
                'operands':match[4] or '', 'instruction_sha256':hashlib.sha256(code).hexdigest()})
    require(len(instructions)==11 and [i['mnemonic'] for i in instructions]==
            ['mov','mov','mov','mov','mov','mov','cdq','sub','sar','mov','ret'],'Complete reviewed instruction forms changed')
    pc=ENTRY
    for instruction in instructions:
        require(instruction['pc']==pc,'Instruction coverage has a gap/overlap');pc+=instruction['size']
    require(pc==END and instructions[-1]['pc']==0x5582b8 and instructions[-1]['operands']=='0x8','Complete RET8 boundary changed')
    require(instructions[-3]['operands']=='eax','Reviewed SAR count-one operand changed')
    output=output.resolve();require(output.is_relative_to((ROOT/'reports/m3-slice').resolve()),'Private extraction output must remain in ignored M3 reports')
    output.mkdir(parents=True,exist_ok=True)
    code_path=output/'sub_00558290.bin';code_path.write_bytes(body)
    globals_path=output/'global-page-initial.bin';globals_path.write_bytes(bytes(4096))
    disassembly=output/'private-original-disassembly.txt';disassembly.write_text(run.stdout)
    record={'schema_version':1,'status':'complete_private_image_slice_admitted','image_path':str(image_path.resolve()),
            'image_sha256':IMAGE_SHA,'image_bytes':len(raw),'image_base':image.image_base,'image_size':image.size_of_image,
            'entry_va':ENTRY,'end_va':END,'code_bytes':SIZE,'code_file_offset':offset,'code_sha256':CODE_SHA,
            'code_path':str(code_path),'instruction_count':11,'instructions':instructions,'outgoing_targets':[],
            'incoming_edge':{'call_va':0x5995dd,'return_va':0x5995e2,'target_va':ENTRY,'call_file_offset':call_offset,
                             'call_bytes':5,'call_sha256':hashlib.sha256(call).hexdigest()},
            'return':{'pc':0x5582b8,'callee_cleanup':8},'code_section':section,
            'global_page':{'base':PAGE,'end':PAGE_END,'size':4096,'permissions':'rw','initial':'PE virtual zero-fill',
                           'initial_path':str(globals_path),'initial_sha256':sha(globals_path),'section':global_section},
            'global_writes':{'base':0x72c1e4,'size':20,'addresses':[0x72c1e4,0x72c1e8,0x72c1ec,0x72c1f0,0x72c1f4]},
            'stack_page':{'base':0x20001000,'size':4096,'permissions':'rw','frame_bytes':12,'return_sentinel':0x10000100},
            'flag_policy':{'defined_mask':0xcc5,'undefined_AF':True,'guest_instruction':'SAR r32,1'},
            'source_tools':{str(Path(__file__).resolve()):sha(Path(__file__)),str(ROOT/'tools/analysis/pe.py'):sha(ROOT/'tools/analysis/pe.py'),
                            str(objdump.resolve()):sha(objdump)},'private_disassembly_sha256':sha(disassembly),
            'scope':'Complete observed function only; no enclosing caller, game startup or gameplay claim.'}
    path=output/'slice.json';path.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'slice_record_sha256':sha(path),'entry_va':ENTRY,'code_sha256':CODE_SHA,'size':SIZE,'image_sha256':IMAGE_SHA},indent=2))
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--image',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--objdump',type=Path,required=True)
    args=parser.parse_args();extract(args.image,args.output,args.objdump)
