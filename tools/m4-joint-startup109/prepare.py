"""Add six normal FS roots to the immutable accepted103 source corpus."""
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
 nativeprep=Path(nativeprep).resolve();out=Path(out).resolve()
 assert out.parent==ROOT/'reports/m4-joint-startup109'and not out.exists();out.mkdir(parents=True)
 pins={};generated={}
 def bind(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return v
 def write(p,s):
  p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8');generated[str(p)]=sha(p)
 parent=ROOT/'reports/m4-joint-startup103/preparation-r1';bind(parent/'report.json','b8d18bc4765dee58c6a4e62082f2d74497833be1c8df0eee76532807c841bde6');prior=json.loads((parent/'report.json').read_bytes())
 accepted=ROOT/'reports/m4-joint-startup103-root/acceptance-r1/report.json';bind(accepted,'13cc2567f30f2dae2d12991a3a76aa6c953c70a49148dc4ed13df34837b14c7c');assert json.loads(accepted.read_bytes())['passed']
 for p,h in json.loads((parent/'pins.json').read_bytes())['files'].items():bind(p,h)
 bind(nativeprep/'report.json',digest);native=json.loads((nativeprep/'report.json').read_bytes());assert native['passed']
 for p,h in (json.loads((nativeprep/'pins.json').read_bytes())['files']if(nativeprep/'pins.json').exists()else native['files']).items():bind(p,h)
 source_lifts=ROOT/'reports/m4-fs-source/lifts-r1/report.json';bind(source_lifts,'f5af3ee18fd942c5f58226b0ae98fca29d7bdc93877d7cfdd624a43cc0aa1ab8');lift=json.loads(source_lifts.read_bytes());assert lift['passed']
 for p,h in lift['files'].items():bind(p,h)
 contracts=ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json';bind(contracts);contract=json.loads(contracts.read_bytes());selected=contract['selected_order'];assert len(selected)==109 and len(contract['roots'])==6
 review=ROOT/'reports/m4-fs-review/static-r1/report.json';bind(review);assert json.loads(review.read_bytes())['passed']
 game=ROOT/'MW3/Mech3.exe';bind(game,'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=PEImage(game.read_bytes())
 for p in parent.rglob('*'):
  if p.is_file()and p.suffix in('.cpp','.hpp','.inc'):write(out/p.relative_to(parent),p.read_text().replace(parent.as_posix(),out.as_posix()))
 protocol=(out/'joint_protocol.hpp').read_text();start=protocol.index('constexpr std::array<std::uint32_t,103> entries');end=protocol.index(';',start)
 write(out/'joint_protocol.hpp',protocol[:start]+'constexpr std::array<std::uint32_t,109> entries{'+','.join(hex(x['entry'])for x in selected)+'}'+protocol[end:])
 fixed=[0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000]
 pages=sorted((set(prior['extra_pages'])|set(contract['source_data_pages']))-set(fixed));assert len(pages)==18
 roots=prior['registration_roots']+[r['entry']for r in contract['roots']];assert len(set(roots))==81
 write(out/'registration_contract.hpp','#pragma once\nnamespace mw34::m4_mixed {\nconstexpr std::array<unsigned,18> registration_pages{'+','.join(hex(x)for x in pages)+'};\nconstexpr std::array<unsigned,81> registration_roots{'+','.join(hex(x)for x in roots)+'};\n}\n')
 write(out/'onexit_session.hpp',(nativeprep/'session.hpp').read_text())
 s=(out/'native_main.cpp').read_text();s=one(s,'phase==103&&r_.calls().size()==106&&r_.translation_count()==104','phase==109&&r_.calls().size()==112&&r_.translation_count()==110')
 for a,b in [('selected103','selected109'),('Connected103','Connected109'),('connected103','connected109'),('persistent103','persistent109'),('Joint103','Joint109'),('records.reserve(103)','records.reserve(109)'),('records.size()==103','records.size()==109'),('total==618','total==654'),('1,6,103,618,17,sizeof(Native)','1,6,109,654,17,sizeof(Native)'),('103-root','109-root')]:s=s.replace(a,b)
 write(out/'native_main.cpp',s)
 objects={};bindings={};retained={}
 for r in contract['roots']:
  entry=r['entry'];b=lift['source_bodies'][f'f_{entry:x}'];size=b['source_bytes'];off,_=pe.rva_range(entry-pe.image_base,size);raw=pe.data[off:off+size]
  bindings[f'f_{entry:x}']=dict(entry=entry,size=size,file_offset=off,original_sha256=hashlib.sha256(raw).hexdigest(),literal_lift_input_sha256=b['source_sha256'],decoded_bytes=b['unique_decoded_bytes'])
 for level in('O0','O2'):
  retained[level]=[p for p in prior['objects'][level]if Path(p).suffix=='.lib'];assert len(retained[level])==1
  old_objects=[p for p in prior['objects'][level]if Path(p).suffix=='.obj'];assert len(old_objects)==295
  added=[p for p in native['entry_objects']if Path(p).stem.endswith('-'+level)]
  bystem={Path(p).stem:p for p in old_objects}
  for p in added:
   stem=Path(p).stem
   if stem in bystem:assert sha(bystem[stem])==sha(p),('Changed prior literal body requires explicit reviewed replacement',p)
   else:bystem[stem]=p
  objects[level]=list(bystem.values());assert len(objects[level])==312
  for p in objects[level]:bind(p)
  old=(out/level/'registration_bindings.inc').read_text();lines=[]
  for r in contract['roots']:
   entry=r['entry'];a=bindings[f'f_{entry:x}'];obj=lift['source_bodies'][f'f_{entry:x}']['objects'][level]
   lines.append('r_.register_translation({{'+hex(entry)+'},{m4_runtime::Abi::Cdecl,0,true},&registration_entry,"Selected literal normal FS constructor root",{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,'+str(a['size'])+',"'+a['original_sha256']+'","'+obj['sha256']+'","'+sha(source_lifts)+'"}});')
  write(out/level/'registration_bindings.inc',old+'\n'+'\n'.join(lines)+'\n')
 write(out/'runtime-entry-bindings.json',json.dumps(bindings,indent=2)+'\n')
 for name in('CMakeLists.txt','build.py','build.ps1','run.py'):
  p=HERE/name;bind(p);write(out/name,p.read_text())
 bind(__file__)
 report=dict(passed=True,scope='Connected109 preparation only; no execution credit',objects=objects,linked_literal_COFFs_per_level=312,retained_unlinked_archives=retained,native_library=str(nativeprep/'registry_library.cpp'),native_include=str(nativeprep),generated_sources=generated,physical_dependencies=pins,parent_acceptance=str(accepted),parent_acceptance_sha256=sha(accepted),source_lifts=str(source_lifts),source_lifts_sha256=sha(source_lifts),contracts=str(contracts),contracts_sha256=sha(contracts),selected_order=selected,registration_roots=roots,extra_pages=pages,connected_root_credit=False,native_executed=False,canonical_capture_transport=True)
 write(out/'report.json',json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files=pins|generated),indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(out/'report.json'),sha256=sha(out/'report.json'),linked_COFFs=312)))
if __name__=='__main__':main(*sys.argv[1:])
