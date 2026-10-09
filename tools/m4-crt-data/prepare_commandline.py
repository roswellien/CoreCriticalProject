"""Private original command-line writer fragment with an explicit authored capture jump."""
import argparse,hashlib,json,pathlib,struct,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-crt'))
from recover_provider import PE,PROVIDER_SHA,bind
def main(out):
 assert out.is_relative_to(ROOT/'reports/m4-crt-data') and not out.exists()
 p=PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',PROVIDER_SHA);source=p.read(0x7800188c-p.base,11);h=hashlib.sha256(source).hexdigest();assert h=='6300f3f77dc2f2ce6ea36590028dd7f3b078c721a08d6daac27ebc8c636b5ac3'
 code=bytearray([0xcc]*4096);code[0x88c:0x897]=source;code[0x897]=0xe9;struct.pack_into('<I',code,0x898,(0x10000100-0x7800189c)&0xffffffff)
 pack=b'MW4CMPK1'+struct.pack('<II',0x78001000,4096)+code;out.mkdir(parents=True);(out/'pack.bin').write_bytes(pack);(out/'original-fragment.bin').write_bytes(source);packhash=hashlib.sha256(pack).hexdigest();(out/'commandline_spec.hpp').write_text('#pragma once\nnamespace mw34::m4_crt_data { inline constexpr char pack_sha[]="'+packhash+'"; }\n')
 report={'passed':True,'scope':'Private preparation of exact original initialization writer fragment and separately identified authored capture jump','provider':bind(p.path),'source':bind(__file__),'PE_parser':bind(ROOT/'tools/m4-crt/recover_provider.py'),'original_begin':0x7800188c,'original_end_exclusive':0x78001897,'original_size':11,'original_file_offset':p.offset(0x7800188c-p.base,11),'original_sha256':h,'actual_indirect_call_IAT':0x7802e034,'actual_stdcall_return':0x78001892,'initialized_global':0x78037174,'authored_capture_jump_site':0x78001897,'authored_capture_destination':0x10000100,'pack_sha256':packhash,'full_process_attach_executed':False,'whole_M4_complete':False};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('output',type=pathlib.Path);v=a.parse_args();main(v.output.resolve())
