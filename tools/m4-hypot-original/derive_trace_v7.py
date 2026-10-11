"""Remove NULL-free stutters and validate all original opcodes before patching."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-hypot-original'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'trace-preparation-r6';out=B/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 old=json.loads(pin(parent/'report.json','4328b1b5a0672c829cc6e5a4e8a2f6ccc2dae9ced3924085ea9598307e9ad56f').read_bytes())
 for p,h in old['files'].items():pin(p,h)
 pin(B/'trace-execution-r1/report.json','ccd8d6f7e00d12113384b4b6fd17d32b568ced390109e7c01be57ebcbcc451a0');pin(B/'trace-execution-r1/run/stage.json');pin(B/'trace-execution-r1/run/stderr.bin');out.mkdir()
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(pin(p).read_bytes())
 ref=(out/'reference.cpp').read_text();source='const std::array<NullHook,2> null_hooks{{{0x78001390,&nullfree_entry_hook,{0x55,0x8b,0xec,0x6a,0xff}},{0x78001420,&nullfree_ret_hook,{0x5f,0x5e,0x5b,0xc9,0xc3}}}};';assert ref.count(source)==1;ref=ref.replace(source,'const std::array<NullHook,0> null_hooks{};');(out/'reference.cpp').write_text(ref)
 kernel=(out/'hypot_trace.hpp').read_text();source='for(unsigned i=0;i<hypot_trace_points.size();++i){const auto&p=hypot_trace_points[i];auto*b=reinterpret_cast<unsigned char*>(p.pc);require(*b==p.opcode,"Exact physical source first opcode before trace");hypot_trace_original[i]=*b;DWORD old{},ignored{};'
 target='for(unsigned i=0;i<hypot_trace_points.size();++i){const auto&p=hypot_trace_points[i];const auto actual=*reinterpret_cast<unsigned char*>(p.pc);require(actual==p.opcode,"Exact physical source first opcode before trace PC="+std::to_string(p.pc)+" expected="+std::to_string(p.opcode)+" actual="+std::to_string(actual));hypot_trace_original[i]=actual;}\n for(unsigned i=0;i<hypot_trace_points.size();++i){const auto&p=hypot_trace_points[i];auto*b=reinterpret_cast<unsigned char*>(p.pc);DWORD old{},ignored{};'
 assert kernel.count(source)==1;kernel=kernel.replace(source,target);(out/'hypot_trace.hpp').write_text(kernel)
 descriptors=json.loads((out/'trace-instruction-contracts.json').read_bytes())['instructions'];families=[];hooks=[]
 for kind,label in [('FsHook','fs_hooks'),('NullHook','null_hooks'),('VtableHook','vtable_hooks'),('LockitHook','lockit_hooks')]:
  block=re.search(r'const std::array<'+kind+r',(\d+)>\s*'+label+r'(\{.*?\});',ref);assert block,kind;count=int(block[1]);entries=[]
  if kind=='NullHook':assert count==0
  else:
   for match in re.finditer(r'\{(0x[0-9a-f]+),(\d+),(?:\d+,)?&([a-z0-9_]+),\{([^{}]*)\}\}',block[2]):
    pc=int(match[1],16);size=int(match[2]);raw=bytes(int(x,0)for x in match[4].split(','));assert len(raw)>=size;entries.append(dict(family=kind,PC=pc,size=size,declared_observer=match[3],raw_hex=raw[:size].hex()))
   assert len(entries)==count,(kind,count,len(entries))
  families.append(dict(family=kind,active_count=count));hooks.extend(entries)
 overlaps=[dict(hook=h,descriptor_PC=d['pc'],descriptor_width=d['width'])for h in hooks for d in descriptors if h['PC']<d['pc']+d['width']and d['pc']<h['PC']+h['size']];assert not overlaps
 assert ref.count('for(const auto&hook:hypot_hooks)')==0 and ref.count('reinterpret_cast<unsigned>(&hypot_entry)')==0
 audit=dict(active_families=families,complete_active_code_spans=hooks,source_descriptors=len(descriptors),source_bytes_unchanged=True,intersection_rule='Full half-open byte ranges of source instructions and active authored code patches',overlaps=overlaps,normal_hypot_observers_installed=False,removed_NULL_free_PC_spans=[dict(PC=0x78001390,size=5),dict(PC=0x78001420,size=5)],all_source_validation_precedes_any_breakpoint=True)
 (out/'active-hook-overlap-audit.json').write_text(json.dumps(audit,indent=2)+'\n');pin(__file__);pin(sys.executable)
 for p in out.iterdir():pin(p)
 report={**old,'scope':old['scope']+'; all active FS/NULL-free/vtable/Lockit source byte ranges disjoint; complete first-opcode validation precedes any breakpoint installation','previous_trace_preparation_sha256':sha(parent/'report.json'),'removed_active_NULL_free_hooks':2,'active_NULL_free_hooks':0,'active_code_hooks_total':len(hooks),'all_hook_family_overlap_count':0,'first_opcode_failure_reports_actual_PC_expected_actual':True,'complete_first_opcode_validation_before_patching':True,'files':pins};p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');pin(p);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),active_code_hooks=len(hooks))))
if __name__=='__main__':main(sys.argv[1])
