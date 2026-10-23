"""Immutable physical origin continuity correction, no imports/source reader."""
from pathlib import Path
import hashlib,json,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141-source/retained-corpus-preparation-r2';assert not out.exists();out.mkdir();p=R/'tools/m4-original141-source/retained_corpus141_v1.py';q=p.with_name('retained_corpus141_v2.py');assert not q.exists();a=p.read_text();b=a
 old=""" for row in rows:
  at=row['pc'];n=row['size'];assert n>0 and(at&4095)+n<=4096;page=at&~4095;assert oldpages[page][1][at&4095:(at&4095)+n]==newpages[page][1][at&4095:(at&4095)+n]
"""
 new=""" # Every origin is physical source, not an observed endpoint or row omission.
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
"""
 assert b.count(old)==1;b=b.replace(old,new)
 oldresult='current_total_source_spans=6411,source_model_equivalence=False'
 newresult='current_total_source_spans=6411,current_physical_source_origin_counts=origin_counts,current_source_overlay_pair_counts=packed_counts,current_source_physical_images=physical,every_retained_span_physical_offset_and_bytes_proved=True,source_model_equivalence=False'
 assert b.count(oldresult)==1;b=b.replace(oldresult,newresult);q.write_text(b);assert b.replace(newresult,oldresult).replace(new,old)==a
 before=a.splitlines(True);after=b.splitlines(True);d=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
  if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(before[i:j]),child=''.join(after[k:l])))
 (out/'inverse.json').write_text(json.dumps(d,indent=2)+'\n');deps=[p,q,R/'tools/analysis/pe.py',R/'MW3/Mech3.exe',R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',R/'reports/m4-startup131-original/preparation-r4/report.json',R/'reports/m4-startup131-original/preparation-r4/pages.bin',R/'reports/m4-startup131-original/preparation-r4/reference.cpp',R/'reports/m4-original141/source-preparation-r6/report.json',R/'reports/m4-original141/source-preparation-r6/spec.hpp',R/'reports/m4-original141/source-preparation-r6/pages.bin',R/'reports/m4-original141/source-preparation-r6/reference.cpp',out/'inverse.json',Path(__file__).resolve()];files={str(x.resolve()):sha(x)for x in deps}
 (out/'ROOT-recipe.txt').write_text('UNEXECUTED physical continuity correction. ROOT independently reviews entirev2, exact wholeinverse and all3980 origin rows/current6411 declarations. Admit PEhelper, actual Game/MSVCP50 images and both source packs/writers/reports before imported PE parser. Physically compare raw source bytes by exactpreferredPC↔image_offset; require both Game overlays, additionally check any provider overlay. Origin1 absent pack is not row exclusion: actualphysical loaded provider is genuine source and both compiledwriters explicitlyverify provider span bytes. Retain all rows and no endpoint input. Before source retry use immutable controller binding only retained_corpus141_v1→v2; all other source/family/registry/reader checks unchanged. No original source CPU/Machine/model equivalence or accepted credit from static continuity.\n');files[str(out/'ROOT-recipe.txt')]=sha(out/'ROOT-recipe.txt')
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_reader_opened=False,initializer_credit=0,exact_whole_inverse=True,inverse_hunks=len(d),required_retained_rows=3980,source_origin_counts={0:3962,1:18},origin_semantics={0:'Actual staged Game rawfile and both exact sourcepack overlays',1:'Actual staged MSVCP50 preferred raw provider, compiledwriter runtime raw-span verifier; optional sourcepack overlays checked if present'},no_row_skipped=True,no_AFTER_source_input=True,controller_rebinding_pending=True,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),inverse_hunks=len(d))))
if __name__=='__main__':main()
