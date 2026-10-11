"""Narrow additive corrections: exact observer span and literal CRT record."""
from pathlib import Path
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-container-source'
s=(T/'validate_FS_observations.py').read_text()
old="a[0]==pending['predecessor']and a[2]==0xffffffff"
assert s.count(old)==1
s=s.replace(old,"a[0]==pending['predecessor']and ((a[1],a[2])==(0x7800ef03,0x7802e260)if pc>=0x78000000 else a[2]==0xffffffff)")
(T/'validate_FS_observations_v2.py').write_text(s)
s=(T/'compare_paired_policy_v2.py').read_text()
old="  loader_rows=[];loader_differences=delta(loaded_page,raw_page);"
new="""  observer_gate=json.loads(pin(ROOT/'reports/m4-container-review/observer-compiled-r3/report.json','9cd673ab15e2a6e06baa617a7d84ee341e85fb80d41531e253a7449933642e59').read_bytes());need(observer_gate['passed'],'Compiled transparent FS original observer');build=json.loads(pin(ROOT/'reports/m4-container-source/original-build-r2/build.json','8b1e7694bf3d9a651b729dc6740310c72c1b7409918de62c9411394da3021541').read_bytes());execution=json.loads(pin(ROOT/'reports/m4-container-source/original-execution-r1/report.json','8a326c950272031da3423a4462a16ff9a408e1e9c83bb794cde67218ae3731bc').read_bytes());worker_path=ROOT/'reports/m4-container-source/original-build-r2/original-worker.exe';worker_bytes=pin(worker_path,execution['files'][str(worker_path.resolve())]).read_bytes();worker=PE.PEImage(worker_bytes);need(worker.image_base==0x18000000,'Actual original fixed declared worker base');observer_spans=[]
  for hook in json.loads(pin(ROOT/'reports/m4-container-source/original-preparation-r2/fs-hook-bindings.json').read_bytes()):
   pc=hook['PC'];raw=bytes.fromhex(hook['raw_bytes'])
   if pc&~4095 not in PAGES:continue
   key=struct.pack('<3I',pc,len(raw),hook['kind']);matches=[i for i in range(len(worker_bytes))if worker_bytes.startswith(key,i)and worker_bytes[i+16:i+16+len(raw)]==raw];need(len(matches)==1,'One physical linked FsHook initializer for observed source span');target=words(worker_bytes,matches[0]+12)[0];toff,_=worker.rva_range(target-worker.image_base,1);need(worker_bytes[toff:toff+2]==bytes.fromhex('8905'),'Actual compiled trampoline begins saving source ESP before pushes');original_bytes=b'\\xe9'+struct.pack('<I',(target-pc-5)&0xffffffff)+b'\\x90'*(len(raw)-5);observer_spans.append(dict(PC=pc,width=len(raw),original_hex=original_bytes.hex(),native_hex=raw.hex(),compiled_target=target,compiled_table_offset=matches[0],declared_symbol=hook['declared_observer']))
  need([(r['PC'],r['width'])for r in observer_spans]==[(0x482b47,6),(0x482b4e,7),(0x482b8e,7)],'Only three exact observed-page original observer spans')
  loader_rows=[];loader_differences=delta(loaded_page,raw_page);"""
assert s.count(old)==1;s=s.replace(old,new)
old="       differences=delta(original,actual);declared=set()"
new="""       differences=delta(original,actual);declared=set()
       for span in observer_spans:
        if span['PC']&~4095!=page:continue
        off=span['PC']&4095;n=span['width'];equal(original[off:off+n],bytes.fromhex(span['original_hex']),'Exact source-bound original compiled transparent observer JMP/padding');equal(actual[off:off+n],bytes.fromhex(span['native_hex']),'Native keeps exact physical literal FS MOV bytes');declared.update(range(off,off+n));counts['exact_observer_span_relations']+=1"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("(('paired-observations.json',rows),","(('observer-span-relations.json',observer_spans),('paired-observations.json',rows),")
s=s.replace("owning_IAT_projection_addresses=list(IATS),","owning_IAT_projection_addresses=list(IATS),observed_original_observer_spans=observer_spans,")
s=s.replace('native109','native116').replace('original/native109','original/native116')
(T/'compare_paired_policy_v3.py').write_text(s)
