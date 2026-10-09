"""Read-only exact-source recovery of next required CRT startup contracts."""
from pathlib import Path
import argparse,hashlib,json,re,struct,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-crt'))
from recover_provider import PE,PROVIDER_SHA,IMAGE_SHA,bind
RANGES=((0x780042e1,0x78004410),(0x7801129b,0x78011318),(0x7800b38f,0x7800b3a0),(0x7800ba5e,0x7800baa0),(0x7800bbbc,0x7800bdfc))
def need(ok,why):
 if not ok:raise ValueError(why)
def decode_lines(raw,provider,begin,end):
 result={}
 for line in raw.decode('utf-8').splitlines():
  m=re.match(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)$',line)
  if not m:continue
  address=int(m[1],16);b=bytes.fromhex(m[2]);need(begin<=address<end and address+len(b)<=end,'Exact requested instruction range');need(provider.read(address-provider.base,len(b))==b,'Actual decoder/source byte equality');need(address not in result,'Unique instruction starts');result[address]={'address':address,'size':len(b),'mnemonic':m[3],'operands':m[4].strip(),'bytes':b.hex()}
 return result
def graph(instructions,entry):
 pending=[entry];seen=set();edges=[];imports=[];returns=[]
 while pending:
  address=pending.pop()
  if address in seen:continue
  need(address in instructions,'CFG edge lacks an exact admitted instruction '+hex(address));seen.add(address);i=instructions[address];m=i['mnemonic'];raw=bytes.fromhex(i['bytes']);fall=address+i['size']
  if m in ('ret','retl'):returns.append(address);continue
  if m=='call' or m=='jmp' or m.startswith('j'):
   relative=None
   if raw[0] in (0xe8,0xe9):need(len(raw)==5,'Exact near rel32');relative=fall+struct.unpack_from('<i',raw,1)[0]
   elif raw[0]==0xeb or 0x70<=raw[0]<=0x7f:need(len(raw)==2,'Exact short relative');relative=fall+struct.unpack_from('<b',raw,1)[0]
   elif raw[:1]==b'\x0f' and 0x80<=raw[1]<=0x8f:need(len(raw)==6,'Exact conditional rel32');relative=fall+struct.unpack_from('<i',raw,2)[0]
   if relative is None:
    if raw[:2]==b'\xff\x15' and len(raw)==6:imports.append({'site':address,'iat':struct.unpack_from('<I',raw,2)[0]})
    else:raise ValueError('Unresolved indirect route '+hex(address))
   else:edges.append({'from':address,'to':relative,'kind':'call' if m=='call' else 'branch'});pending.append(relative)
   if m!='jmp':edges.append({'from':address,'to':fall,'kind':'fallthrough'});pending.append(fall)
  else:edges.append({'from':address,'to':fall,'kind':'fallthrough'});pending.append(fall)
 need(returns,'Complete root requires reachable actual return');return {'entry':entry,'instruction_count':len(seen),'instructions':[instructions[x] for x in sorted(seen)],'edges':edges,'returns':returns,'provider_imports':imports,'complete_import_free':not imports}
def controls(instructions):
 cases=[]
 def deny(name,fn):
  try:fn()
  except (ValueError,struct.error) as e:cases.append({'name':name,'rejected':True,'diagnostic':str(e)});return
  raise ValueError('Static CFG observer accepted '+name)
 removed=dict(instructions);removed.pop(0x7801129b);deny('missing-hot-cold-tail',lambda:graph(removed,0x780042e1))
 removed=dict(instructions);removed.pop(0x7800432c);deny('missing-CW-to-CRT-helper',lambda:graph(removed,0x780042e1))
 removed=dict(instructions);removed.pop(0x7800439f);deny('missing-CRT-to-CW-helper',lambda:graph(removed,0x780042e1))
 removed=dict(instructions);removed.pop(0x780042f7);deny('missing-control87',lambda:graph(removed,0x780042e1))
 changed=dict(instructions);changed[0x780042ef]={**changed[0x780042ef],'bytes':'e805000000'};deny('CALL-to-middle-of-instruction',lambda:graph(changed,0x780042e1))
 changed=dict(instructions);changed[0x780042ef]={**changed[0x780042ef],'bytes':'ffd0'};deny('unreviewed-indirect-CALL',lambda:graph(changed,0x780042e1))
 return cases
