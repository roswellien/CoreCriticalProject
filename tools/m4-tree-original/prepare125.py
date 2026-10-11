"""Full125 genuine original schedule, additive to accepted124.

No derived source effects enter execution. The already measured prefix supplies
only exact code/interface geometry and safe observer bounds.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-tree-original'
OLD=ROOT/'reports/m4-lockit-original/original-preparation-r4'
PREFIX=BASE/'prefix-preparation-r1'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
def one(s,a,b):
    need(s.count(a)==1,'One exact additive edit '+a[:70]);return s.replace(a,b,1)
def array(s,field):return [int(v,16) for v in re.search(r' '+field+r'\{([^;]+)\};',s)[1].split(',')]
def replace_array(s,field,values):
    old=re.search(r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;',s)[0]
    return one(s,old,'inline constexpr std::array<std::uint32_t,'+str(len(values))+'> '+field+'{'+','.join(hex(v) for v in values)+'};')
def main(name):
    out=BASE/name;need(not out.exists(),'Fresh additive full125 preparation');pins={}
    def pin(p,h=None):
        p=Path(p).resolve();need(p.suffix!='.mwb','No inherited capture reader');v=sha(p);need(h is None or h==v,'Exact identity '+str(p));need(str(p) not in pins or pins[str(p)]==v,'Stable physical identity');pins[str(p)]=v;return p
    def text(p):return pin(p).read_text(encoding='utf-8-sig')
    old=json.loads(pin(OLD/'report.json','6a25b9b16ccdbfefe30488ea6b87afd5c266489fd63f2b5710c05c04a14fd68b').read_bytes())
    prefix=json.loads(pin(PREFIX/'report.json','0ed3a7baf7998b697390041dcf8241c28cc0d8689959c423a72f7971382e39e3').read_bytes())
    measured=json.loads(pin(BASE/'prefix-validation-r2/report.json','58e023bb24afc474b164c454bc3591bf2cd476c70b3ce90607251ea67583a920').read_bytes())
    trace=json.loads(pin(BASE/'trace-validation-r2/report.json','1c099256ca7bdc076bffa23a37c9aab6975a4769337ce8c7cff64ba623bea463').read_bytes())
    need(measured['passed'] and trace['passed'],'Actual bounded prefix and instruction observation gates')
    for parent in (old,prefix):
        for p,h in parent['files'].items():pin(p,h)
    spec=text(OLD/'spec.hpp');prefix_spec=text(PREFIX/'spec.hpp')
    old_entries=array(spec,'entries');old_slots=array(spec,'table_slots')
    pairs=sorted(list(zip(old_slots,old_entries))+[(0x5e0168,0x4b7f70)])
    need(len(pairs)==125 and [p for p in pairs if p!=(0x5e0168,0x4b7f70)]==list(zip(old_slots,old_entries)),'Accepted124 complete relative order unchanged')
    sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
    game=PEImage(pin(ROOT/'MW3/Mech3.exe').read_bytes())
    for slot,entry in pairs:
        offset,_=game.rva_range(slot-game.image_base,4);need(struct.unpack_from('<I',game.data,offset)[0]==entry,'Every complete schedule entry is physical startup table value')
    for field,values in [('entries',[e for s,e in pairs]),('table_slots',[s for s,e in pairs]),('page_bases',array(prefix_spec,'page_bases')),('page_permissions',array(prefix_spec,'page_permissions'))]:spec=replace_array(spec,field,values)
    old_code=re.search(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',spec)[0]
    new_code=re.search(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',prefix_spec)[0];spec=one(spec,old_code,new_code)
    spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"','pack_sha[]="'+prefix['pack_sha256']+'"',spec)
    spec=re.sub(r'pack_size=\d+','pack_size='+str((PREFIX/'pages.bin').stat().st_size),spec)
    allocations=re.search(r'inline constexpr std::array<FsAllocationBinding,8> lockit_allocation_bindings\{\{(.*)\}\};',spec)[1]
    spec=re.sub(r'inline constexpr std::array<FsAllocationBinding,8> lockit_allocation_bindings\{\{[^;]+;','inline constexpr std::array<FsAllocationBinding,11> lockit_allocation_bindings{{'+allocations+',{0x4b7f70,0x4ba306,24},{0x4b7f70,0x4ba33c,24},{0x4b7f70,0x4bab32,24}}};',spec)
    lockit_roots=re.search(r'inline constexpr std::array<LockitRoot,4>lockit_roots\{\{(.*)\}\};',spec)[1]
    spec=re.sub(r'inline constexpr std::array<LockitRoot,4>lockit_roots\{\{[^;]+;','inline constexpr std::array<LockitRoot,5>lockit_roots{{'+lockit_roots+',{0x4b7f70,0x60b2f8,0x60b314,0x60b318,24}}};',spec)
    ref=text(OLD/'reference.cpp');prefref=text(PREFIX/'reference.cpp')
    start=ref.index('extern "C" extern "C" extern "C" void fs_hook_');end=ref.index('struct FsAllocation {',start)
    prestart=prefref.index('extern "C" void fs_hook_');preend=prefref.index('struct FsAllocation {',prestart)
    ref=ref[:start]+prefref[prestart:preend]+ref[end:]
    for a,b in [('FsEvent fs_events[64]','FsEvent fs_events[256]'),('fs_event_count>=64','fs_event_count>=256'),('lockit_snapshots[6]','lockit_snapshots[128]'),('lockit_count>=6','lockit_count>=128'),('lockit_allocations[8]','lockit_allocations[64]'),('lockit_allocation_count>=8','lockit_allocation_count>=64'),('RegistryAPIEntry registry_API_ledger[32]','RegistryAPIEntry registry_API_ledger[256]'),('registry_initial_sizes[32]','registry_initial_sizes[256]'),('registry_initial_bytes[32][1024]','registry_initial_bytes[256][1024]'),('i>=32','i>=256'),('registry_API_count<=32','registry_API_count<=256')]:ref=ref.replace(a,b)
    ref=re.sub(r'std::array<void\*,118> pages','std::array<void*,'+str(len(array(prefix_spec,'page_bases')))+'> pages',ref)
    ref=one(ref,'r->tag.status=execute();','if(entries[phase]==0x4b7f70)require(*reinterpret_cast<unsigned*>(0x60b314)==0&&*reinterpret_cast<unsigned*>(0x60b318)==0,"Actual untouched tree header/counter BEFORE in complete sequence");r->tag.status=execute();')
    ref=one(ref,'require(*crtnext-*crtbegin==96*4,"Exact96callback vectorextent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),96*4);','require(*crtnext-*crtbegin==97*4,"Exact97callback vector extent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),97*4);')
    ref=one(ref,'require(lockit_allocation_count==8,"Eight genuine four-root Lockit owners");','require(lockit_allocation_count>0&&lockit_allocation_count<64,"Bounded actual complete Lockit/tree owners");out.append("cleanup/"+std::to_string(sequence)+"/lockit-owner-count.bin",&lockit_allocation_count,4);')
    ref=ref.replace('Original124','Original125').replace('Connected original124','Connected original125').replace('MW4J124D','MW4J125D').replace('MW4J124O','MW4J125O').replace('6 connected sequences /744 actual original initializer phases captured','6 connected sequences /750 actual original initializer phases captured')
    protocol=text(OLD/'protocol.hpp');protocol=one(protocol,'sequences=6, roots=124','sequences=6, roots=125')
    out.mkdir(parents=True)
    (out/'reference.cpp').write_text(ref);(out/'spec.hpp').write_text(spec);(out/'protocol.hpp').write_text(protocol)
    for filename in ('pages.bin','original_broker.hpp','fs_observer_x86.asm','fs-hook-bindings.json'):(out/filename).write_bytes(pin(PREFIX/filename).read_bytes())
    for filename in ('reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','CMakeLists.txt'):(out/filename).write_bytes(pin(OLD/filename).read_bytes())
    selected=[dict(phase=i,slot=s,entry=e) for i,(s,e) in enumerate(pairs)];(out/'selected-order.json').write_text(json.dumps(selected,indent=2)+'\n')
    pin(__file__)
    for p in out.iterdir():pin(p)
    report={**prefix,'scope':'Full genuine original125 startup relative-order extension of accepted124. Authentic DLL loader/bootstrap and persistent source state; source tree code/interfaces only, no AFTER/per-phase effects or count seed. Broad execution and independent review remain pending.','parent_preparation_sha256':sha(OLD/'report.json'),'normal_prefix_validation_sha256':sha(BASE/'prefix-validation-r2/report.json'),'instruction_observation_sha256':sha(BASE/'trace-validation-r2/report.json'),'original_sequences':6,'original_roots':125,'original_phases':750,'callback_count':97,'added_root_phase':next(r['phase'] for r in selected if r['entry']==0x4b7f70),'selected_order':selected,'code_dispatch_points':len(prefix['source_spans']),'source_spans':prefix['source_spans'],'original_execution_pending':True,'predicted_counts_supplied_to_execution':False,'debugger_instruction_trace_enabled':False,'files':pins}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),tree_phase=report['added_root_phase'])))
if __name__=='__main__':main(sys.argv[1])
