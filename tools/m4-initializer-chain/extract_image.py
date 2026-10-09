"""Hash-admit the two adjacent CRT roots and complete connected callees."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/analysis'))
from pe import PEImage, read_binary, load_manifest, validate_identity
IMAGE_SHA = '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
DOSSIER_SHA = '7521a5ed5229de80df26d98a47a31ae865203826d4ca614e88cd46e01ca5037c'
FUNCTIONS = {
    0x410910: (36,0xfd10,'f5a91456f4eb0ecab7e5cd689b1d1465dc4e2610bc879397e500b02d00946af7','8dc7dc98da449480bd1ed4c472a2e65f79b27a2a5bb4d4fcd0e4f7f189d1b3fb'),
    0x410940: (203,0xfd40,'483e3a9fd5dccbe4ce508f1cfa05f483ffa055bef943a5d065e1ecd3f8d3c165','f7502f131e188e65a861eb4acd0c3081b1c172fe1ee5d204299247d694be9f09'),
    0x40daf0: (23,0xcef0,'52af66aa3019e79ddf6a585457016cf7600d6b5d88ca709a6dd3ba80eaa28bd8','c125a11860a90a57646a86722808d471a91099c8fd7a0814945227df32e88130'),
    0x40db30: (43,0xcf30,'c97edf4e6b211c619b0ec53ed23d5afb2e933ad128c4a5d1fd57ac0900144e65','d1c6b4a8264df0a2b5040907332928d3a6ce42a8d63f1ea37d6a3a1621a0daf1'),
}
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok,why):
    if not ok:raise ValueError(why)
def extract(image_path,out,objdump):
    dossier=ROOT/'reports/m4-startup/next-initializer-410940/pins.json'
    require(sha(dossier)==DOSSIER_SHA,'Frozen candidate dossier identity differs')
    pins=json.loads(dossier.read_text())
    for binding in pins['bindings']:
        path=Path(binding['path']);require(path.stat().st_size==binding['size_bytes'] and sha(path)==binding['sha256'],'Frozen dossier file changed: '+str(path))
    require(sha(objdump)=='a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a','Wrong pinned decoder')
    raw=read_binary(image_path);image=PEImage(raw)
    validate_identity(raw,load_manifest(ROOT/'games/mw3/config/supported-binaries.json'),image)
    require(hashlib.sha256(raw).hexdigest()==IMAGE_SHA,'Wrong admitted image')
    for slot,entry in ((0x5e0058,0x410910),(0x5e005c,0x410940)):
        require(image.rva_u32(slot-image.image_base)==entry,'Adjacent CRT root changed')
    out=out.resolve();require(out.is_relative_to((ROOT/'reports/m4-initializer-chain').resolve()),'Private extraction outside ignored chain reports')
    out.mkdir(parents=True,exist_ok=True)
    chunks=[];records=[]
    for entry,(size,offset,expected,ir) in FUNCTIONS.items():
        actual,_=image.rva_range(entry-image.image_base,size)
        require(actual==offset,'Function file offset changed')
        code=raw[offset:offset+size];require(hashlib.sha256(code).hexdigest()==expected,'Complete function identity changed')
        path=out/f'code-{entry:x}.bin';path.write_bytes(code)
        command=[str(objdump),'--disassemble','--x86-asm-syntax=intel',f'--start-address={entry}',f'--stop-address={entry+size}',str(image_path)]
        run=subprocess.run(command,capture_output=True,check=True,timeout=30)
        (out/f'disassembly-{entry:x}.txt').write_bytes(run.stdout)
        records.append({'entry_va':entry,'end_va':entry+size,'size_bytes':size,'file_offset':offset,'code_sha256':expected,'guest_ir_sha256':ir,'bundle_offset':sum(map(len,chunks)),'code_path':str(path),'decoder_command':command})
        chunks.append(code)
    bundle=out/'code.bin';bundle.write_bytes(b''.join(chunks))
    global_section=next(s for s in image.sections if s['virtual_address']<=0x604000-image.image_base<s['virtual_address']+s['virtual_size'])
    require(global_section['writable'] and 0x604000-image.image_base>=global_section['virtual_address']+global_section['raw_size'] and 0x605000-image.image_base<=global_section['virtual_address']+global_section['virtual_size'],'Shared global page is not wholly writable PE zero-fill')
    initial=out/'global-page-initial.bin';initial.write_bytes(bytes(4096))
    record={'schema_version':1,'profile':'m4-connected-initializers-410910-410940','image_path':str(image_path.resolve()),'image_sha256':IMAGE_SHA,
            'code_path':str(bundle),'code_sha256':sha(bundle),'code_bytes':bundle.stat().st_size,'functions':records,
            'global_page':{'base':0x604000,'size':4096,'initial_path':str(initial),'initial_sha256':sha(initial)},
            'stack_page':{'base':0x20001000,'size':4096,'required_relative_span':[-28,4],'return_sentinel':0x10000100},
            'dossier_pins':{'path':str(dossier),'sha256':DOSSIER_SHA,'bindings_verified':len(pins['bindings'])},
            'source_tools':{str(Path(__file__)):sha(Path(__file__)),str(ROOT/'tools/analysis/pe.py'):sha(ROOT/'tools/analysis/pe.py'),str(ROOT/'games/mw3/config/supported-binaries.json'):sha(ROOT/'games/mw3/config/supported-binaries.json'),str(objdump):sha(objdump)}}
    (out/'slice.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'functions':len(records),'code_bytes':record['code_bytes'],'code_sha256':record['code_sha256']}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--image',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--objdump',type=Path,required=True)
    a=p.parse_args();extract(a.image,a.output,a.objdump)
