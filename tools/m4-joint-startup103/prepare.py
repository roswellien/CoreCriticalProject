"""Add connected103 without changing accepted71 sources or literal objects."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main(nativeprep,digest,source_lifts,contracts,out):
 nativeprep=Path(nativeprep).resolve();source_lifts=Path(source_lifts).resolve();contracts=Path(contracts).resolve();out=Path(out).resolve()
 assert out.parent==ROOT/'reports/m4-joint-startup103'and not out.exists();out.mkdir(parents=True)
 pins={};generated={}
 def bind(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return v
 def write(p,s):
  p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8');generated[str(p)]=sha(p)
 parent=ROOT/'reports/m4-joint-startup71/preparation-r2';bind(parent/'report.json','bc4a257580f63973805b1b2c687725e1319c641d8c151e8feca9802b34028584');prior=json.loads((parent/'report.json').read_bytes())
 accepted=ROOT/'reports/m4-joint-startup71-root/acceptance-r1/report.json';bind(accepted,'64c010e01930d4f84d7df9cb8cd932669ce25b6f3f1dc21989f197282025fdfc')
 for p,h in json.loads((parent/'pins.json').read_bytes())['files'].items():bind(p,h)
 bind(nativeprep/'report.json',digest);native=json.loads((nativeprep/'report.json').read_bytes());assert native['passed']
 nativepins=json.loads((nativeprep/'pins.json').read_bytes())['files']if(nativeprep/'pins.json').exists()else native['files']
 for p,h in nativepins.items():bind(p,h)
 bind(source_lifts);lift=json.loads(source_lifts.read_bytes());assert lift['passed']
 for p,h in lift['files'].items():bind(p,h)
 bind(contracts);contract=json.loads(contracts.read_bytes());selected=contract['selected_order'];assert len(selected)==103 and len(contract['roots'])==32
 loader=ROOT/'reports/m4-mfc-source/loader-identity-r1/report.json';bind(loader,'7925f659144954487b1b13d781d4aee48aa0b8d20887ce9ee8aa40ce7a12b09b');assert json.loads(loader.read_bytes())['passed']
 game=ROOT/'MW3/Mech3.exe';bind(game,'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=PEImage(game.read_bytes())
 mfc=ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL';bind(mfc,'5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8')
 for p in parent.rglob('*'):
  if p.is_file()and p.suffix in('.cpp','.hpp','.inc'):write(out/p.relative_to(parent),p.read_text().replace(parent.as_posix(),out.as_posix()))
 protocol=(out/'joint_protocol.hpp').read_text();start=protocol.index('constexpr std::array<std::uint32_t,71> entries');end=protocol.index(';',start)
 write(out/'joint_protocol.hpp',protocol[:start]+'constexpr std::array<std::uint32_t,103> entries{'+','.join(hex(x['entry'])for x in selected)+'}'+protocol[end:])
 fixed=[0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000]
 pages=sorted((set(prior['extra_pages'])|set(contract['source_data_pages'])|{0x5f498000})-set(fixed));roots=prior['registration_roots']+[r['entry']for r in contract['roots']];assert len(set(roots))==75
 write(out/'registration_contract.hpp','#pragma once\nnamespace mw34::m4_mixed {\nconstexpr std::array<unsigned,'+str(len(pages))+'> registration_pages{'+','.join(hex(x)for x in pages)+'};\nconstexpr std::array<unsigned,75> registration_roots{'+','.join(hex(x)for x in roots)+'};\n}\n')
 write(out/'onexit_session.hpp',(nativeprep/'session.hpp').read_text())
 s=(out/'native_main.cpp').read_text();s=one(s,'phase==71&&r_.calls().size()==74&&r_.translation_count()==72','phase==103&&r_.calls().size()==106&&r_.translation_count()==104')
 s=one(s,'std::span<const std::byte>crt,unsigned repeat','std::span<const std::byte>crt,std::span<const std::byte>mfc,unsigned repeat')
 s=one(s,'std::make_unique<m4_onexit::Session>(r_,crt)','std::make_unique<m4_onexit::Session>(r_,crt,mfc)')
 s=one(s,'need(argc==5,"Joint71 exact game/numeric/CRT fresh-directory")','need(argc==6,"Joint103 exact game/numeric/CRT/MFC fresh-directory")')
 s=one(s,'crt=old::read(argv[3],266293);','crt=old::read(argv[3],266293),mfc=old::read(argv[4],954128);')
 s=one(s,'capture_direct::Writer writer(argv[4],options);','need(old::sha256(mfc)=="5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8","Exact MFC provider identity");capture_direct::Writer writer(argv[5],options);')
 s=one(s,'std::as_bytes(std::span{crt}),repeat,cw,top)','std::as_bytes(std::span{crt}),std::as_bytes(std::span{mfc}),repeat,cw,top)')
 s=one(s,'const unsigned header[]{1,6,71,426,17,sizeof(Native)}','const unsigned header[]{1,6,103,618,17,sizeof(Native)}')
 for a,b in [('selected71','selected103'),('Connected71','Connected103'),('connected71','connected103'),('persistent71','persistent103'),('Joint71','Joint103'),('Joint27','Joint103'),('selected27','selected103'),('records.reserve(71)','records.reserve(103)'),('records.size()==71','records.size()==103'),('total==426','total==618'),('426native','618native')]:s=s.replace(a,b)
 write(out/'native_main.cpp',s)
 objects={};bindings={}
 for r in contract['roots']:
  entry=r['entry'];b=lift['source_bodies'][f'f_{entry:x}'];size=b['source_bytes'];off,_=pe.rva_range(entry-pe.image_base,size);raw=pe.data[off:off+size]
  bindings[f'f_{entry:x}']=dict(entry=entry,size=size,file_offset=off,original_sha256=hashlib.sha256(raw).hexdigest(),literal_lift_input_sha256=b['source_sha256'],decoded_bytes=b['unique_decoded_bytes'])
 for level in('O0','O2'):
  added=[p for p in native['entry_objects']if Path(p).stem.endswith('-'+level)];objects[level]=list(dict.fromkeys(prior['objects'][level]+added))
  for p in objects[level]:bind(p)
  old=(out/level/'registration_bindings.inc').read_text();lines=[]
  for r in contract['roots']:
   entry=r['entry'];a=bindings[f'f_{entry:x}'];obj=lift['source_bodies'][f'f_{entry:x}']['objects'][level]
   lines.append('r_.register_translation({{'+hex(entry)+'},{m4_runtime::Abi::Cdecl,0,true},&registration_entry,"Selected literal MFC allocation root",{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,'+str(a['size'])+',"'+a['original_sha256']+'","'+obj['sha256']+'","'+sha(source_lifts)+'"}});')
  write(out/level/'registration_bindings.inc',old+'\n'+'\n'.join(lines)+'\n')
 write(out/'runtime-entry-bindings.json',json.dumps(bindings,indent=2)+'\n')
 for name in('CMakeLists.txt','build.py','build.ps1','run.py'):
  p=HERE/name;bind(p);write(out/name,p.read_text())
 bind(__file__)
 report=dict(passed=True,scope='Connected103 preparation only; no execution credit',objects=objects,native_library=str(nativeprep/'registry_library.cpp'),native_include=str(nativeprep),generated_sources=generated,physical_dependencies=pins,parent_acceptance=str(accepted),parent_acceptance_sha256=sha(accepted),source_lifts=str(source_lifts),source_lifts_sha256=sha(source_lifts),contracts=str(contracts),contracts_sha256=sha(contracts),selected_order=selected,registration_roots=roots,extra_pages=pages,connected_root_credit=False,native_executed=False)
 write(out/'report.json',json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files=pins|generated),indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(out/'report.json'),sha256=sha(out/'report.json'))),flush=True)
if __name__=='__main__':main(*sys.argv[1:])
