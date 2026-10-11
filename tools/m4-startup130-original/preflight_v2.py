"""Light physical preparation/build gate. No original/native capture is opened."""
from pathlib import Path
import hashlib,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-startup130-original'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh light gate');out.mkdir(parents=True);pins={};passed=False;checks={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No capture reader');v=sha(p);need(h is None or v==h,'Exact dependency '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable identity');pins[str(p)]=v;return p
 def report(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 try:
  prep=BASE/'preparation-r1';p=report(prep/'report.json','89e159e71b3ae0a367bb33ee32c161cccae1aea45c005c2498c7e4e6ffb51af6');b=report(BASE/'build-r1/build.json','f1d29a95e80d91d282017339e0c7afd4676725f516b7b4e03b9c6e94d294d872')
  need(p['passed']and b['passed']and b['preparation_sha256']==sha(prep/'report.json'),'Actual final x86 build binds preparation')
  for parent in(p,report(BASE/'build-r1/pins.json')):
   for file,h in parent['files'].items():pin(file,h)
  accepted=report(ROOT/'reports/m4-joint-startup125-root/acceptance-r2/report.json','856ba8bd458e178f4a9afd91ff24299becc4debef76ee17c359da0f741165d51');need(accepted['passed'],'Accepted125 physical union receipt; inherited payload reread not performed here')
  selected=report(prep/'selected-order.json');old=report(ROOT/'reports/m4-tree-original/original125-preparation-r1/selected-order.json')
  additions={0x4b64f0:0x5e0160,0x4df610:0x5e01c8,0x4e0710:0x5e01cc,0x4e0810:0x5e01d0,0x4e1ca0:0x5e01d4}
  need(len(selected)==130 and[r['entry']for r in selected if r['entry']not in additions]==[r['entry']for r in old]and all(r['slot']==additions[r['entry']]for r in selected if r['entry']in additions),'Complete schedule and exact relative old order')
  need([r['phase']for r in selected]==list(range(130))and len({r['slot']for r in selected})==130,'Exact single invocation at130 distinct source slots')
  old_protocol=text(ROOT/'reports/m4-tree-original/original125-preparation-r1/protocol.hpp');protocol=text(prep/'protocol.hpp');need(protocol==old_protocol.replace('sequences=6, roots=125','sequences=6, roots=130'),'Fixed raw Record geometry changed only schedule count')
  need(p['record_bytes']==b['record_bytes']==356992 and p['ordinary_record_pages']==b['pages']==43 and p['combined_source_page_count']==b['combined_pages']==46 and b['external_pages']==3,'43 fixed pages plus3 separate complete external pages')
  hooks=report(prep/'fs-hook-bindings.json');need(len(hooks)==63 and len({r['PC']for r in hooks})==63,'Exact63 unique FS observers')
  ref=text(prep/'reference.cpp');header=text(prep/'format_observer.hpp');spec=text(prep/'spec.hpp')
  need(ref.count('mixed_allocation_count=0;')==1 and ref.count('format_owner_count=0;')==1,'Dynamic owners reset only at complete sequence bootstrap')
  need(ref.index('mixed_allocation_count=0;')<ref.index('for(unsigned phase=0;phase<entries.size();++phase)')and ref.index('format_owner_count=0;')<ref.index('for(unsigned phase=0;phase<entries.size();++phase)'),'Persistent live owner inventory across all phases')
  need('mixed_owner_heaps[e.index]=registry_API_ledger[ai].args[0];std::memcpy(mixed_owner_initial[e.index],registry_initial_bytes[ai],capacity);'in ref and 'registry_initial_bytes[a.API_index],a.capacity'not in ref,'Whole mixed initial backing copied at actual API return before later ledger resets')
  need('HeapSize(reinterpret_cast<HANDLE>(mixed_owner_heaps[a.index]),0,reinterpret_cast<void*>(a.pointer))'in ref,'Persistent actual heap identity avoids interpreting a later phase ledger')
  stutter='if(fs_phase_root!=0x4df610&&fs_phase_root!=0x4e0710&&fs_phase_root!=0x4e0810&&fs_phase_root!=0x4e1ca0)return;'
  need(header.count(stutter)==1 and header.index(stutter)<header.index('GetLastError()'),'Other selected roots stutter before host API/observer mutation')
  producer=ref.index('"Actual original registry producer CALL/RET"');loop=ref.index('for(unsigned phase=0;phase<entries.size();++phase)');install=ref.index('        install_format_hooks();');restore=ref.index('"Restore actual formatting return source"');source_conservation=ref.index('"Original selected source changed after checkpoint"');cleanup=ref.index('remove_CRT_hooks();registry_cleanup.restore();')
  need(producer<install<loop<restore<source_conservation<cleanup,'Formatting hooks admitted only after producer, restored before source conservation and genuine cleanup')
  need('"Restore formatting named source IAT"'in ref and 'if(sequence+1<sequences)install_CRT_hooks();'in ref,'Named game IAT and CRT hooks restore/reinstall each sequence')
  need('101*4,"Exact101callback vector extent"'in ref and '0x4e1ca0,0x60b668,0x60b7d4,0x60b7d0,24'in spec,'101 callback source domain and mixed actual Lockit object/header mapping')
  need('std::array<unsigned,3> format_extra_pages{0x5cd000,0x5e3000,0x5e9000}'in ref and '/extra-before/'in ref and '/extra-after/'in ref,'All3 external pages retained whole at every phase endpoint')
  need('if(format_phase){for(unsigned page=0x78000000;page<0x78040000;page+=4096)'in ref and 'crt_stem+"before/"'in ref and 'crt_stem+"after/"'in ref,'Actual current complete loaded CRT pages retained for four new formatter domains')
  raw=pin(prep/'pages.bin',p['pack_sha256']).read_bytes();need(raw[:8]==b'MW4J124P'and len(raw)==12+4104*p['sparse_pack_pages'],'Exact sparse input pack geometry')
  records={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],raw[20+i*4104:4116+i*4104])for i in range(struct.unpack_from('<I',raw,8)[0])};need(records[0x5e8000][0]==2,'Physical data output page writable')
  oldprep=report(ROOT/'reports/m4-tree-original/original125-preparation-r1/report.json');oldpack=pin(ROOT/'reports/m4-tree-original/original125-preparation-r1/pages.bin',oldprep['pack_sha256']).read_bytes();oldrecords={struct.unpack_from('<I',oldpack,12+i*4104)[0]:(struct.unpack_from('<I',oldpack,16+i*4104)[0],oldpack[20+i*4104:4116+i*4104])for i in range(struct.unpack_from('<I',oldpack,8)[0])}
  loader_pages=[page for page in oldprep['observed_pages']if page not in oldrecords]
  need(loader_pages==[0x780c1000,0x78115000,0x5f498000,0x5f4cc000,0x7810a000,0x78145000,0x78146000],'Seven authentic DLL-loaded pages are not sparse authored input records')
  for page in oldprep['observed_pages']:
   if page in oldrecords:need(records[page][1]==oldrecords[page][1],'Every complete inherited sparse raw data/stack input page unchanged')
  need(not p['predicted_counts_supplied_to_execution']and not p['source_output_seed']and not p['initializer_credit'],'Prepared input source bytes/interfaces only, no credit or supplied effects')
  checks=dict(relative_roots_retained=125,added_roots=5,roots=130,sequences=6,phases=780,callback_source_domain=101,ordinary_record_pages=43,extra_complete_pages=3,combined_pages=46,FS_observer_sites=63,fixed_Record_bytes=356992,source_MFC_owner_domain=35+10+5+15+3,source_positive_string_domain=19,source_format_owner_domain=4,source_registry_owner_domain=1,source_ordinary_owner_domain=92,source_owner_counts_are_observation_predictions=True,inherited_whole_sparse_input_pages_checked=36,authentic_loaded_provider_pages=7,actual_current_CRT_page_inputs_for_four_roots=True,transparent_outside_format_roots=True,owner_initial_backings_persistent=True,format_restore_before_cleanup=True,inherited_capture_reader_opened=False,execution_performed=False,initializer_credit=False)
  pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'report.json').write_text(json.dumps(dict(passed=passed,scope='Physical full130 preparation/build/source-interface preflight only; fresh execution, independent source/paired gates and final full identity rehash remain separate.',preparation_sha256=pins.get(str((BASE/'preparation-r1/report.json').resolve())),build_sha256=pins.get(str((BASE/'build-r1/build.json').resolve())),checks=checks,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