def main():
 a=argparse.ArgumentParser();a.add_argument('--out',required=True);out=Path(a.parse_args().out).resolve();need(out.is_relative_to(ROOT/'reports/m4-crt-next') and not out.exists(),'Fresh CRT-next private dossier');provider=PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',PROVIDER_SHA);game=PE(ROOT/'MW3/Mech3.exe',IMAGE_SHA);exports=provider.exports();imports=provider.imports();out.mkdir(parents=True);tool=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe';instructions={};ranges=[];commands=[]
 for start,end in RANGES:
  section=[s for s in provider.sections if s[0]<=start-provider.base and end-provider.base<=s[0]+min(s[1],s[2])];need(len(section)==1 and section[0][4]&0xe0000000==0x60000000,'Exact raw RX range')
  code=provider.read(start-provider.base,end-start);binary=out/(hex(start)+'-source.bin');binary.write_bytes(code);command=[str(tool),'-d','--x86-asm-syntax=intel','--start-address='+hex(start),'--stop-address='+hex(end),str(provider.path)];r=subprocess.run(command,capture_output=True);need(r.returncode==0,'Exact LLVM decoding');log=out/(hex(start)+'-llvm.txt');log.write_bytes(r.stdout+r.stderr);commands.append({'command':command,'exit_code':r.returncode,'log':bind(log)});decoded=decode_lines(r.stdout,provider,start,end);instructions.update(decoded);ranges.append({'begin':start,'end_exclusive':end,'source':bind(binary),'raw_offset':provider.offset(start-provider.base,end-start),'instruction_count':len(decoded)})
 roots=[graph(instructions,x) for x in (0x780042e1,0x780042f7,0x7800432c,0x7800439f,0x7800b38f)]
 # __getmainargs requires parser+allocator+OS work; its closure deliberately
 # stops at unresolved dependencies rather than inventing a success contract.
 observed_getmainargs=[i for i in instructions.values() if 0x7800ba5e<=i['address']<0x7800baa0];data=[]
 for name,size in (('_adjust_fdiv',4),('_acmdln',4)):
  e=exports[name];raw=provider.read(e['rva'],size);s=[s for s in provider.sections if s[0]<=e['rva'] and e['rva']+size<=s[0]+min(s[1],s[2])];need(len(s)==1 and s[0][4]&0xe0000000==0xc0000000,'Exact data import raw RW provenance');game_import=[i for i in game.imports() if i.get('name')==name and i['library'].lower()=='msvcrt.dll'];need(len(game_import)==1,'Exact game data IAT');data.append({'name':name,**e,'size':size,'raw_offset':provider.offset(e['rva'],size),'original_bytes_hex':raw.hex(),'original_value':struct.unpack('<I',raw)[0],'game_import':game_import[0],'initialized_host_provider_value_unobserved':True,'native_data_import_route_admitted':False})
 report={'passed':True,'scope':'Static next-CRT closure/provenance only; no original/native body execution, service or data-import admission','provider':bind(provider.path),'image':bind(game.path),'decoder':bind(tool),'source':bind(__file__),'PE_parser':bind(ROOT/'tools/m4-crt/recover_provider.py'),'source_ranges':ranges,'commands':commands,'complete_roots':roots,'authored_failure_controls':controls(instructions),'data_imports':data,'provider_imports':imports,'setusermatherr':{'entry':0x7800b38f,'end_exclusive':0x7800b3a0,'cdecl_argument_bytes':4,'callee_pop_bytes':0,'zeroed_global':0x780392b8,'callback_pointer_global':0x7803b0c4,'flags_defined_mask':0x8c5,'defined_flags_result':0x44,'AF':'AND makes AF undefined; do not infer it from a convenient host result','callback_invoked':False},'getmainargs_partial':{'body_entry':0x7800ba5e,'body_end_exclusive':0x7800baa0,'instructions':observed_getmainargs,'direct_required_dependencies':[0x7800b3b4,0x7800bbbc],'normal_no_wildcard_parser':0x7800bc48,'normal_parser_required_services':['KERNEL32 GetModuleFileNameA at provider IAT7802E018','malloc at780012B3','_amsg_exit allocation failure at7800BADB','multibyte classification table780379E1'],'complete_closure':False,'native_admitted':False},'CW_bridge_defects':{'pinned_semantics':bind(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/lib/Arch/X86/Semantics/X87.cpp'),'FNSTCW':'Mutates guest PC to single and sources RC from host __remill_fpu_get_rounding','FLDCW':'Loads guest CW then forces PC to single; updates host rounding','required_native_contract':'Dedicated typed guest memory read/write16 CW bridges preserving measured PC/RC/masks and all non-CW state; no host environment used as guest state authority','hardware_reserved_bit_normalization':'Needs actual original FLDCW→FNSTCW/FXSAVE observations before a normalized guest CW policy can be admitted'},'whole_M4_complete':False,'limits':['Exact staged provider chosen explicitly; actual game host-loaded provider remains unobserved','Controlfp CFG complete/import-free, execution and equivalence pending','Getmainargs wildcard and normal parser complete dependency closure absent','No data IAT rewrite or successful CRT substitutes','Guest SEH, CRT initialization, argv/environment ownership and menu work remain open']}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');paths=[x for x in out.iterdir() if x.is_file()]+[provider.path,game.path,tool,Path(__file__),ROOT/'tools/m4-crt/recover_provider.py',ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/lib/Arch/X86/Semantics/X87.cpp'];(out/'pins.json').write_text(json.dumps({'files':{str(x.resolve()):bind(x)['sha256'] for x in paths}},indent=2)+'\n');print('Static next CRT dossier prepared; no execution/admission credit')
if __name__=='__main__':main()
