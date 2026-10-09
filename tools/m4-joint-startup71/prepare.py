"""Additive connected71 worker preparation; accepted54 remains immutable."""
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
def main(nativeprep,digest,out):
 nativeprep=Path(nativeprep).resolve();out=Path(out).resolve();assert out.parent==ROOT/'reports/m4-joint-startup71' and not out.exists();out.mkdir(parents=True)
 pins={};generated={}
 def bind(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);pins[str(p)]=v;return v
 def write(p,s):
  p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8');generated[str(p)]=sha(p)
 parent=ROOT/'reports/m4-joint-startup54/preparation-r8';bind(parent/'report.json','505933b586f357986f715ff6f3a195bbbce04a62fdecbba7ff273915740f9ddc');prior=json.loads((parent/'report.json').read_text())
 accepted=ROOT/'reports/m4-joint-startup54-root/acceptance-r1/report.json';bind(accepted,'5a7feb121fd1a8fc95d4e31da18af67099e91012b3f70e36e17575973b4cd89c')
 for p,h in json.loads((parent/'pins.json').read_text())['files'].items():bind(p,h)
 bind(nativeprep/'report.json',digest);native=json.loads((nativeprep/'report.json').read_text());assert native['passed']
 nativepins=json.loads((nativeprep/'pins.json').read_text())['files']if (nativeprep/'pins.json').exists()else native['files']
 for p,h in nativepins.items():bind(p,h)
 source=ROOT/'reports/m4-strings-source/lifts-r1/report.json';bind(source,'903f755f6f21cf67f873925fb1bfbe4748e543af6b5fdc9de325a925fac17a3a');lift=json.loads(source.read_text())
 for p,h in lift['files'].items():bind(p,h)
 correction=ROOT/'reports/m4-strings-source/recovery-r7/report.json';bind(correction,'972ec961d7617d2e7b789d23ab1ce82da0c33424b37c12e2dc94c23d1e154341')
 interface=ROOT/'reports/m4-strings-source/recovery-r7/instruction-contracts.json';bind(interface,'e1a4a4e2a6f1d55b5a1a94b10254202e88304e67dfbedd77326e72f0986e97a9');contract=json.loads(interface.read_text());selected=contract['selected_order'];assert len(selected)==71
 oldnativeprep=ROOT/'reports/m4-onexit-native/preparation-r11';oldnative=json.loads((oldnativeprep/'report.json').read_text())
 game=ROOT/'MW3/Mech3.exe';bind(game,'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=PEImage(game.read_bytes())
 for p in parent.rglob('*'):
  if p.is_file()and p.suffix in('.cpp','.hpp','.inc'):
   s=p.read_text().replace(parent.as_posix(),out.as_posix());write(out/p.relative_to(parent),s)
 protocol=(out/'joint_protocol.hpp').read_text();start=protocol.index('constexpr std::array<std::uint32_t,54> entries');end=protocol.index(';',start)
 protocol=protocol[:start]+'constexpr std::array<std::uint32_t,71> entries{'+','.join(hex(x['entry'])for x in selected)+'}'+protocol[end:];write(out/'joint_protocol.hpp',protocol)
 oldpages=prior['extra_pages'];fixed=[0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000]
 pages=sorted((set(oldpages)|set(contract['source_data_pages']))-set(fixed));roots=prior['registration_roots']+[r['entry']for r in contract['roots']];assert len(set(roots))==43
 write(out/'registration_contract.hpp','#pragma once\nnamespace mw34::m4_mixed {\nconstexpr std::array<unsigned,'+str(len(pages))+'> registration_pages{'+','.join(hex(x)for x in pages)+'};\nconstexpr std::array<unsigned,43> registration_roots{'+','.join(hex(x)for x in roots)+'};\n}\n')
 write(out/'onexit_session.hpp',(nativeprep/'session.hpp').read_text())
 s=(out/'native_main.cpp').read_text();s=one(s,'phase==54&&r_.calls().size()==57&&r_.translation_count()==55','phase==71&&r_.calls().size()==74&&r_.translation_count()==72')
 s=s.replace('selected54','selected71').replace('Connected54','Connected71').replace('connected54','connected71').replace('persistent54','persistent71').replace('Joint54','Joint71')
 s=one(s,'const unsigned header[]{1,6,54,324,17,sizeof(Native)}','const unsigned header[]{1,6,71,426,17,sizeof(Native)}');s=s.replace('records.reserve(54)','records.reserve(71)').replace('records.size()==54','records.size()==71').replace('total==324','total==426').replace('324native','426native')
 s=one(s,'while(context.registry().growth_witnesses().empty())','const auto initial_growth=context.registry().growth_witnesses().size();while(context.registry().growth_witnesses().size()==initial_growth)')
 write(out/'native_main.cpp',s)
 objects={};runtime_bindings={}
 for r in contract['roots']:
  entry=r['entry'];b=lift['source_bodies'][f'f_{entry:x}'];size=b['source_bytes'];off,_=pe.rva_range(entry-pe.image_base,size);raw=pe.data[off:off+size]
  runtime_bindings[f'f_{entry:x}']=dict(entry=entry,size=size,file_offset=off,original_sha256=hashlib.sha256(raw).hexdigest(),literal_lift_input_sha256=b['source_sha256'],decoded_bytes=b['unique_decoded_bytes'])
 for level in('O0','O2'):
  inherited=prior['objects'][level]
  # Frozen native preparation carries the authoritative new closure and source objects.
  added=[p for p in native['entry_objects']if Path(p).stem.endswith('-'+level)]
  objects[level]=list(dict.fromkeys(inherited+added))
  for p in objects[level]:bind(p)
  oldlines=(out/level/'registration_bindings.inc').read_text();lines=[]
  for r in contract['roots']:
   entry=r['entry'];a=runtime_bindings[f'f_{entry:x}'];obj=lift['source_bodies'][f'f_{entry:x}']['objects'][level]
   lines.append('r_.register_translation({{'+hex(entry)+'},{m4_runtime::Abi::Cdecl,0,true},&registration_entry,"Selected literal duplicated-string root",{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,'+str(a['size'])+',"'+a['original_sha256']+'","'+obj['sha256']+'","'+sha(source)+'"}});')
  write(out/level/'registration_bindings.inc',oldlines+'\n'+'\n'.join(lines)+'\n')
  # The original entry/control COFFs remain unchanged. Only the separately
  # compiled Session source and newly lifted game/CRT bodies are additive.
 write(out/'runtime-entry-bindings.json',json.dumps(runtime_bindings,indent=2)+'\n')
 for name in('CMakeLists.txt','build.py','build.ps1','run.py'):
  p=HERE/name;bind(p);write(out/name,p.read_text())
 bind(__file__)
 report=dict(passed=True,scope='Connected71 preparation only; no execution credit',objects=objects,native_library=str(nativeprep/'registry_library.cpp'),native_include=str(nativeprep),generated_sources=generated,physical_dependencies=pins,parent_acceptance=str(accepted),parent_acceptance_sha256=sha(accepted),source_lifts=str(source),source_lifts_sha256=sha(source),selected_order=selected,registration_roots=roots,extra_pages=pages,connected_root_credit=False,native_executed=False)
 write(out/'report.json',json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files=pins|generated),indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(out/'report.json'),sha256=sha(out/'report.json'))))
if __name__=='__main__':main(*sys.argv[1:])
