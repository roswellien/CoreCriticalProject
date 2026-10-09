"""Exact provider writer and explicit authored capture, static/lift inputs only."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,subprocess,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-commandline-native'
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
GAME_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
WRITER_SHA='6300f3f77dc2f2ce6ea36590028dd7f3b078c721a08d6daac27ebc8c636b5ac3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):p=Path(p).resolve();return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def main(out):
 out=Path(out).resolve();assert out.parent==BASE and not out.exists();out.mkdir(parents=True)
 parser=ROOT/'tools/analysis/pe.py';s=importlib.util.spec_from_file_location('cmd_pe',parser);pe=importlib.util.module_from_spec(s);s.loader.exec_module(pe)
 provider_path=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';game_path=ROOT/'MW3/Mech3.exe';assert sha(provider_path)==PROVIDER_SHA and sha(game_path)==GAME_SHA
 provider=pe.PEImage(provider_path.read_bytes());game=pe.PEImage(game_path.read_bytes());assert provider.image_base==0x78000000
 def get(address,size):o,_=provider.rva_range(address-provider.image_base,size);return provider.data[o:o+size]
 def section(address,size,flags):
  r=address-provider.image_base
  items=[x for x in provider.sections if x['virtual_address']<=r and r+size<=x['virtual_address']+min(x['virtual_size'],x['raw_size']) and x['characteristics']&0xe0000000==flags]
  assert len(items)==1;return items[0]
 def imports(image):return [dict(library=x['library'],**y) for x in image.imports() for y in x['symbols']]
 p_import=[x for x in imports(provider) if x.get('name')=='GetCommandLineA' and x['iat_rva']+provider.image_base==0x7802e034 and x['library'].lower()=='kernel32.dll'];assert len(p_import)==1
 g_import=[x for x in imports(game) if x.get('name')=='_acmdln' and x['iat_rva']+game.image_base==0x5bb518 and x['library'].lower()=='msvcrt.dll'];assert len(g_import)==1
 exports=[x for x in provider.exports() if '_acmdln' in x['names']];assert len(exports)==1 and exports[0]['rva']+provider.image_base==0x78037174
 code=get(0x7800188c,11);assert hashlib.sha256(code).hexdigest()==WRITER_SHA;source_section=section(0x7800188c,11,0x60000000);global_section=section(0x78037174,4,0xc0000000);iat_section=section(0x7802e034,4,0x40000000)
 source=bytearray([0xcc]*4096);source[0x88c:0x897]=code;source[0x897]=0xe9;struct.pack_into('<I',source,0x898,(0x10000100-0x7800189c)&0xffffffff)
 pages=[(0x78001000,5,source),(0x7802e000,1,get(0x7802e000,4096)),(0x78037000,3,get(0x78037000,4096))]
 pack=b'MW4CNPK1'+struct.pack('<I',len(pages))+b''.join(struct.pack('<II',a,f)+v for a,f,v in pages);(out/'pack.bin').write_bytes(pack);(out/'writer-original.bin').write_bytes(code);(out/'writer-authored-capture.bin').write_bytes(source[0x88c:0x89c])
 llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';lifter=ROOT/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe';sem=ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc';assert sha(sem)=='618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca'
 cmds=[]
 def run(argv,name):
  q=subprocess.run(list(map(str,argv)),capture_output=True,timeout=60);p=out/name;p.write_bytes(q.stdout+q.stderr);cmds.append(dict(command=list(map(str,argv)),exit_code=q.returncode,log=bind(p)));assert q.returncode==0;return q.stdout.decode()
 decoded=run([llvm/'llvm-objdump.exe','-d','--x86-asm-syntax=intel','--start-address=0x7800188c','--stop-address=0x78001897',provider_path],'writer-llvm.txt')
 rows=[]
 for line in decoded.splitlines():
  m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
  if m:
   a=int(m[1],16);b=bytes.fromhex(m[2]);assert get(a,len(b))==b;rows.append(dict(pc=a,bytes_hex=b.hex(),mnemonic=m[3],operands=m[4]))
 assert [x['pc'] for x in rows]==[0x7800188c,0x78001892]
 run([lifter,'--arch=x86','--os=windows','--address='+str(0x7800188c),'--bytes='+source[0x88c:0x89c].hex(),'--semantics_dir='+str(sem.parent),'--ir_out='+str(out/'guest.ll')],'lifter.log')
 run([llvm/'llvm-as.exe',out/'guest.ll','-o',out/'guest.bc'],'assemble.log');run([llvm/'opt.exe','-passes=verify','-disable-output',out/'guest.bc'],'verify.log')
 (out/'spec.hpp').write_text('#pragma once\nnamespace mw34::m4_cmd_native {\ninline constexpr char pack_sha[]="'+sha(out/'pack.bin')+'";\ninline constexpr char provider_sha[]="'+PROVIDER_SHA+'";\ninline constexpr char game_sha[]="'+GAME_SHA+'";\n}\n')
 report=dict(passed_static=True,scope='Exact original11bytes plus declared authored capture jump and verified guest IR; no writer/provider execution, no fabricated RET/full attach',entry=0x7800188c,call_return=0x78001892,end_original=0x78001897,authored_capture_pc=0x10000100,writer_original=bind(out/'writer-original.bin'),writer_source_section=source_section,provider_import=p_import[0],provider_IAT_original=struct.unpack('<I',get(0x7802e034,4))[0],provider_IAT_section=iat_section,provider_global=0x78037174,provider_global_file_DWORD=struct.unpack('<I',get(0x78037174,4))[0],global_section=global_section,game_data_import=g_import[0],provider_export=exports[0],instructions=rows,pack=bind(out/'pack.bin'),commands=cmds,inputs=[bind(p) for p in [provider_path,game_path,parser,Path(__file__),lifter,sem,llvm/'llvm-objdump.exe',llvm/'llvm-as.exe',llvm/'opt.exe',ROOT/'docs/m4-crt-commandline-native-contract.md']],native_measurement_plan='Independent actual GetCommandLineA host snapshot; owned GuestAddress; compiled source store; same explicit lpApplicationName-independent commandline fixtures supplied to each process with child-local configuration env; observe alterations rather than overwrite',frozen_dependencies=[bind(ROOT/'reports/m4-runtime/context-r9/build.json'),bind(ROOT/'reports/m4-crt-data/author-review-r1/report.json')])
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed_static=True,report_sha256=sha(out/'report.json'),pack_sha256=sha(out/'pack.bin'))))
if __name__=='__main__':main(sys.argv[1])
