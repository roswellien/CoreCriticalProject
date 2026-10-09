"""Hash-admit and privately extract a complete startup initializer route."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage,read_binary,load_manifest,validate_identity
IMAGE_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
CODE_SHA='f5a91456f4eb0ecab7e5cd689b1d1465dc4e2610bc879397e500b02d00946af7'
ENTRY,END,SIZE=0x410910,0x410934,36
LLVM_OBJDUMP_SHA='a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok,reason):
    if not ok:raise ValueError(reason)
def extract(image_path,output,objdump):
    require(sha(objdump)==LLVM_OBJDUMP_SHA,'Wrong pinned instruction decoder')
    raw=read_binary(image_path);image=PEImage(raw)
    validate_identity(raw,load_manifest(ROOT/'games/mw3/config/supported-binaries.json'),image)
    require(hashlib.sha256(raw).hexdigest()==IMAGE_SHA,'Wrong admitted executable')
    offset,_=image.rva_range(ENTRY-image.image_base,SIZE)
    code=raw[offset:offset+SIZE]
    require(offset==0xfd10 and hashlib.sha256(code).hexdigest()==CODE_SHA,'Complete initializer route bytes changed')
    require(image.rva_u32(0x5e0058-image.image_base)==ENTRY,'Actual CRT initializer pointer changed')
    section=next(s for s in image.sections if s['virtual_address']<=ENTRY-image.image_base<s['virtual_address']+s['virtual_size'])
    require(section['executable'] and not section['writable'],'Initializer section permissions changed')
    global_section=next(s for s in image.sections if s['virtual_address']<=0x604000-image.image_base<s['virtual_address']+s['virtual_size'])
    require(global_section['writable'] and 0x604000-image.image_base>=global_section['virtual_address']+global_section['raw_size'] and
            0x605000-image.image_base<=global_section['virtual_address']+global_section['virtual_size'],'Data page is not wholly PE zero-fill')
    run=subprocess.run([str(objdump),'--disassemble','--x86-asm-syntax=intel',f'--start-address={ENTRY}',f'--stop-address={END}',str(image_path)],capture_output=True,check=True,timeout=30)
    instructions=[]
    for line in run.stdout.decode().splitlines():
        m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}[ ]*)+)\t(.+)$',line)
        if m:
            address,body,asm=int(m[1],16),bytes.fromhex(m[2]),re.sub(r'\s+',' ',m[3].strip())
            require(raw[image.rva_range(address-image.image_base,len(body))[0]:][:len(body)]==body,'Decoder byte mismatch')
            instructions.append({'pc':address,'size':len(body),'assembly':asm,'sha256':hashlib.sha256(body).hexdigest()})
    cursor=ENTRY
    for i in instructions:require(i['pc']==cursor,'Uncovered initializer extent');cursor+=i['size']
    require(cursor==END,'Initializer extent differs')
    reachable=[i for i in instructions if i['pc']==ENTRY or i['pc']>=0x410920]
    require(len(reachable)==8 and [i['assembly'].split(' ')[0] for i in reachable]==['jmp','mov','mov','mov','add','dec','jne','ret'],'Closed wrapper/body instruction forms differ')
    output=output.resolve();require(output.is_relative_to((ROOT/'reports/m4-initializer').resolve()),'Private output must stay in ignored M4 initializer reports')
    output.mkdir(parents=True,exist_ok=True)
    (output/'code.bin').write_bytes(code);(output/'global-page-initial.bin').write_bytes(bytes(4096))
    (output/'disassembly.txt').write_bytes(run.stdout)
    report={'schema_version':1,'image_sha256':IMAGE_SHA,'image_path':str(image_path.resolve()),
            'code_sha256':CODE_SHA,'code_path':str(output/'code.bin'),'entry_va':ENTRY,'end_va':END,
            'code_bytes':SIZE,'code_file_offset':offset,'instructions':instructions,'reachable_instructions':reachable,
            'unreachable_padding_bytes':11,'outgoing_targets':[],'direct_initializer_slot':0x5e0058,
            'global_page':{'base':0x604000,'size':4096,'initial_path':str(output/'global-page-initial.bin'),'initial_sha256':sha(output/'global-page-initial.bin')},
            'stack_page':{'base':0x20001000,'size':4096,'frame_bytes':4,'return_sentinel':0x10000100},
            'source_tools':{str(Path(__file__).resolve()):sha(Path(__file__)),str(ROOT/'tools/analysis/pe.py'):sha(ROOT/'tools/analysis/pe.py'),
                            str(ROOT/'games/mw3/config/supported-binaries.json'):sha(ROOT/'games/mw3/config/supported-binaries.json'),str(objdump.resolve()):sha(objdump)},
            'scope':'Complete real initializer wrapper and body, invoked offline; other143 initializers and native CRT/MFC/menu remain unimplemented'}
    (output/'slice.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'entry_va':ENTRY,'code_sha256':CODE_SHA,'size_bytes':SIZE,'reachable_instruction_count':8}))
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('image','output','objdump'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();extract(a.image,a.output,a.objdump)
