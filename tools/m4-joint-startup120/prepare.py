"""Join four literal roots to the immutable accepted116 connected corpus."""
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
def main(nativeprep,digest,source_lifts,lift_digest,contracts,contract_digest,preflight_path,preflight_sha,ghidra_path,ghidra_sha,out):
 nativeprep=Path(nativeprep).resolve();source_lifts=Path(source_lifts).resolve();contracts=Path(contracts).resolve();out=Path(out).resolve()
 assert out.parent==ROOT/'reports/m4-joint-startup120'and not out.exists();out.mkdir(parents=True)
 pins={};generated={}
 def bind(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return v
 def write(p,s):
  p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),p;p.write_text(s,encoding='utf-8');generated[str(p)]=sha(p)
 def replace(p,s):
  assert str(p)in generated;p.write_text(s,encoding='utf-8');generated[str(p)]=sha(p)
 parent=ROOT/'reports/m4-joint-startup116/preparation-r1';bind(parent/'report.json','55c616f42ea7ed9458ed50cf999d31ee8f81df5d1df27419a56d4e3bfdd8aa0e');prior=json.loads((parent/'report.json').read_bytes())
 accepted=ROOT/'reports/m4-joint-startup116-root/acceptance-r1/report.json';bind(accepted,'de76b4e006e5ad2ce0b90f634054379f2271abd14ecb8591643c24e72cc4c0e6');assert json.loads(accepted.read_bytes())['passed']
 for p,h in json.loads((parent/'pins.json').read_bytes())['files'].items():bind(p,h)
 bind(nativeprep/'report.json',digest);native=json.loads((nativeprep/'report.json').read_bytes());assert native['passed']
 nativepins=json.loads((nativeprep/'pins.json').read_bytes())if(nativeprep/'pins.json').exists()else native['files']
 for p,h in nativepins.get('files',nativepins).items():bind(p,h)
 for p,h in native.get('files',{}).items():bind(p,h)
 bind(source_lifts,lift_digest);lift=json.loads(source_lifts.read_bytes());assert lift['passed']
 for p,h in lift['files'].items():bind(p,h)
 bind(contracts,contract_digest);contract=json.loads(contracts.read_bytes());selected=contract['selected_order'];assert len(selected)==120 and len(contract['roots'])==4
 old_entries=[x['entry']for x in prior['selected_order']];new_entries=[x['entry']for x in selected];new_roots={r['entry']for r in contract['roots']}
 assert set(new_entries)-set(old_entries)==new_roots and [e for e in new_entries if e not in new_roots]==old_entries
 preflight=Path(preflight_path).resolve();bind(preflight,preflight_sha);assert json.loads(preflight.read_bytes())['passed']
 ghidra=Path(ghidra_path).resolve();bind(ghidra,ghidra_sha);assert json.loads(ghidra.read_bytes())['passed']
 game=ROOT/'MW3/Mech3.exe';bind(game,'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=PEImage(game.read_bytes())
 for p in parent.rglob('*'):
  if p.is_file()and p.suffix in('.cpp','.hpp','.inc'):write(out/p.relative_to(parent),p.read_text().replace(parent.as_posix(),out.as_posix()))
 protocol=(out/'joint_protocol.hpp').read_text();start=protocol.index('constexpr std::array<std::uint32_t,116> entries');end=protocol.index(';',start)
 replace(out/'joint_protocol.hpp',protocol[:start]+'constexpr std::array<std::uint32_t,120> entries{'+','.join(hex(x['entry'])for x in selected)+'}'+protocol[end:])
 fixed=[0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000]
 pages=sorted((set(prior['extra_pages'])|set(contract['source_data_pages']))-set(fixed));assert len(pages)==23 and set(pages)-set(prior['extra_pages'])=={0x5bc000,0x5cf000,0x5fc000}
 roots=prior['registration_roots']+[r['entry']for r in contract['roots']];assert len(set(roots))==92
 replace(out/'registration_contract.hpp','#pragma once\nnamespace mw34::m4_mixed {\nconstexpr std::array<unsigned,23> registration_pages{'+','.join(hex(x)for x in pages)+'};\nconstexpr std::array<unsigned,92> registration_roots{'+','.join(hex(x)for x in roots)+'};\n}\n')
 replace(out/'onexit_session.hpp',(nativeprep/'session.hpp').read_text())
 s=(out/'native_main.cpp').read_text();s=one(s,'phase==116&&r_.calls().size()==119&&r_.translation_count()==117','phase==120&&r_.calls().size()==123&&r_.translation_count()==121')
 for a,b in [('selected116','selected120'),('Connected116','Connected120'),('connected116','connected120'),('persistent116','persistent120'),('Joint116','Joint120'),('records.reserve(116)','records.reserve(120)'),('records.size()==116','records.size()==120'),('total==696','total==720'),('696native','720native'),('1,6,116,696,17,sizeof(Native)','1,6,120,720,17,sizeof(Native)'),('116-root','120-root')]:s=s.replace(a,b)
 replace(out/'native_main.cpp',s)
 objects={};bindings={};retained={};added_counts={}
 for r in contract['roots']:
  entry=r['entry'];b=lift['source_bodies'][f'f_{entry:x}'];size=b['source_bytes'];off,_=pe.rva_range(entry-pe.image_base,size);raw=pe.data[off:off+size]
  bindings[f'f_{entry:x}']=dict(entry=entry,size=size,file_offset=off,original_sha256=hashlib.sha256(raw).hexdigest(),literal_lift_input_sha256=b['source_sha256'],decoded_bytes=b['unique_decoded_bytes'])
 for level in('O0','O2'):
  retained[level]=prior['retained_unlinked_archives'][level];assert len(retained[level])==1
  old_objects=prior['objects'][level];assert len(old_objects)==336 and all(Path(p).suffix=='.obj'for p in old_objects)
  added=[p for p in native['entry_objects']if Path(p).stem.endswith('-'+level)]
  bypath={str(Path(p).resolve()).casefold():p for p in old_objects};assert len(bypath)==336
  for p in added:
   key=str(Path(p).resolve()).casefold()
   if key in bypath:assert sha(bypath[key])==sha(p),('Changed prior physical literal object',p)
   else:bypath[key]=p
  objects[level]=list(bypath.values());added_counts[level]=len(objects[level])-336;assert added_counts[level]>0
  for p in objects[level]:bind(p)
  old=(out/level/'registration_bindings.inc').read_text();lines=[]
  for r in contract['roots']:
   entry=r['entry'];a=bindings[f'f_{entry:x}'];obj=lift['source_bodies'][f'f_{entry:x}']['objects'][level]
   lines.append('r_.register_translation({{'+hex(entry)+'},{m4_runtime::Abi::Cdecl,0,true},&registration_entry,"Selected literal finite-vtable constructor root",{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,'+str(a['size'])+',"'+a['original_sha256']+'","'+obj['sha256']+'","'+sha(source_lifts)+'"}});')
  replace(out/level/'registration_bindings.inc',old+'\n'+'\n'.join(lines)+'\n')
 assert len(objects['O0'])==len(objects['O2'])==351 and added_counts['O0']==added_counts['O2']==15
 write(out/'runtime-entry-bindings.json',json.dumps(bindings,indent=2)+'\n')
 for name in('CMakeLists.txt','build.py','build.ps1','run.py'):
  p=HERE/name;bind(p);write(out/name,p.read_text())
 bind(__file__)
 report=dict(passed=True,scope='Connected120 preparation only; no execution credit',objects=objects,linked_literal_COFFs_per_level=len(objects['O0']),added_literal_COFFs_per_level=added_counts['O0'],retained_unlinked_archives=retained,native_library=str(nativeprep/'registry_library.cpp'),native_include=str(nativeprep),generated_sources=generated,physical_dependencies=pins,parent_acceptance=str(accepted),parent_acceptance_sha256=sha(accepted),source_lifts=str(source_lifts),source_lifts_sha256=sha(source_lifts),contracts=str(contracts),contracts_sha256=sha(contracts),selected_order=selected,registration_roots=roots,extra_pages=pages,connected_root_credit=False,native_executed=False,canonical_capture_transport=True)
 write(out/'report.json',json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps(dict(files=pins|generated),indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(out/'report.json'),sha256=sha(out/'report.json'),linked_COFFs=len(objects['O0']))))
if __name__=='__main__':main(*sys.argv[1:])
