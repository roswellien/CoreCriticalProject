"""Current physical131 source continuity; no cached current result oracle."""
import json,re,struct
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def prove(C,pin):
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 old=read(R/'reports/m4-startup131-original/preparation-r4/report.json','1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb')
 actual=read(C['source_preparation']['path'],C['source_preparation']['sha256']);order=read(C['selected_order']['path'],C['selected_order']['sha256']);directory=Path(C['source_preparation']['path']).parent
 assert actual['root_count']==len(order)==141 and actual['phases']==846 and actual['callback_count']==111
 prior={r['entry']for r in old['selected_order']};assert len(prior)==131 and [r for r in order if r['entry']in prior]==old['selected_order']
 text=pin(directory/'spec.hpp').read_text();match=re.search(r'std::array<CodeBinding,(\d+)> code_bindings\{\{(.*?)\}\};',text,re.S);assert match
 current=[tuple(int(v.strip(),0)for v in row.split(','))for row in re.findall(r'\{([^{}]+)\}',match[2])];assert len(current)==int(match[1])==6411 and len(set(current))==6411
 declared=set(current);rows=old['source_spans'];assert len(rows)==3980
 for row in rows:assert tuple(row[k]for k in('pc','size','image_offset','origin'))in declared
 def pages(p):
  b=pin(p).read_bytes();assert b[:8]==b'MW4J124P';n=struct.unpack_from('<I',b,8)[0];assert len(b)==12+n*4104
  out={}
  for i in range(n):
   off=12+i*4104;address,permission=struct.unpack_from('<2I',b,off);assert address not in out and address%4096==0;out[address]=(permission,b[off+8:off+4104])
  return out
 oldpages=pages(R/'reports/m4-startup131-original/preparation-r4/pages.bin');newpages=pages(directory/'pages.bin')
 # Every origin is physical source, not an observed endpoint or row omission.
 # The actual compiled writers select raw Game for0 and MSVCP50 for1.
 import importlib.util
 pe_path=pin(R/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638');s=importlib.util.spec_from_file_location('original141_continuity_PE',pe_path);PE=importlib.util.module_from_spec(s);s.loader.exec_module(PE)
 role_specs={0:(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf',2384384,0x400000,'Game'),1:(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a',565760,0x780c0000,'MSVCP50')}
 images={};physical=[];origin_counts={0:0,1:0};packed_counts={0:0,1:0}
 for origin,(path,digest,size,base,name)in role_specs.items():
  raw=pin(path,digest).read_bytes();assert len(raw)==size;image=PE.PEImage(raw);assert image.image_base==base;images[origin]=image;physical.append(dict(origin=origin,name=name,path=str(path.resolve()),sha256=digest,bytes=size,preferred_base=base))
 for writer in(R/'reports/m4-startup131-original/preparation-r4/reference.cpp',directory/'reference.cpp'):
  writer_text=pin(writer).read_text();assert 'const auto&origin=span.origin?provider:image;'in writer_text and 'provider.data()+span.image_offset,span.size)'in writer_text and '91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'in writer_text
  assert 'const auto image=read(argv[2],2384384)'in writer_text and 'const auto provider=read(argv[3],565760)'in writer_text
 for row in rows:
  at=row['pc'];n=row['size'];origin=row['origin'];offset=row['image_offset'];assert origin in images and type(n)is int and n>0 and(at&4095)+n<=4096;page=at&~4095;image=images[origin]
  actual_offset,_=image.rva_range(at-image.image_base,n);assert actual_offset==offset and offset+n<=len(image.data),'Exact physical PC/preferred base/file-offset relation';raw=image.data[offset:offset+n];assert len(raw)==n
  # Source0 executes the sparse pack. Both prior/current declared overlays must
  # exist and equal complete physical raw source bytes. Source1 executes the
  # actual loaded provider and its raw bytes are checked by both writer bodies.
  # Any packed source1 overlay is additionally checked, never used as fallback.
  assert origin!=0 or(page in oldpages and page in newpages),'Every Game source row retained in both actual packs'
  assert(page in oldpages)==(page in newpages)or origin==1,'No missing Game overlay'
  for packed in(oldpages,newpages):
   if page in packed:assert packed[page][1][at&4095:(at&4095)+n]==raw,'Every available prior/current source overlay equals entire physical source span'
  origin_counts[origin]+=1;packed_counts[origin]+=int(page in oldpages and page in newpages)
 assert sum(origin_counts.values())==3980 and origin_counts=={0:3962,1:18}
 return dict(passed=True,current_physical_131_root_table_pairs=131,current_exact_retained_source_spans=3980,current_total_source_spans=6411,current_physical_source_origin_counts=origin_counts,current_source_overlay_pair_counts=packed_counts,current_source_physical_images=physical,every_retained_span_physical_offset_and_bytes_proved=True,source_model_equivalence=False,current_result_oracle_used=False,full_original131_CPU_executed=False,scope='Every accepted131 physical source declaration and byte span remains current141, exact relative root/slot order. Fresh semantic families and actual strict observation are separate required domains.',original_validation_sha256=C['validation']['sha256'],source_AFTER_seed=False,canonical_reader_opened=False,initializer_credit=0)
