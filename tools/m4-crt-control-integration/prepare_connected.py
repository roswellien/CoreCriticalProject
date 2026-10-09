"""Exact game wrapper/provider original pages, explicitly declared one-slot fixup."""
import hashlib,json,pathlib,struct,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-crt'))
from recover_provider import PE
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def prepare(out):
 assert not out.exists() and out.is_relative_to(ROOT/'reports/m4-crt-control-integration')
 prep=ROOT/'reports/m4-crt-control-integration/preparation-r1/report.json';assert sha(prep)=='2ff6fb125e0abae0b125f0e00e430cf5e8e4a0ab3a22b1c1eb9fefcb65c8175a';m=json.loads(prep.read_text());game=ROOT/'MW3/Mech3.exe';provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';assert sha(game)==m['game_image_sha256'] and sha(provider)==m['provider_sha256'];pe=PE(game,m['game_image_sha256'])
 gamepage=bytearray([0xcc]*4096)
 for row in m['complete_source_ranges']:
  body=game.read_bytes()[row['file_offset']:row['file_offset']+row['size_bytes']];assert hashlib.sha256(body).hexdigest()==row['sha256'];a=row['address'];gamepage[a-0x5ac000:a-0x5ac000+len(body)]=body
 # Instrumentation starts at the declared original outer CALL continuation;
 # neither wrapper nor thunk nor any provider body is changed.
 gamepage[0x436]=0xe9;struct.pack_into('<I',gamepage,0x437,(0x10000100-0x5ac43b)&0xffffffff)
 iat=bytearray([0xa5]*4096);struct.pack_into('<I',iat,0x578,0x780042e1)
 old=ROOT/'reports/m4-crt-control/research-r1/pack.bin';b=old.read_bytes();assert b[:8]==b'MW4CFPK1' and len(b)==8220;pages=[(0x5ac000,1,gamepage),(0x5bb000,2,iat)]
 for i in range(2):a,role=struct.unpack_from('<II',b,12+i*4104);assert (a,role)==((0x78004000,1) if i==0 else (0x78011000,1));pages.append((a,role,b[20+i*4104:20+i*4104+4096]))
 pack=b'MW4CIPK1'+struct.pack('<I',4)+b''.join(struct.pack('<II',a,role)+p for a,role,p in pages);assert len(pack)==16428
 out.mkdir(parents=True);(out/'pack.bin').write_bytes(pack);(out/'probe_spec.hpp').write_text('#pragma once\nnamespace mw34::m4_crt_control_integration { inline constexpr char pack_sha[]="'+sha(out/'pack.bin')+'"; }\n')
 (out/'report.json').write_text(json.dumps({'passed':True,'scope':'Connected exact original wrapper/thunk/four-provider pages; preparation only','preparation_path':str(prep),'preparation_sha256':sha(prep),'game_path':str(game),'game_sha256':sha(game),'provider_path':str(provider),'provider_sha256':sha(provider),'consumed_provider_pack_path':str(old),'consumed_provider_pack_sha256':sha(old),'pack_sha256':sha(out/'pack.bin'),'pages':[{'address':a,'role':role,'sha256':hashlib.sha256(p).hexdigest()}for a,role,p in pages],'original_declared_loader_IAT_resolution':{'slot':0x5bb578,'target':0x780042e1,'native_raw_IAT_unchanged':True},'instrumentation':{'game_jump_site':0x5ac436,'capture_destination':0x10000100,'source_bytes_changed':False},'original_or_native_executed':False,'whole_M4_complete':False,'sources':{str(pathlib.Path(__file__)):sha(__file__),str(ROOT/'tools/m4-crt/recover_provider.py'):sha(ROOT/'tools/m4-crt/recover_provider.py')}},indent=2)+'\n')
if __name__=='__main__':prepare(pathlib.Path(sys.argv[1]).resolve())
