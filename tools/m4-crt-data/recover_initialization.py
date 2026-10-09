"""Read-only exact-byte direct reference inventory for required CRT data imports."""
import argparse,hashlib,json,pathlib,re,struct,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-crt'))
from recover_provider import PE,PROVIDER_SHA,IMAGE_SHA
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,w):
 if not v:raise ValueError(w)
def bind(p):p=pathlib.Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def main(out):
 need(out.is_relative_to(ROOT/'reports/m4-crt-data') and not out.exists(),'Fresh private static data dossier')
 provider=PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',PROVIDER_SHA);game=PE(ROOT/'MW3/Mech3.exe',IMAGE_SHA);tool=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe';out.mkdir(parents=True)
 command=[str(tool),'-d','--x86-asm-syntax=intel',str(provider.path)];r=subprocess.run(command,capture_output=True);need(r.returncode==0 and not r.stderr,'Exact full provider decoder');log=out/'provider-text-llvm.txt';log.write_bytes(r.stdout);instructions={};symbol=None
 for line in r.stdout.decode().splitlines():
  m=re.match(r'^([0-9a-f]+) <([^>]+)>:$',line)
  if m:symbol={'address':int(m[1],16),'label':m[2]};continue
  m=re.match(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)$',line)
  if not m:continue
  address=int(m[1],16);body=bytes.fromhex(m[2]);need(provider.read(address-provider.base,len(body))==body,'Decoder literal byte equality');need(address not in instructions,'Unique instruction starts');need(any(va<=address-provider.base and address-provider.base+len(body)<=va+min(vs,rs) and flags&0xe0000000==0x60000000 for va,vs,rs,rp,flags in provider.sections),'Only file-backed RX instruction inventory')
  instructions[address]={'address':address,'size':len(body),'mnemonic':m[3],'operands':m[4].strip(),'bytes_hex':body.hex(),'decoder_nearest_symbol':symbol}
 exports=provider.exports();imports=provider.imports();names=['_adjust_fdiv','_acmdln'];globals=[]
 for name in names:
  e=exports[name];need(any(va<=e['rva'] and e['rva']+4<=va+min(vs,rs) and flags&0xe0000000==0xc0000000 for va,vs,rs,rp,flags in provider.sections),'Exact data export file-backed RW')
  slot=[i for i in game.imports() if i.get('name')==name and i['library'].casefold()=='msvcrt.dll'];need(len(slot)==1,'One named original game data IAT owner')
  refs=[v for v in instructions.values() if re.search(r'(?<![0-9a-f])0x'+format(e['address'],'x')+r'(?![0-9a-f])',v['operands'])]
  globals.append({'name':name,**e,'game_import':slot[0],'source_file_offset':provider.offset(e['rva'],4),'source_value':struct.unpack('<I',provider.read(e['rva'],4))[0],'direct_instruction_references':refs,'initialized_value_measured':False})
 services=[]
 for name in ('GetCommandLineA','GetCommandLineW','GetEnvironmentStringsW','GetVersion','GetVersionExA','HeapCreate','GetModuleFileNameA'):
  slots=[i for i in imports if i.get('name')==name]
  for slot in slots:
   refs=[v for v in instructions.values() if re.search(r'(?<![0-9a-f])0x'+format(slot['iat'],'x')+r'(?![0-9a-f])',v['operands'])];services.append({**slot,'direct_instruction_references':refs})
 entry=provider.base+provider.u32(provider.opt+16);entryrow=instructions.get(entry);need(entryrow is not None,'Provider entry at observed RX instruction')
 report={'passed':True,'scope':'Exact-byte static direct data/import reference inventory; no provider loading/execution or initialized-data admission','source':bind(__file__),'PE_parser':bind(ROOT/'tools/m4-crt/recover_provider.py'),'provider':bind(provider.path),'game':bind(game.path),'decoder':bind(tool),'decoded_RX_instructions':len(instructions),'all_decoded_instruction_bytes_match_exact_provider':True,'provider_entry':entry,'provider_entry_instruction':entryrow,'required_data_globals':globals,'relevant_OS_import_sites':services,'command':command,'exit_code':r.returncode,'decoder_log':bind(log),'limitations':['Direct absolute references only; this is not an exhaustive alias/indirect writer proof','Nearest decoder symbol is an output label, not a recovered function boundary','Provider PE file values do not authorize initialized provider state','No actual GetCommandLine/argv/environment or heap service implementation','Actual required initialization branches and service effects still need recovery and measured gates','No original IAT rewrite, host pointer cast, provider DLL load/DllMain, native startup or menu credit'],'whole_M4_complete':False}
 rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');paths=[rp,log,pathlib.Path(__file__),ROOT/'tools/m4-crt/recover_provider.py',provider.path,game.path,tool,pathlib.Path(sys.executable)];(out/'pins.json').write_text(json.dumps({'files':{str(p.resolve()):sha(p) for p in paths}},indent=2)+'\n');print('Read-only data initialization inventory;',len(instructions),'actual decoded RX instructions')
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('output',type=pathlib.Path);v=a.parse_args();main(v.output.resolve())
