"""Separate bounded genuine debugger instruction trace from frozen normal prefix."""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-tree-original'
PARENT=BASE/'prefix-preparation-r1'

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
def one(s,a,b):
    need(s.count(a)==1,'Exactly one source edit '+a[:60]);return s.replace(a,b,1)
def main(name):
    out=BASE/name;need(not out.exists(),'Fresh additive trace preparation');pins={}
    def pin(p,h=None):
        p=Path(p).resolve();need(p.suffix!='.mwb','No inherited archive reader');v=sha(p);need(h is None or h==v,'Exact source identity '+str(p));need(str(p) not in pins or pins[str(p)]==v,'Stable identity');pins[str(p)]=v;return p
    parent=json.loads(pin(PARENT/'report.json','0ed3a7baf7998b697390041dcf8241c28cc0d8689959c423a72f7971382e39e3').read_bytes())
    for p,h in parent['files'].items():pin(p,h)
    tree=json.loads(pin(ROOT/'reports/m4-tree-source/recovery-r1/instruction-contracts.json').read_bytes())
    module_spec=importlib.util.spec_from_file_location('tree_trace_literal_input',pin(ROOT/'tools/m4-tree-source/game_model.py'))
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module);program,callbacks=module.source_program()
    rows={r['pc']:r for r in tree['instructions']}
    extras=[r for pc,r in program.items() if 0x5f401ea0<=pc<=0x5f401ec8 or pc==0x5abd26]
    need(len(extras)==20,'Complete normal MFC allocator body plus game import thunk')
    for r in extras:
        need(r['pc'] not in rows or rows[r['pc']]==r,'Exact shared allocator import extension');rows[r['pc']]=r
    for loaded in list(sys.modules.values()):
        path=getattr(loaded,'__file__',None)
        if path and str(ROOT/'tools').lower() in str(Path(path).resolve()).lower():pin(path)
    hooks={r['PC']:r for r in json.loads(pin(PARENT/'fs-hook-bindings.json').read_bytes())}
    regs=['eax','ecx','edx','ebx','esp','ebp','esi','edi'];descriptors=[]
    for pc,r in sorted(rows.items()):
        cells=[];fs=pc in hooks
        if not fs:
            for i,d in enumerate(r['decoded_operands']):
                if d['kind']!='memory':continue
                read=i in r['explicit_memory_reads'];write=i in r['explicit_memory_writes']
                if not(read or write):continue
                need(d['segment']=='default','Non-FS literal memory operand');coef=[0]*8
                for term in d['terms']:coef[regs.index(term['register'])]+=term['scale']
                cells.append(dict(displacement=d['displacement']&0xffffffff,coefficients=coef,width=d['bits']//8,read=int(read),write=int(write),segment=0))
            for d in r['implicit_memory']:
                write=d['kind']=='stack-write';need(write or d['kind']=='stack-read','Known literal implicit source cell')
                need(d['address'] in ('SSBASE+ESP-4','SSBASE+ESP','SSBASE+incomingESP'),'Actual incoming stack address')
                coef=[0]*8;coef[4]=1
                cells.append(dict(displacement=0xfffffffc if write else 0,coefficients=coef,width=d['bits']//8,read=int(not write),write=int(write),segment=0))
        need(len(cells)<=4,'Bounded complete instruction cells')
        descriptors.append(dict(pc=pc,width=r['width'],bytes_hex=r['bytes_hex'],mnemonic=r['mnemonic'],operands=r['operands'],kind=1 if fs else 0,opcode=0xe9 if fs else int(r['bytes_hex'][:2],16),cells=cells))
    out.mkdir(parents=True)
    filenames=['pages.bin','spec.hpp','protocol.hpp','original_broker.hpp','reference.cpp','reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','fs_observer_x86.asm','fs-hook-bindings.json','CMakeLists.txt']
    for filename in filenames:(out/filename).write_bytes(pin(PARENT/filename).read_bytes())
    (out/'trace_points.json').write_text(json.dumps(descriptors,indent=2)+'\n')
    cell=lambda c:'{'+','.join([hex(c['displacement']),'{'+','.join(map(str,c['coefficients']))+'}',str(c['width']),str(c['read']),str(c['write']),str(c['segment'])])+'}'
    text='#pragma once\nstruct TreeTraceMemory {unsigned displacement,coefficients[8],width,read,write,segment;};\nstruct TreeTracePoint {unsigned pc,width,kind,opcode,count;TreeTraceMemory cells[4];};\ninline constexpr std::array<TreeTracePoint,'+str(len(descriptors))+'> tree_trace_points{{\n'
    for d in descriptors:text+='{'+','.join(map(str,[d['pc'],d['width'],d['kind'],d['opcode'],len(d['cells'])]))+',{'+','.join(cell(c) for c in d['cells'])+'}},\n'
    (out/'trace_points.hpp').write_text(text+'}};\n')
    (out/'tree_trace.hpp').write_bytes(pin(Path(__file__).parent/'tree_trace.hpp').read_bytes())
    ref=(out/'reference.cpp').read_text()
    marker='static std::uint32_t execute()'
    need(ref.count(marker)==1,'Trace header after genuine owner definitions');ref=ref.replace(marker,'#include "tree_trace.hpp"\n'+marker,1)
    ref=one(ref,'bool mw34::original_broker::handle_debug_checkpoint(HANDLE child,const DEBUG_EVENT&event){','bool mw34::original_broker::handle_debug_checkpoint(HANDLE child,const DEBUG_EVENT&event){\n if(tree_trace_debug(child,event))return true;')
    ref=one(ref,'const bool debugger=argc>1&&std::string(argv[argc-1])=="--checkpoint";mw34::original_broker::checkpoint_mode=debugger;','const bool debugger=false;mw34::original_broker::checkpoint_mode=true;')
    ref=one(ref,'r->tag.status=execute();fs_phase_root=0;','tree_trace_begin();r->tag.status=execute();tree_trace_finish();fs_phase_root=0;')
    ref=one(ref,'const auto lockbase="phase/"','out.append("tree-trace/count.bin",&tree_trace_count,4);out.append("tree-trace/events.bin",tree_trace_events,tree_trace_count*sizeof(TreeTraceEvent));\n            const auto lockbase="phase/"')
    (out/'reference.cpp').write_text(ref)
    broker=(out/'original_broker.hpp').read_text()
    begin=broker.index('const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;std::cerr<<')
    end=broker.index('\n            if(handle_debug_checkpoint',begin)
    broker=broker[:begin]+'const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;'+broker[end:]
    (out/'original_broker.hpp').write_text(broker)
    pin(__file__)
    for p in out.iterdir():pin(p)
    report={**parent,'scope':'Separate bounded genuine debugger trace; physical one-instruction execution, actual memory/control observations. Debugger CONTEXT/TF metadata are projected and distinct from frozen normal raw machine observations. No broad125 execution or initializer credit.','parent_preparation_sha256':sha(PARENT/'report.json'),'trace_descriptors':len(descriptors),'trace_event_bytes':1656,'trace_event_bound':16384,'trace_cell_bytes':48,'debugger_context_bytes':716,'debugger_observer_TF':True,'FS_trace_kind':'actual transparent FS-observer JMP; source FS semantics only from full raw FsEvent records','physical_after_effects_supplied':False,'files':pins}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
    print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),descriptors=len(descriptors))))
if __name__=='__main__':main(sys.argv[1])
