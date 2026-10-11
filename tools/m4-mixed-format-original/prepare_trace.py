"""Reuse the sealed exact CRT trace kernel on a fresh authentic mixed-root process."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-mixed-format-original';PARENT=BASE/'prefix-preparation-r1';TRACE=ROOT/'reports/m4-formatting-original/trace-preparation-r2'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(s,a,b):
 assert s.count(a)==1,a[:90];return s.replace(a,b,1)
def main(name):
 out=BASE/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix!='.mwb';v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 parent=json.loads(pin(PARENT/'report.json','9a770096b8f19c794e150771a7578832a30a333a65f93619882895769930a779').read_bytes());trace=json.loads(pin(TRACE/'report.json','213677732af503f385447dc4c885d1f8f798d316e1d1fe23cce05684cd28906c').read_bytes())
 for receipt in(parent,trace):
  for p,h in receipt['files'].items():pin(p,h)
 out.mkdir(parents=True)
 for p in PARENT.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(pin(p).read_bytes())
 for fn in('trace_points.json','trace_points.hpp','tree_trace.hpp'):(out/fn).write_bytes(pin(TRACE/fn).read_bytes())
 ref=(out/'reference.cpp').read_text();ref=one(ref,'static std::uint32_t execute()','#include "tree_trace.hpp"\nstatic std::uint32_t execute()');ref=one(ref,'bool mw34::original_broker::handle_debug_checkpoint(HANDLE child,const DEBUG_EVENT&event){','bool mw34::original_broker::handle_debug_checkpoint(HANDLE child,const DEBUG_EVENT&event){\n if(tree_trace_debug(child,event))return true;');ref=one(ref,'const bool debugger=argc>1&&std::string(argv[argc-1])=="--checkpoint";mw34::original_broker::checkpoint_mode=debugger;','const bool debugger=false;mw34::original_broker::checkpoint_mode=true;')
 before='''            const auto crt_stem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/CRT-image/";std::vector<unsigned> crt_pages_metadata;
            for(unsigned page=0x78000000;page<0x78040000;page+=4096){MEMORY_BASIC_INFORMATION region{};require(VirtualQuery(reinterpret_cast<void*>(page),&region,sizeof(region))==sizeof(region),"Actual loaded CRT page query");const auto flags=region.Protect;if(region.State!=MEM_COMMIT||(flags&(PAGE_NOACCESS|PAGE_GUARD)))continue;crt_pages_metadata.push_back(page);crt_pages_metadata.push_back(flags);crt_pages_metadata.push_back(region.Type);out.append(crt_stem+"before/"+std::to_string(page)+".bin",reinterpret_cast<void*>(page),4096);}
            out.append(crt_stem+"metadata.bin",crt_pages_metadata.data(),crt_pages_metadata.size()*4);
'''
 ref=one(ref,'            r->tag.status=execute();fs_phase_root=0;',before+'            tree_trace_begin();r->tag.status=execute();tree_trace_finish();fs_phase_root=0;')
 after='''            const auto trace_stem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/format-trace/";out.append(trace_stem+"count.bin",&tree_trace_count,4);out.append(trace_stem+"events.bin",tree_trace_events,tree_trace_count*sizeof(TreeTraceEvent));out.append(trace_stem+"segments.bin",tree_trace_selectors,sizeof(tree_trace_selectors));out.append(trace_stem+"segments-ready.bin",&tree_trace_selectors_ready,4);
            for(unsigned i=0;i<crt_pages_metadata.size();i+=3)out.append(crt_stem+"after/"+std::to_string(crt_pages_metadata[i])+".bin",reinterpret_cast<void*>(crt_pages_metadata[i]),4096);
'''
 ref=one(ref,'            const auto format_stem=',after+'            const auto format_stem=');(out/'reference.cpp').write_text(ref)
 broker=(out/'original_broker.hpp').read_text();begin=broker.index('const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;std::cerr<<');end=broker.index('\n            if(handle_debug_checkpoint',begin);broker=broker[:begin]+'const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;'+broker[end:];(out/'original_broker.hpp').write_text(broker)
 pin(__file__)
 for p in out.iterdir():pin(p)
 report={**parent,'scope':'Separate genuine original mixed-root CRT trace using the exact sealed729-point kernel; no native or cold formatting path claim','parent_preparation_sha256':sha(PARENT/'report.json'),'trace_kernel_preparation_sha256':sha(TRACE/'report.json'),'source_trace_contract_path':str(ROOT/'reports/m4-formatting-source/provider-recovery-r2/report.json'),'source_trace_contract_sha256':'2aa9a712983ab98a08c3f59adf8e29b24c17f1f8c0d41ebb786a55c7241a13b9','trace_descriptors':729,'trace_event_bytes':1656,'trace_event_bound':16384,'trace_cell_bytes':48,'debugger_context_bytes':716,'debugger_TF_RF_projection_mask':0x10100,'provider_only_trace':True,'segment_evidence_bytes':60,'CRT_page_endpoint_inputs':'All genuinely readable committed original CRT pages, independently before/after','files':pins}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
