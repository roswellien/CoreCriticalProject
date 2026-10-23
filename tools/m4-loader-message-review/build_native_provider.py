"""Compile/link only; inspect native resources/imports/exports without loading."""
from pathlib import Path
import hashlib,json,shutil,struct,subprocess,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-loader-message-review/native-build-r1';assert not out.exists();out.mkdir();prep=R/'reports/m4-loader-message-review/native-preparation-r1/report.json';assert sha(prep)=='de099653af14f330b58d4e4a9753b9e4ab4712f4c18fbd147a7393a396406f16';d=json.loads(prep.read_bytes());pins=dict(d['files']);pins[str(prep)]=sha(prep);runs=[];passed=False
 def pin(p):p=Path(p).resolve();pins[str(p)]=sha(p);return p
 cl=pin(shutil.which('cl.exe'));link=pin(shutil.which('link.exe'));llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';cvtres=pin(llvm/'llvm-cvtres.exe');readobj=pin(llvm/'llvm-readobj.exe')
 def run(cmd,prefix):
  result=subprocess.run([str(x)for x in cmd],capture_output=True);p=Path(prefix);p.with_suffix('.stdout').write_bytes(result.stdout);p.with_suffix('.stderr').write_bytes(result.stderr);pin(p.with_suffix('.stdout'));pin(p.with_suffix('.stderr'));runs.append(dict(command=[str(x)for x in cmd],exit_code=result.returncode));assert result.returncode==0,result.stderr.decode(errors='replace')
 try:
  res=out/'messages.obj';run([cvtres,'/machine:x64','/out:'+str(res),prep.parent/'messages.res'],out/'resource-convert');pin(res)
  for level,option in [('O0','/Od'),('O2','/O2')]:
   dst=out/level;dst.mkdir();obj=dst/'message.obj';dll=dst/'Mech3Msg.dll'
   run([cl,'/nologo','/c','/MD','/EHsc','/std:c++17',option,'/Fo'+str(obj),'/I'+str(prep.parent),prep.parent/'native_provider.cpp'],dst/'compile');pin(obj)
   run([link,'/nologo','/DLL','/MACHINE:X64','/OUT:'+str(dll),'/IMPLIB:'+str(dst/'Mech3Msg.lib'),obj,res],dst/'link');pin(dll)
   run([readobj,'--file-headers','--coff-imports','--coff-exports',dll],dst/'inspection')
   # Whole native PE32+ resource leaf independently inspected from raw bytes.
   data=dll.read_bytes();pe=struct.unpack_from('<I',data,0x3c)[0];coff=pe+4;machine,count=struct.unpack_from('<HH',data,coff);optional=coff+20;size=struct.unpack_from('<H',data,coff+16)[0];assert machine==0x8664 and struct.unpack_from('<H',data,optional)[0]==0x20b;section_table=optional+size;sections=[]
   for i in range(count):
    at=section_table+i*40;name=data[at:at+8].rstrip(b'\0').decode();vs,rva,rawsize,raw=struct.unpack_from('<IIII',data,at+8);sections.append(dict(name=name,rva=rva,virtual_bytes=vs,raw_bytes=rawsize,raw=raw))
   def offset(rva,n):
    section=next(s for s in sections if s['rva']<=rva and rva+n<=s['rva']+s['raw_bytes']);return section['raw']+rva-section['rva']
   rr,rn=struct.unpack_from('<II',data,optional+112+2*8);rb=offset(rr,rn);leaves=[]
   def resource(pos,chain):
    named,ids=struct.unpack_from('<HH',data,rb+pos+12);assert named==0
    for i in range(ids):
     key,child=struct.unpack_from('<II',data,rb+pos+16+i*8)
     if child&0x80000000:resource(child&0x7fffffff,chain+[key])
     else:
      va,n,codepage,reserved=struct.unpack_from('<IIII',data,rb+child);payload=data[offset(va,n):offset(va,n)+n];leaves.append(dict(path=chain+[key],bytes=n,sha256=hashlib.sha256(payload).hexdigest(),codepage=codepage,reserved=reserved))
   resource(0,[]);assert len(leaves)==1 and leaves[0]['path']==[11,1,1033]and leaves[0]['bytes']==68528 and leaves[0]['sha256']=='8f09455e1f69228625d19f538c6779023a862e836477acfe70a8b2dcc508cf7e'
   p=dst/'physical-resource.json';p.write_text(json.dumps(dict(machine=machine,magic=0x20b,sections=sections,resources=leaves,actual_resource_payload_whole_bytes_equal=True,DLL_loaded=False),indent=2)+'\n');pin(p)
  for p in [Path(__file__),Path(__file__).with_suffix('.ps1'),Path(sys.executable)]:pin(p)
  for path,h in pins.items():assert sha(path)==h
  passed=True
 finally:
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Both O0/O2 native x64 executable DLL compile/link and independent whole original resource leaf physical hash only; no module loaded',preparation_sha256=sha(prep),runs=runs,no_DLL_execution=True,native_game_launch=False,source_algorithm_equivalence=False,original_MSVCRT_parity=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q))))
if __name__=='__main__':main()
