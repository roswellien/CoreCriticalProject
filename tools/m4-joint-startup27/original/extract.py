"""Sparse actual original 27-root sequence, preserving all frozen ancestors.

No hardware execution or expected-value result is generated here. One actual
numeric service IAT relocation is explicit; all code originates in admitted PE
images, and the initial writable image/stack is seeded once per sequence.
"""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'reports/m4-joint-startup27'
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
GAME_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
PROVIDER_SHA='91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'
OBSERVED=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();actual=sha(p);assert h is None or actual==h,(str(p),actual,h);PINS[str(p)]=actual;return p
def mapped_page(image,address):
 result=bytearray(4096)
 for off in range(4096):
  matches=[s for s in image.sections if image.image_base+s['virtual_address']<=address+off<image.image_base+s['virtual_address']+max(s['virtual_size'],s['raw_size'])]
  assert len(matches)==1,'Owned image page mapping must be unambiguous'
  s=matches[0];within=address+off-image.image_base-s['virtual_address']
  if within<s['raw_size']:result[off]=image.data[s['raw_offset']+within]
 return bytes(result)
PINS={}
def main(out):
 out=Path(out).resolve();assert out.parent==BASE and not out.exists();out.mkdir(parents=True)
 old=ROOT/'reports/m4-mixed-startup/original-extract-original-build-r2'
 extraction=json.loads(pin(old/'extraction.json').read_text(encoding='utf-8-sig'))
 oldpack=pin(old/'pages.bin',extraction['pack']['sha256']).read_bytes()
 assert oldpack[:8]==b'MW4MXP01' and struct.unpack_from('<I',oldpack,8)==(22,) and len(oldpack)==12+22*4104
 for b in extraction['inventory_bindings']:pin(b['path'],b['sha256'])
 gamepath=pin(ROOT/'MW3/Mech3.exe',GAME_SHA);providerpath=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',PROVIDER_SHA)
 game=PEImage(gamepath.read_bytes());provider=PEImage(providerpath.read_bytes())
 assert game.image_base==0x400000 and provider.image_base==0x780c0000
 records=[]
 for i in range(22):
  a,p=struct.unpack_from('<2I',oldpack,12+i*4104);records.append((a,p,oldpack[20+i*4104:4116+i*4104]))
 spans=[dict(pc=pc,size=size,image_offset=off,origin=0)for pc,size,off,_ in extraction['code_bindings']]
 sparse=bytearray(b'\xcc'*4096)
 for entry,size,digest in ((0x4c19f0,10,'1147d8ad778df578820c4be4a4719d35cc4a4c39e0d74043bfdbc57909a261cc'),(0x4c1a00,117,'642aa130e093e1dc8e691b492ae650831cb9f60cf2428d2448e6c0a61fe1e3c5')):
  off,_=game.rva_range(entry-game.image_base,size);code=game.data[off:off+size];assert hashlib.sha256(code).hexdigest()==digest
  sparse[entry&4095:(entry&4095)+size]=code;spans.append(dict(pc=entry,size=size,image_offset=off,origin=0))
 records.append((0x4c1000,1,bytes(sparse)))
 # Own the actual complete provider RX/data pages; only its admitted leaf runs.
 provider_code=mapped_page(provider,0x780c1000);assert hashlib.sha256(provider_code[0xf0:0xf7]).hexdigest()=='31d3ed84e61450051bfba7bc7265523bc3e687f3c7e1a1cb237ec08494ec3d1d'
 off,_=provider.rva_range(0x10f0,7);spans.append(dict(pc=0x780c10f0,size=7,image_offset=off,origin=1))
 iat=bytearray(mapped_page(game,0x5bb000));raw_iat=struct.unpack_from('<I',iat,0x4fc)[0];struct.pack_into('<I',iat,0x4fc,0x780c10f0)
 records.extend(((0x5bb000,0,bytes(iat)),(0x780c1000,1,provider_code),(0x78115000,0,mapped_page(provider,0x78115000))))
 assert len(records)==26 and len({a for a,_,_ in records})==26 and set(OBSERVED)<=set(a for a,_,_ in records)
 assert dict((a,b)for a,_,b in records)[0x78115000][4:8]==bytes.fromhex('ffff7f7f')
 entries=set(x['entry']for x in extraction['selected_table_slots'])|{0x4c19f0};order=[]
 for i in range(145):
  slot=0x5e0000+4*i;off,_=game.rva_range(slot-game.image_base,4);entry=struct.unpack_from('<I',game.data,off)[0]
  if entry in entries:order.append((slot,entry))
 assert len(order)==27 and order[18]==(0x5e016c,0x4c19f0) and order[17][1]==0x4b7020 and order[19][1]==0x4c78f0
 pack=b'MW4J27P1'+struct.pack('<I',26)+b''.join(struct.pack('<2I',a,p)+b for a,p,b in records)
 (out/'pages.bin').write_bytes(pack)
 header=['#pragma once','#include <array>','#include <cstdint>','namespace mw34::m4_mixed_original {',f'inline constexpr char pack_sha[]="{hashlib.sha256(pack).hexdigest()}";',f'inline constexpr std::size_t pack_size={len(pack)};',f'inline constexpr unsigned raw_iat={hex(raw_iat)};']
 for name,values in (('entries',[e for s,e in order]),('table_slots',[s for s,e in order]),('page_bases',[a for a,p,b in records]),('page_permissions',[p for a,p,b in records])):
  header.append('inline constexpr std::array<std::uint32_t,'+str(len(values))+'> '+name+'{'+','.join(hex(v)for v in values)+'};')
 header.extend(('struct CodeBinding {std::uint32_t pc,size,image_offset,origin;};','inline constexpr std::array<CodeBinding,'+str(len(spans))+'> code_bindings{{'+','.join('{'+','.join(hex(x[k])for k in ('pc','size','image_offset','origin'))+'}'for x in spans)+'}};','}'))
 (out/'spec.hpp').write_text('\n'.join(header)+'\n')
 report={'passed':True,'scope':'New sparse original27 packing only; no original execution or native acceptance','order':[{'slot':s,'entry':e}for s,e in order],'IAT_relocation':{'cell':0x5bb4fc,'raw_file':raw_iat,'actual_provider_leaf':0x780c10f0,'reason':'One declared loader-equivalent owning service relocation only'},'observed_pages':list(OBSERVED),'pages':[{'address':a,'permissions':p,'sha256':hashlib.sha256(b).hexdigest()}for a,p,b in records],'bindings':spans,'capture_pc':0x410a80,'pack_sha256':sha(out/'pages.bin'),'whole_M4_complete':False}
 (out/'extraction.json').write_text(json.dumps(report,indent=2)+'\n');pin(__file__);pin(ROOT/'tools/analysis/pe.py')
 for p in out.iterdir():
  if p.is_file():pin(p)
 (out/'pins.json').write_text(json.dumps({'files':PINS},indent=2)+'\n')
 print(json.dumps({'passed':True,'pages':26,'roots':27,'observed_pages':14,'pack_sha256':report['pack_sha256']}))
if __name__=='__main__':main(sys.argv[1])
