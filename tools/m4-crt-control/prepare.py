"""Exact original provider pages and complete cold/hot CFG lifting inputs."""
import argparse,hashlib,json,pathlib,struct,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-crt'))
from recover_provider import PE
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
RANGES=[(0x780042e1,303,'adf05ce99957b1a9d6c33dce1dda80a595cda795085d2794935bb4d78a46f47b'),(0x7801129b,125,'b48e01a7f8be0f6c5f477cb30911f7dc92adcca417894943587560507db19b88')]
ENTRIES=[0x780042e1,0x780042f7,0x7800432c,0x7800439f]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main(out):
 assert not out.exists() and out.is_relative_to(ROOT/'reports/m4-crt-control');provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';assert sha(provider)==PROVIDER_SHA
 pe=PE(provider,PROVIDER_SHA);pages={0x78004000:bytearray([0xcc]*4096),0x78011000:bytearray([0xcc]*4096)};dense=bytearray([0xcc]*(0x78011318-0x780042e1));ranges=[]
 for va,size,h in RANGES:
  offset=pe.offset(va-pe.base,size);body=provider.read_bytes()[offset:offset+size];assert hashlib.sha256(body).hexdigest()==h;page=va&~4095;pages[page][va-page:va-page+size]=body;dense[va-0x780042e1:va-0x780042e1+size]=body;ranges.append({'address':va,'size_bytes':size,'file_offset':offset,'sha256':h})
 pack=b'MW4CFPK1'+struct.pack('<I',2)+b''.join(struct.pack('<II',a,1)+b for a,b in pages.items());assert len(pack)==8220
 out.mkdir(parents=True);(out/'pack.bin').write_bytes(pack);(out/'dense-lift.bin').write_bytes(dense)
 sem=ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc';assert sha(sem)=='618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca'
 for entry in ENTRIES:
  # Complete reachable provider bytes; CC holes are authored traps. The CFG
  # admission below must reject any reached hole, unknown or missing block.
  flags=['--arch=x86','--os=windows','--address='+str(0x780042e1),'--entry_address='+str(entry),'--bytes='+dense.hex(),'--semantics_dir='+str(sem.parent),'--ir_out='+str(out/f'guest-{entry:x}.ll')]
  (out/f'flags-{entry:x}.txt').write_text('\n'.join(flags)+'\n')
 (out/'probe_spec.hpp').write_text('#pragma once\nnamespace mw34::m4_crt_control { inline constexpr char pack_sha[]="'+sha(out/'pack.bin')+'"; }\n')
 (out/'report.json').write_text(json.dumps({'passed':True,'scope':'Exact source extraction and static lift inputs only; execution pending','provider_path':str(provider),'provider_sha256':PROVIDER_SHA,'source_ranges':ranges,'entries':ENTRIES,'pack_sha256':sha(out/'pack.bin'),'dense_sha256':sha(out/'dense-lift.bin'),'semantics_path':str(sem),'semantics_sha256':sha(sem),'sources':{str(p):sha(p) for p in [pathlib.Path(__file__),ROOT/'tools/m4-crt/recover_provider.py']},'whole_M4_complete':False},indent=2)+'\n');print(out)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output',type=pathlib.Path);a=p.parse_args();main(a.output.resolve())
