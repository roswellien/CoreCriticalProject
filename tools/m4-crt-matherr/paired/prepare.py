"""New paired fixture preparation, retaining the root's frozen leaf/lift."""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/m4-crt'))
from recover_provider import PE,IMAGE_SHA,PROVIDER_SHA
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(out):
 assert out.is_relative_to(ROOT/'reports/m4-crt-matherr') and not out.exists()
 frozen=ROOT/'reports/m4-crt-matherr/preflight-seal-r2/pins.json'
 assert sha(frozen)=='62a7a42bd1f59f1ca24b19e6e9e0729c2e6033adb587eaccb964910b398692e7'
 pins=json.loads(frozen.read_text())['files']
 for p,h in pins.items():assert sha(p)==h,p
 game=PE(ROOT/'MW3/Mech3.exe',IMAGE_SHA);provider=PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',PROVIDER_SHA)
 assert game.read(0x5ac428-0x400000,6)==bytes.fromhex('ff150cb55b00')
 assert game.read(0x5ac423-0x400000,5)==bytes.fromhex('68b0e75100')
 leaf=provider.read(0xb38f,17);assert sha(ROOT/'reports/m4-crt-matherr/preparation-r1/source.bin')==hashlib.sha256(leaf).hexdigest()
 out.mkdir(parents=True);(out/'prepare-source.py').write_bytes(Path(__file__).read_bytes())
 pack=bytearray(b'MW4MTK01'+struct.pack('<I',2));instrumentation=[]
 for base,owner in ((0x5ac000,game),(0x7800b000,provider)):
  page=bytearray(owner.read(base-(0x400000 if owner is game else 0x78000000),4096))
  if owner is game:
   at=0x42e;before=bytes(page[at:at+5]);page[at:at+5]=b'\xe9'+struct.pack('<I',(0x10000100-0x5ac433)&0xffffffff)
   instrumentation.append({'site':0x5ac42e,'original_bytes_hex':before.hex(),'authored_capture_target':0x10000100,'patch_bytes_hex':page[at:at+5].hex(),'original_instructions_at_capture_site_executed':False})
  pack+=struct.pack('<II',base,1)+page
 (out/'pack.bin').write_bytes(pack)
 spec='#pragma once\nnamespace mw34::m4_crt_matherr_paired { inline constexpr char pack_sha[]="'+sha(out/'pack.bin')+'"; }\n'
 (out/'pack_spec.hpp').write_text(spec)
 report={'passed':True,'scope':'Source-bound paired fixture only, no execution credit','records':1536,'original_stride':26836,'native_stride':33964,'provider':{'path':str(provider.path),'sha256':PROVIDER_SHA,'entry':0x7800b38f,'source_sha256':hashlib.sha256(leaf).hexdigest()},'game':{'path':str(game.path),'sha256':IMAGE_SHA,'static_callsite':0x5ac428,'static_named_slot':0x5bb50c,'static_argument':0x51e7b0,'caller_instructions_executed':False},'capture_instrumentation':instrumentation,'coherent_profile_depths':[0,1,7,8,0,1,7,8],'sticky_status_by_arg_index':'0 for0..3, IE|ZE|PE=0x25 for4..7; all masked','page_order':[0x20001000,0x78039000,0x7803b000],'synthetic_leaf_frame':{'ESP':0x200017fc,'return':0x5ac42e,'argument_address':0x20001800},'root_preflight_pins':str(frozen),'root_preflight_pins_sha256':sha(frozen),'whole_M4_complete':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 p={str(Path(x).resolve()):sha(x) for x in [Path(__file__),ROOT/'tools/m4-crt/recover_provider.py',game.path,provider.path,frozen,ROOT/'tools/m4-crt-matherr/paired/protocol.hpp']}
 p.update({str(x.resolve()):sha(x) for x in out.iterdir() if x.is_file()});(out/'pins.json').write_text(json.dumps({'files':p},indent=2)+'\n')
 print(json.dumps({'passed':True,'pack_sha':sha(out/'pack.bin'),'report_sha':sha(out/'report.json')}))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
