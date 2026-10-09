"""Recover complete numeric-max game/provider slices; no body execution."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage,read_binary
IMAGE_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
PROVIDER_SHA='91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'
DOSSIER_SHA='d9594fdad37b5f0061653f2a51687bd1fb23106d65c6bc6d10a84103420c2689'
def require(ok,why):
 if not ok:raise ValueError(why)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):
 p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def page(image,base):
 b=bytearray(4096)
 for i in range(4096):
  ss=[s for s in image.sections if image.image_base+s['virtual_address']<=base+i<image.image_base+s['virtual_address']+max(s['virtual_size'],s['raw_size'])]
  require(len(ss)==1,'Owned page mapping ambiguous');s=ss[0];r=base+i-image.image_base-s['virtual_address']
  if r<s['raw_size']:b[i]=image.data[s['raw_offset']+r]
 return bytes(b)
def main():
 out=Path(sys.argv[1]).resolve();require(out.is_relative_to(ROOT/'reports/m4-fp-numeric-max') and not out.exists(),'Entirely fresh private extraction required')
 dossier=ROOT/'reports/m4-service-initializers/static-r1';require(sha(dossier/'final-report.json')==DOSSIER_SHA,'Frozen dossier changed')
 pins=json.loads((dossier/'final-pins.json').read_text())['bindings']
 for item in pins:require(Path(item['path']).stat().st_size==item['size_bytes'] and sha(item['path'])==item['sha256'],'Frozen dossier binding changed: '+item['path'])
 gamepath=ROOT/'MW3/Mech3.exe';providerpath=ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'
 require(sha(gamepath)==IMAGE_SHA and gamepath.stat().st_size==2384384 and sha(providerpath)==PROVIDER_SHA and providerpath.stat().st_size==565760,'Exact images required')
 game=PEImage(read_binary(gamepath));provider=PEImage(read_binary(providerpath));require(game.image_base==0x400000 and provider.image_base==0x780c0000,'Preferred bases differ')
 gd=json.loads((dossier/'three-FP-root-graphs.json').read_text())['0x4c19f0'];pd=json.loads((dossier/'MSVCP50.DLL.provider.json').read_text())
 graphs=[gd['graphs'][str(e)] for e in (0x4c19f0,0x4c1a00)]+[pd['graphs'][str(0x780c10f0)]]
 require([g['instruction_count'] for g in graphs]==[5,16,2] and all(g['local_decode_closed'] and not g['unresolved_controls'] and not g['FS_sites'] for g in graphs),'Complete selected graph differs')
 importsite=graphs[1]['import_sites'];require(len(importsite)==1 and importsite[0]['iat']==0x5bb4fc and importsite[0]['return_pc']==0x4c1a09 and importsite[0]['symbol']['hint']==1544 and importsite[0]['symbol']['name']=='?max@?$numeric_limits@M@std@@SAMXZ','Exact owning import differs')
 export=next(x for x in pd['requested_exports'] if x['requested']==importsite[0]['symbol']['name'])
 require(export['export']['ordinal']==1545 and export['export']['rva']==0x10f0,'Actual export binding differs')
 rows=[r for g in graphs for r in g['instructions']];sparse={a:bytearray(b'\xcc'*4096) for a in (0x4c1000,0x780c1000)};spans=[];slices=[]
 for g in graphs:
  im=provider if g['entry']>0x70000000 else game;origin=1 if im is provider else 0;start=g['entry'];end=max(r['pc']+r['size'] for r in g['instructions'])
  require(all(a['pc']+a['size']==b['pc'] for a,b in zip(g['instructions'],g['instructions'][1:])),'Selected leaf not contiguous')
  offset,_=im.rva_range(start-im.image_base,end-start);code=im.data[offset:offset+end-start]
  for r in g['instructions']:
   off,_=im.rva_range(r['pc']-im.image_base,r['size']);actual=im.data[off:off+r['size']];require(actual==bytes.fromhex(r['bytes']),'Instruction bytes differ')
   b=sparse[r['pc']&~4095];b[r['pc']&4095:(r['pc']&4095)+r['size']]=actual;spans.append((r['pc'],r['size'],off,origin))
  slices.append({'entry':start,'end':end,'image_offset':offset,'origin':origin,'code':code.hex(),'code_sha256':hashlib.sha256(code).hexdigest()})
 # The loader resolves one declared IAT cell; no DLL initialization is run.
 iat=bytearray(page(game,0x5bb000));struct.pack_into('<I',iat,0x4fc,0x780c10f0)
 records=[(a,1,bytes(b)) for a,b in sparse.items()]+[(0x10000000,1,b'\xcc'*4096),(0x5bb000,0,bytes(iat)),(0x78115000,0,page(provider,0x78115000)),(0x60b000,2,page(game,0x60b000)),(0x20001000,2,b'\xa5'*4096)]
 require(records[4][2][4:8]==bytes.fromhex('ffff7f7f'),'Provider data initializer differs')
 pack=b'MW4NMP01'+struct.pack('<I',len(records))+b''.join(struct.pack('<II',a,p)+b for a,p,b in records);out.mkdir(parents=True);(out/'pages.bin').write_bytes(pack)
 header=['#pragma once','#include <array>','#include <cstdint>','namespace mw34::m4_numeric_max {',f'inline constexpr char pack_sha[]="{hashlib.sha256(pack).hexdigest()}";',f'inline constexpr std::size_t pack_size={len(pack)};',
 'inline constexpr std::array<std::uint32_t,7> page_bases{'+','.join(hex(a) for a,p,b in records)+'};','inline constexpr std::array<std::uint32_t,7> page_permissions{'+','.join(str(p) for a,p,b in records)+'};',
 'struct CodeBinding {std::uint32_t pc,size,image_offset,origin;};','inline constexpr std::array<CodeBinding,23> code_bindings{{'+','.join('{'+','.join(hex(v) for v in s)+'}' for s in spans)+'}};','}']
 (out/'spec.hpp').write_text('\n'.join(header)+'\n')
 repairpath=ROOT/'reports/x87-repair/toolchain/repair.json';repair=json.loads(repairpath.read_text());llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
 require(sha(repair['remill_lifter_path'])=='b63f79c2f905163219008c03967a4d48de0ad5fa1a9bdc869968b873831dca38' and sha(repair['repaired_semantics_path'])=='618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca','Pinned lift tool changed')
 commands=[]
 for item in slices:
  name=f"{item['entry']:x}";(out/(name+'.bin')).write_bytes(bytes.fromhex(item['code']))
  for phase,args in [('lift',[repair['remill_lifter_path'],'--arch=x86','--os=windows',f"--address={item['entry']}",'--bytes='+item['code'],'--semantics_dir='+str(Path(repair['repaired_semantics_path']).parent),'--ir_out='+str(out/(name+'.ll'))]),('assemble',[llvm/'llvm-as.exe',out/(name+'.ll'),'-o',out/(name+'.bc')]),('verify',[llvm/'opt.exe','-passes=verify','-disable-output',out/(name+'.bc')])]:
   result=subprocess.run(list(map(str,args)),capture_output=True,timeout=50);(out/(name+'-'+phase+'.stdout')).write_bytes(result.stdout);(out/(name+'-'+phase+'.stderr')).write_bytes(result.stderr);commands.append({'command':list(map(str,args)),'exit':result.returncode});require(result.returncode==0,'Static lift failed')
  item['IR']=bind(out/(name+'.ll'))
 report={'scope':'Complete actual game/provider static recovery only; no execution/equivalence','images':[bind(gamepath),bind(providerpath)],'dossier':[bind(dossier/'final-report.json'),bind(dossier/'final-pins.json')],'graphs':graphs,'instructions':rows,'slices':slices,'IAT':importsite[0],'export':export['export'],'pack':bind(out/'pages.bin'),'spec':bind(out/'spec.hpp'),'commands':commands,'source':bind(__file__),'PE_parser':bind(ROOT/'tools/analysis/pe.py'),'tools':[bind(repairpath),bind(repair['remill_lifter_path']),bind(repair['repaired_semantics_path']),bind(llvm/'llvm-as.exe'),bind(llvm/'opt.exe')],'full_M4_complete':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files=[bind(p) for p in out.rglob('*') if p.is_file()]+pins+report['images']+report['tools']+[report['source'],report['PE_parser']];(out/'pins.json').write_text(json.dumps({'bindings':files},indent=2)+'\n');print(json.dumps({'instructions':23,'entries':3,'pack_bytes':len(pack),'out':str(out)}))
if __name__=='__main__':main()
