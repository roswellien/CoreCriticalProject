"""Authentic13-root prerequisite-only worker; no constructor/provider invocation."""
from pathlib import Path
import hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];T=Path(__file__).resolve().parent;B=R/'reports/m4-constructor-original'
OLD=R/'reports/m4-mfc1168-connected-original/preparation-r3'
sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def one(s,a,b):need(s.count(a)==1,'Exact additive source '+a[:90]);return s.replace(a,b,1)
def main(name):
 out=B/name;need(not out.exists(),'Fresh constructor prerequisite preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No capture archives');v=sha(p);need(h is None or h==v,'Exact source '+str(p));pins[str(p)]=v;return p
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 def data(p,h=None):return json.loads(pin(p,h).read_bytes())
 old=data(OLD/'report.json','4f3510adc78d8766df79c9cd1c56bd1de754a483444d1caf3015e208f43850e1');need(old['passed'],'Current genuine prefix template')
 prerequisites=data(R/'reports/m4-remaining-service-source/prefix-prerequisites-r1/report.json','92783f81ad1a61ef521930c67c3d7b3ee34cdeeb02c0d8001e26355d99e8f806')
 selected=old['selected_order'][:13];need(len(selected)==13 and selected[-1]['slot']==0x5e0034,'Exact authentic selected prefix')
 raw=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();count=struct.unpack_from('<I',raw,8)[0];need(len(raw)==12+count*4104,'Whole old pack')
 records={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],raw[20+i*4104:4116+i*4104])for i in range(count)}
 game=PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 page=0x5f2000;need(page not in records,'Missing domain page is genuinely new')
 rva=page-game.image_base;section=next(s for s in game.sections if s['virtual_address']<=rva and rva+4096<=s['virtual_address']+max(s['virtual_size'],s['raw_size']))
 need(section['writable']and section['readable']and not section['executable'],'Physical game data permission')
 off,_=game.rva_range(rva,4096);bytes_=game.data[off:off+4096];need(len(bytes_)==4096,'Whole physical data page');records[page]=(2,bytes_)
 pack=raw[:8]+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,perm)+v for p,(perm,v)in records.items());need(len(pack)==12+4104*len(records)and all(len(v)==4096 for _,v in records.values()),'Whole new pack geometry')
 out.mkdir(parents=True);(out/'pages.bin').write_bytes(pack)
 spec=text(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"','pack_sha[]="'+sha(out/'pages.bin')+'"',spec);spec=re.sub(r'pack_size=\d+','pack_size='+str(len(pack)),spec)
 for field,values in [('entries',[v['entry']for v in selected]),('table_slots',[v['slot']for v in selected]),('page_bases',list(records)),('page_permissions',[v[0]for v in records.values()])]:
  pattern=r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;';need(len(re.findall(pattern,spec))==1,'Exact declaration '+field);spec=re.sub(pattern,f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};',spec)
 (out/'spec.hpp').write_text(spec);(out/'protocol.hpp').write_text(one(text(OLD/'protocol.hpp'),'sequences=1, roots=14','sequences=1, roots=13'))
 ref=text(OLD/'reference.cpp');ref=one(ref,'#include "connected_observer.hpp"','#include "connected_observer.hpp"\n#include "prerequisite_observer.hpp"')
 ref=one(ref,'std::array<void*,133> pages','std::array<void*,134> pages');ref=one(ref,'"MW4M131P"','"MW4C13PP"')
 ref=one(ref,'constexpr std::array<unsigned,3>extras{0x5cd000,0x5e3000,0x5e9000}','constexpr std::array<unsigned,4>extras{0x5cd000,0x5e3000,0x5e9000,0x5f2000}')
 ref=one(ref,'        const bool mfc_phase=phase==13;','        const bool mfc_phase=false;')
 ref=one(ref,'    for(unsigned phase=0;phase<entries.size();++phase){','    constructor_collect(0xffffffffU,"bootstrap");\n    for(unsigned phase=0;phase<entries.size();++phase){')
 ref=one(ref,'        const auto stem="phase/0/"+std::to_string(phase);registry_snapshot(stem+"/registry-before");','        const auto stem="phase/0/"+std::to_string(phase);registry_snapshot(stem+"/registry-before");constructor_graph(stem+"/BEFORE");')
 ref=one(ref,'registry_API_count=0;fs_error=0;std::memset(registry_API_ledger,0,sizeof(registry_API_ledger));mixed_before={};mixed_after={};r->tag.status=execute();','registry_API_count=0;fs_error=0;std::memset(registry_API_ledger,0,sizeof(registry_API_ledger));std::memset(registry_initial_sizes,0,sizeof(registry_initial_sizes));std::memset(registry_initial_bytes,0,sizeof(registry_initial_bytes));mixed_before={};mixed_after={};r->tag.status=execute();')
 ref=one(ref,'        copy_pages(r->memory_after);registry_snapshot(stem+"/registry-after");','        copy_pages(r->memory_after);registry_snapshot(stem+"/registry-after");constructor_collect(phase,stem);constructor_graph(stem+"/AFTER");')
 ref=one(ref,'    // Restore exact owning API cells before research registry cleanup. Borrowed','    constructor_graph("final13-BEFORE-constructors");\n    // Restore exact owning API cells before research registry cleanup. Borrowed')
 ref=one(ref,'one chronological13-root prefix plus genuine1168 completed; semantic/native acceptance pending','one authentic13-root prerequisite prefix completed; constructors unexecuted; semantic/native acceptance pending')
 (out/'reference.cpp').write_text(ref)
 copies=('reference_x86.asm','preserve_x86.asm','fs_observer_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','format_observer_x86.asm','format_observer.hpp','original_broker.hpp','boundaries.asm','api_boundaries.asm','connected_observer.hpp','CMakeLists.txt')
 for name_ in copies:(out/name_).write_text(text(OLD/name_))
 (out/'prerequisite_observer.hpp').write_text(text(T/'prerequisite_observer.hpp'))
 contracts=dict(selected_order=selected,root_frame=0x20001800,caller=dict(CW=0x007f,TOP=0,repeat=0),new_physical_data_page=dict(page=page,permission=2,file_offset=off,section=section,sha256=hashlib.sha256(bytes_).hexdigest()),actual_prerequisite_cells=[0x603fdc,0x603fe0,0x5f2a48,0x72c508,0x72c2cc],occurrence_bytes=48,occurrence_bound=1024,list_node_bound=256,whole_backing_capacity_bound=65536,HeapAlloc_initial_capture_bound=1024,allocation_identity='Actual sequential API invocation occurrence plus heap/pointer/phase/API ordinal; not OS generation',backing_policy='Complete genuine HeapAlloc-return initial bytes and current live whole list capacities; realloc API initial absent is explicitly not supplied',list_policy='Read actual next/prev/payload and traverse source next links to measured sentinel; no predicted count or seeded pointer',callback_scope='Actual registry publications carried through13 selected roots; callbacks not executed',new_constructor_entries_executed=[],borrowed_prefix_owner_cleanup=False,active_game_source_observers=[],trace_admitted=False,source_after_seed=False)
 (out/'contracts.json').write_text(json.dumps(contracts,indent=2)+'\n')
 for p in(Path(__file__),R/'tools/analysis/pe.py',R/'tools/m4-capture-direct/capture_direct_v3.hpp',R/'tools/m4-capture-direct/capture_direct_v3.cpp'):pin(p)
 for p in out.iterdir():pin(p)
 report=dict(passed=True,scope='Preparation-only genuine13-root prerequisite prefix; constructor roots unexecuted',parent_prefix_preparation_sha256=sha(OLD/'report.json'),prefix_prerequisites_sha256=sha(R/'reports/m4-remaining-service-source/prefix-prerequisites-r1/report.json'),selected_order=selected,source_spans=old['source_spans'],ordinary_pages=43,external_source_pages=[0x5cd000,0x5e3000,0x5e9000,0x5f2000],combined_source_pages=47,sparse_pack_pages=len(records),pack_bytes=len(pack),pack_sha256=sha(out/'pages.bin'),original_sequences=1,original_roots=13,original_phases=13,record_bytes=356992,source_frame=0x20001800,original_executed=False,capture_reader_opened=False,preinvoked_provider=False,source_after_seed=False,initializer_credit=0,contracts=str(out/'contracts.json'),files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
