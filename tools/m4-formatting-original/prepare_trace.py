"""Physical original CRT-only trace alongside exact normal game/service boundaries."""
from pathlib import Path
import hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-formatting-original';PARENT=BASE/'prefix-preparation-r3'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def one(s,a,b):
 need(s.count(a)==1,'One exact trace source edit '+a[:60]);return s.replace(a,b,1)
def main(contract_path,contract_digest,name):
 out=BASE/name;need(not out.exists(),'Fresh additive trace preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No inherited payload reader');v=sha(p);need(h is None or h==v,'Exact source '+str(p));pins[str(p)]=v;return p
 parent=json.loads(pin(PARENT/'report.json','6a41ecc0684a7440b05bad9ff1eb78470422c2ae95d5b3d636d1b7ee1da41138').read_bytes())
 for p,h in parent['files'].items():pin(p,h)
 receipt=json.loads(pin(contract_path,contract_digest).read_bytes())
 for p,h in receipt['files'].items():pin(p,h)
 source_contract_path=Path(receipt['instructions']);rows=json.loads(pin(source_contract_path,receipt['instructions_sha256']).read_bytes())['instructions']
 need(rows and all(0x78000000<=r['pc']<0x78040000 for r in rows),'Only actual original CRT instruction scopes')
 regs=['eax','ecx','edx','ebx','esp','ebp','esi','edi'];descriptors=[]
 for r in sorted(rows,key=lambda r:r['pc']):
  cells=[]
  for i,d in enumerate(r['decoded_operands']):
   if d['kind']!='memory':continue
   read=i in r['explicit_memory_reads'];write=i in r['explicit_memory_writes']
   if not(read or write):continue
   need(d['segment']=='default','Only explicit default-segment provider operands');coef=[0]*8
   for term in d['terms']:coef[regs.index(term['register'])]+=term['scale']
   cells.append(dict(displacement=d['displacement']&0xffffffff,coefficients=coef,width=d['bits']//8,read=int(read),write=int(write),segment=0))
  for d in r['implicit_memory']:
   if d['kind']=='string-read':continue
   write=d['kind']=='stack-write';need(write or d['kind']=='stack-read','Known literal stack cell');need(d['address']in('SSBASE+ESP-4','SSBASE+ESP','SSBASE+incomingESP','SSBASE+EBP'),'Actual incoming stack address');coef=[0]*8;coef[5 if d['address']=='SSBASE+EBP'else 4]=1
   cells.append(dict(displacement=0xfffffffc if write else 0,coefficients=coef,width=d['bits']//8,read=int(not write),write=int(write),segment=0))
  if r['mnemonic']in('scasb','scasw','scasd'):
   coef=[0]*8;coef[7]=1;cells.append(dict(displacement=0,coefficients=coef,width={'scasb':1,'scasw':2,'scasd':4}[r['mnemonic']],read=1,write=0,segment=0))
  if r['mnemonic']in('lodsb','lodsw','lodsd'):
   coef=[0]*8;coef[6]=1;cells.append(dict(displacement=0,coefficients=coef,width={'lodsb':1,'lodsw':2,'lodsd':4}[r['mnemonic']],read=1,write=0,segment=0))
  need(len(cells)<=4 and all(c['width']<=4 for c in cells),'Bounded complete actual memory cells');descriptors.append(dict(pc=r['pc'],width=r['width'],bytes_hex=r['bytes_hex'],mnemonic=r['mnemonic'],operands=r['operands'],kind=0,opcode=int(r['bytes_hex'][:2],16),cells=cells,repeat=r.get('repeat')))
 out.mkdir(parents=True)
 for p in PARENT.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(pin(p).read_bytes())
 (out/'trace_points.json').write_text(json.dumps(descriptors,indent=2)+'\n')
 cell=lambda c:'{'+','.join([hex(c['displacement']),'{'+','.join(map(str,c['coefficients']))+'}',str(c['width']),str(c['read']),str(c['write']),str(c['segment'])])+'}'
 text='#pragma once\nstruct TreeTraceMemory {unsigned displacement,coefficients[8],width,read,write,segment;};\nstruct TreeTracePoint {unsigned pc,width,kind,opcode,count;TreeTraceMemory cells[4];};\ninline constexpr std::array<TreeTracePoint,'+str(len(descriptors))+'> tree_trace_points{{\n'
 for d in descriptors:text+='{'+','.join(map(str,[d['pc'],d['width'],d['kind'],d['opcode'],len(d['cells'])]))+',{'+','.join(cell(c)for c in d['cells'])+'}},\n'
 (out/'trace_points.hpp').write_text(text+'}};\n')
 kernel=pin(ROOT/'tools/m4-tree-original/tree_trace.hpp').read_text()
 kernel=one(kernel,'get(&lockit_allocation_count,&owners,4);','get(&format_owner_count,&owners,4);')
 kernel=one(kernel,'owners<=64','owners<=16')
 kernel=one(kernel,'FsAllocation allocations[64]{};get(lockit_allocations,allocations,owners*sizeof(FsAllocation));','FormatOwner allocations[16]{};get(format_owners,allocations,owners*sizeof(FormatOwner));')
 kernel=kernel.replace('a.pointer','a.words[5]').replace('a.capacity','a.words[6]')
 (out/'tree_trace.hpp').write_text(kernel)
 ref=(out/'reference.cpp').read_text();ref=one(ref,'static std::uint32_t execute()','#include "tree_trace.hpp"\nstatic std::uint32_t execute()')
 ref=one(ref,'bool mw34::original_broker::handle_debug_checkpoint(HANDLE child,const DEBUG_EVENT&event){','bool mw34::original_broker::handle_debug_checkpoint(HANDLE child,const DEBUG_EVENT&event){\n if(tree_trace_debug(child,event))return true;')
 ref=one(ref,'const bool debugger=argc>1&&std::string(argv[argc-1])=="--checkpoint";mw34::original_broker::checkpoint_mode=debugger;','const bool debugger=false;mw34::original_broker::checkpoint_mode=true;')
 before='''            const auto crt_stem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/CRT-image/";std::vector<unsigned> crt_pages_metadata;
            for(unsigned page=0x78000000;page<0x78040000;page+=4096){MEMORY_BASIC_INFORMATION region{};require(VirtualQuery(reinterpret_cast<void*>(page),&region,sizeof(region))==sizeof(region),"Actual loaded CRT page query");const auto flags=region.Protect;if(region.State!=MEM_COMMIT||(flags&(PAGE_NOACCESS|PAGE_GUARD)))continue;crt_pages_metadata.push_back(page);crt_pages_metadata.push_back(flags);crt_pages_metadata.push_back(region.Type);out.append(crt_stem+"before/"+std::to_string(page)+".bin",reinterpret_cast<void*>(page),4096);}
            out.append(crt_stem+"metadata.bin",crt_pages_metadata.data(),crt_pages_metadata.size()*4);
'''
 ref=one(ref,'            r->tag.status=execute();fs_phase_root=0;',before+'            tree_trace_begin();r->tag.status=execute();tree_trace_finish();fs_phase_root=0;')
 marker='            const auto format_stem='
 after='''            const auto trace_stem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/format-trace/";out.append(trace_stem+"count.bin",&tree_trace_count,4);out.append(trace_stem+"events.bin",tree_trace_events,tree_trace_count*sizeof(TreeTraceEvent));
            for(unsigned i=0;i<crt_pages_metadata.size();i+=3)out.append(crt_stem+"after/"+std::to_string(crt_pages_metadata[i])+".bin",reinterpret_cast<void*>(crt_pages_metadata[i]),4096);
'''
 ref=one(ref,marker,after+marker);(out/'reference.cpp').write_text(ref)
 broker=(out/'original_broker.hpp').read_text();begin=broker.index('const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;std::cerr<<');end=broker.index('\n            if(handle_debug_checkpoint',begin);broker=broker[:begin]+'const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;'+broker[end:];(out/'original_broker.hpp').write_text(broker)
 pin(__file__)
 for p in out.iterdir():pin(p)
 report={**parent,'scope':'Separate actual original CRT instruction trace of three formatting prefixes; real table/owner/stack memory, source entry and return boundaries remain captured; no native or generic formatter claim','parent_preparation_sha256':sha(PARENT/'report.json'),'source_trace_contract_path':str(contract_path),'source_trace_contract_sha256':contract_digest,'trace_descriptors':len(descriptors),'trace_event_bytes':1656,'trace_event_bound':16384,'trace_cell_bytes':48,'debugger_context_bytes':716,'debugger_TF_RF_projection_mask':0x10100,'provider_only_trace':True,'CRT_page_endpoint_inputs':'Every genuinely readable committed loaded CRT page inside physical image extent; full BEFORE and AFTER retained independently, no post-state seed','files':pins}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),descriptors=len(descriptors))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
