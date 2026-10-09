"""Exact read-only work-area initializer recovery; private original bytes only."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-spi-workarea'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(out):
    out=Path(out).resolve();out.relative_to(BASE);out.mkdir(parents=True,exist_ok=False)
    parser=ROOT/'tools/analysis/pe.py';sp=importlib.util.spec_from_file_location('pe_read_only',parser);pe=importlib.util.module_from_spec(sp);sp.loader.exec_module(pe)
    image=ROOT/'MW3/Mech3.exe';need=sha(image);assert need=='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
    obj=pe.PEImage(image.read_bytes());old=ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json';g=json.loads(old.read_text())[str(0x482cf0)]
    assert len(g['instructions'])==22 and g['local_decode_closed'] and not g['FP_sites'] and not g['FS_sites']
    def get(a,n):o,_=obj.rva_range(a-0x400000,n);return obj.data[o:o+n]
    assert struct.unpack('<I',get(0x5e0110,4))[0]==0x482cf0
    code=bytearray([0xcc]*4096)
    for x in g['instructions']:
        b=bytes.fromhex(x['bytes']);assert get(x['pc'],len(b))==b;code[x['pc']-0x482000:x['pc']-0x482000+len(b)]=b
    # Authored capture broker; never overlaps a recovered instruction.
    assert code[0xff0:0xff5]==b'\xcc'*5
    pages=[(0x482000,1,code),(0x5bb000,2,bytearray(4096)),(0x5e6000,0,bytearray(get(0x5e6000,4096))),(0x608000,2,bytearray(4096)),(0x20001000,2,bytearray([0xa5]*4096))]
    pack=b'MW4SPIP1'+struct.pack('<I',5)+b''.join(struct.pack('<II',a,p)+b for a,p,b in pages);(out/'pack.bin').write_bytes(pack)
    identities={str(p):sha(p) for p in [image,parser,old,Path(__file__)]}
    for p in [Path('C:/Windows/SysWOW64/user32.dll'),Path('C:/Windows/System32/user32.dll'),Path('C:/Windows/SysWOW64/win32u.dll'),Path('C:/Windows/SysWOW64/ntdll.dll')]:identities[str(p)]=sha(p)
    body=g['instructions'];report=dict(passed_static=True,entry=0x482cf0,slot=0x5e0110,body=body,call_site=0x482cdd,owning_IAT=0x5bb6dc,return_pc=0x482ce3,args=[0x30,0,0x608fa0,0],source24=dict(address=0x5e6000,size=24,file_offset=obj.rva_range(0x5e6000-0x400000,24)[0],hex=get(0x5e6000,24).hex()),destination_prefix=dict(address=0x608f88,size=24),RECT_output=dict(address=0x608fa0,size=16,fields='4 signed little-endian LONG32'),service_entry=dict(ESP='S-32',EAX=0x608fa0,EBX=0x608f88,ECX=0,ESI=0x5e6018,EDI=0x608fa0,EDX='incoming',stack=['return482CE3','action30','uiParam0','pvParam608FA0','flags0']),post_call_instructions=[x for x in body if 0x482ce3<=x['pc']<=0x482ce8],service_output_liveness=dict(BOOL='discarded by MOVEAX,EBX',ECX='unread after CALL',EDX='unread after CALL',arithmetic_flags='unread after CALL; MOV,POP,RET preserve them',FP_SIMD='no reached caller reads FP/SIMD'),defined_final_outputs=dict(EAX=0x608f88,ESP='S+4',EIP=0x482ff0,EBX_ESI_EDI_EBP='incoming preserved',DF=0,prefix='original24 source bytes',RECT='actual query16 bytes; no invented dimensions'),proposal=dict(native='host SystemParametersInfoA(30,0,&ownedRECT,0); exact guest16 read/copyback through GuestMemory, no guest-pointer casting',original='separate x86 original/provider broker; actual query+ABI snapshots; never final native backend',unsupported='caller-volatile ECX/EDX/arithmetic flags and any service-volatile FP/SIMD observations are retained but no fabricated equality; failure BOOL is not converted to exception or defaults; no connected startup credit'),official_contract='https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfoa',pack=dict(path=str(out/'pack.bin'),sha256=sha(out/'pack.bin')),bindings=identities,execution=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    header='#pragma once\nnamespace mw34::spi {\ninline constexpr const char pack_sha[]="'+sha(out/'pack.bin')+'";\ninline constexpr const char image_sha[]="'+need+'";\ninline constexpr const char provider32_sha[]="'+identities['C:\\Windows\\SysWOW64\\user32.dll']+'";\ninline constexpr const char provider64_sha[]="'+identities['C:\\Windows\\System32\\user32.dll']+'";\n}\n'
    (out/'spec.hpp').write_text(header);print(json.dumps(dict(passed_static=True,report_sha256=sha(out/'report.json'),pack_sha256=sha(out/'pack.bin'))))
if __name__=='__main__':main(sys.argv[1])
