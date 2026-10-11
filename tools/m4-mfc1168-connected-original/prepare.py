"""Prepare one authentic current130 prefix followed by ordinal1168. No execution."""
from pathlib import Path
import hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-connected-original'
OLD=R/'reports/m4-startup130-original/preparation-r2';MFC=R/'reports/m4-mfc1168-probe/preparation-r10'
sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def one(s,a,b):need(s.count(a)==1,'Exact additive source '+a[:100]);return s.replace(a,b,1)
def main(name):
 out=B/name;need(not out.exists(),'Fresh preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No capture archive');v=sha(p);need(h is None or h==v,'Physical pin '+str(p));pins[str(p)]=v;return p
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 def data(p,h=None):return json.loads(pin(p,h).read_bytes())
 old=data(OLD/'report.json','8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814');mfc=data(MFC/'report.json')
 gap=data(R/'reports/m4-mfc1168-native/connected-gap-r1/report.json','a85f58fa74d6fa47e58e664163a572c108c3d9e661ec0d389878d4bd3cec308f')
 facts=data(gap['facts']);need(old['passed']and mfc['passed']and gap['passed'],'Physical prerequisites')
 selected=[dict(v)for v in old['selected_order'][:13]]+[dict(phase=13,slot=0x5e0040,entry=0x5ae3e4)]
 need([(v['slot'],v['entry'])for v in selected[:13]]==[(v['slot'],v['entry'])for v in facts['preceding_selected']],'Exact selected chronology')
 need(facts['ordinary_original_and_native_root_frame']==0x20001800,'Actual source caller geometry')
 raw=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();count=struct.unpack_from('<I',raw,8)[0];need(len(raw)==12+count*4104,'Current130 exact pack')
 records={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],bytearray(raw[20+i*4104:4116+i*4104]))for i in range(count)}
 game=PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 graphs=data(R/'reports/m4-mfc1168-original/recovery-r2/game-graphs.json');rows={r['pc']:r for g in graphs.values()for r in g['instructions']};need(len(rows)==25,'Exact new game source')
 spans=list(old['source_spans']);known={v['pc']:v for v in spans};new_spans=[]
 for row in rows.values():
  pc=row['pc'];bytes_=bytes.fromhex(row['bytes']);off,_=game.rva_range(pc-game.image_base,len(bytes_));need(game.data[off:off+len(bytes_)]==bytes_,'Physical source bytes')
  if pc in known:need(known[pc]==dict(pc=pc,size=len(bytes_),image_offset=off,origin=0),'Same source binding');continue
  consumed=0
  while consumed<len(bytes_):
   a=pc+consumed;p=a&~4095;o=a&4095;n=min(len(bytes_)-consumed,4096-o)
   if p not in records:records[p]=(1,bytearray(b'\xcc'*4096))
   need(len(records[p][1])==4096,'Sparse source page geometry');records[p][1][o:o+n]=bytes_[consumed:consumed+n];consumed+=n
  v=dict(pc=pc,size=len(bytes_),image_offset=off,origin=0);spans.append(v);new_spans.append(v)
 for v in selected:need(struct.unpack_from('<I',records[v['slot']&~4095][1],v['slot']&4095)[0]==v['entry'],'Actual table slot')
 need(all(len(v[1])==4096 for v in records.values()),'Every source page whole4096B')
 pack=b'MW4J124P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,perm)+bytes_ for p,(perm,bytes_)in records.items());need(len(pack)==12+4104*len(records),'Exact combined pack')
 out.mkdir(parents=True);(out/'pages.bin').write_bytes(pack)
 spec=text(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"','pack_sha[]="'+sha(out/'pages.bin')+'"',spec);spec=re.sub(r'pack_size=\d+','pack_size='+str(len(pack)),spec)
 for field,values in [('entries',[v['entry']for v in selected]),('table_slots',[v['slot']for v in selected]),('page_bases',list(records)),('page_permissions',[v[0]for v in records.values()])]:spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(v[k])for k in('pc','size','image_offset','origin'))+'}'for v in spans)+'}};',spec)
 (out/'spec.hpp').write_text(spec)
 protocol=one(text(OLD/'protocol.hpp'),'sequences=6, roots=130','sequences=1, roots=14');(out/'protocol.hpp').write_text(protocol)
 # All current130 globals/observer bodies are preserved, but inactive unrelated
 # source-code hooks are not installed into the new reached MFC/CRT interval.
 original=text(OLD/'reference.cpp');ref=original[:original.index('int main(')]
 ref+='#include "connected_observer.hpp"\n'
 start=original[original.index('int main('):original.index('    for(const auto&hook:fs_hooks){auto*code=',original.index('int main('))]
 start=re.sub(r'std::array<void\*,132> pages',f'std::array<void*,{len(records)}> pages',start)
 start=one(start,'    if(auto broker=mw34::original_broker::dispatch','    require(!debugger,"Normal chronological writer only; no trace admission");\n    if(auto broker=mw34::original_broker::dispatch')
 ref+=start+text(R/'tools/m4-mfc1168-connected-original/main_tail.inc')
 (out/'reference.cpp').write_text(ref)
 worker=text(MFC/'worker.cpp');a=worker.index('Cpu b_cpu');z=worker.index('#include "trace.hpp"');obs='extern "C" {\n'+worker[a:z]
 obs=obs.replace('static std::filesystem::path output_directory;','static mw34::capture_direct::Writer*connected_writer{};').replace('static unsigned api_targets[api_imports.size()]{};','')
 a=obs.index('static void dump(');z=obs.index('static unsigned dword(',a);obs=obs[:a]+'static void dump(const std::string&name,const void*data,std::size_t n){require(connected_writer!=nullptr,"Current chronological writer");connected_writer->append("MFC1168/"+name,data,n);}\n'+obs[z:]
 obs=obs.replace('named_boundaries[16]','named_boundaries[64]').replace('named_count<16','named_count<64')
 obs=obs.replace('b.provider_capacity>=0x1044','b.provider_capacity>=0x1044') # Actual coverage admission, not a predicted numerical result.
 (out/'connected_observer.hpp').write_text('#include <intrin.h>\nextern "C" {unsigned mixed_teb_before_base{},mixed_teb_after_base{};unsigned char mixed_teb_before_pages[8192]{},mixed_teb_after_pages[8192]{};}\n'+obs+text(R/'tools/m4-mfc1168-connected-original/observer_tail.inc'))
 asm=text(OLD/'reference_x86.asm');asm=one(asm,'EXTERN mixed_host_esp:DWORD','EXTERN mixed_host_esp:DWORD\nEXTERN mixed_teb_before_base:DWORD\nEXTERN mixed_teb_after_base:DWORD\nEXTERN mixed_teb_before_pages:BYTE\nEXTERN mixed_teb_after_pages:BYTE\nEXTERN fs_error:DWORD')
 asm=one(asm,' fxsave mixed_host_fx\n',' fxsave mixed_host_fx\n mov esi,DWORD PTR fs:[18h]\n and esi,0fffff000h\n mov mixed_teb_before_base,esi\n mov edi,OFFSET mixed_teb_before_pages\n mov ecx,2048\n cld\n rep movsd\n')
 asm=one(asm,' fnstenv mixed_env_after\n',' fnstenv mixed_env_after\n mov esi,DWORD PTR fs:[18h]\n and esi,0fffff000h\n mov mixed_teb_after_base,esi\n mov edi,OFFSET mixed_teb_after_pages\n mov ecx,2048\n cld\n rep movsd\n')
 asm=one(asm,' mov eax,registry_API_count\n dec eax\n imul eax,eax,104',' mov eax,registry_API_count\n dec eax\n cmp eax,256\n jae api_ledger_overflow\n imul eax,eax,104')
 asm=one(asm,' push DWORD PTR registry_API_after[32]',' jmp api_ledger_restore\napi_ledger_overflow:\n mov fs_error,1\napi_ledger_restore:\n push DWORD PTR registry_API_after[32]')
 asm=one(asm,'.code\nmixed_enter PROC','.code\nASSUME fs:NOTHING\nmixed_enter PROC');(out/'reference_x86.asm').write_text(asm)
 for p in ['preserve_x86.asm','fs_observer_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','format_observer_x86.asm','format_observer.hpp','original_broker.hpp']:(out/p).write_text(text(OLD/p))
 for p in ['boundaries.asm','api_boundaries.asm']:(out/p).write_text(text(MFC/p))
 cmake=text(OLD/'CMakeLists.txt');cmake=one(cmake,' format_observer_x86.asm "${MW34_WRITER_SOURCE}"',' format_observer_x86.asm boundaries.asm api_boundaries.asm "${MW34_WRITER_SOURCE}"');(out/'CMakeLists.txt').write_text(cmake)
 patches=[dict(PC=p,size=n,raw=b,family='MFC1168-game-boundary')for p,n,b in [(0x5ae3a8,5,'e823dbffff'),(0x5ae3ad,8,'8b4c24048b542408'),(0x5ae3b7,9,'884814899040100000'),(0x5ae3c4,6,'ff1574b65b00'),(0x5ae3ca,7,'596a0158c20800')]]
 patches += [dict(PC=0x410a80,size=5,family='capture-broker'),dict(PC=0x5ac3ec,size=5,family='sentinel-terminal')]
 for i,a in enumerate(patches):
  for b in patches[i+1:]:need(a['PC']+a['size']<=b['PC']or b['PC']+b['size']<=a['PC'],'Whole active code patches disjoint')
 for p in patches[:5]:
  off,_=game.rva_range(p['PC']-game.image_base,p['size']);need(game.data[off:off+p['size']].hex()==p['raw'],'Physical observer replay')
 contracts=dict(selected_order=selected,source_frame=0x20001800,bootstrap_frame=0x20001800,unaccepted_omitted_slots=[0x5e0038,0x5e003c],caller_domain=dict(repeat=0,CW=0x007f,TOP=0),fixed_current_source_pages=old['observed_pages'],external_source_pages=old['extra_whole_source_pages'],active_code_patches=patches,unrelated_source_hooks_installed=False,bootstrap_API_ledger_retained=True,generic_CRT_IAT_restored_before_MFC=True,MFC_provider_discovery_precall=False,source_AFTER_seed=False,borrowed_graph_initial_from_current_prefix=True,borrowed_graph_capacity_method='Actual GlobalSize/LocalSize; unresolved actual backing page retained explicitly',coherent_TEB_raw8192_before_and_after_root=True,named_IAT_cells=[0x5f498330,0x7802e044,0x7802e0c8,0x7802e048],named_API_return_slot_scope='Actual entry saved before shim temporarily replaces stack return word; API return CPU PC is source saved continuation; external code is untraced',FS_frame_scope='Raw genuine TEB endpoints and full live source stack; no per-instruction FS observer installed. Literal internal FS source comparison remains subsequent work.',lock25_pointer_cell=0x7803708c,lock25_CS24_current=True,whole_CRT_pages=[0x78000000,0x78040000],whole_MFC_pages=[0x5f400000,0x5f4d0000],codepage_carried_page_policy='78037000 is already mapped by native19; merge only measured fields compatible with current carried page after source comparison',callback_cleanup_scope='Actual CRT vector full backing retained; freed through authentic CRT free after restoration; no borrowed manager/TLS/object released and no source callback credit')
 (out/'contracts.json').write_text(json.dumps(contracts,indent=2)+'\n')
 for p in [Path(__file__),R/'tools/analysis/pe.py',R/'tools/m4-capture-direct/capture_direct_v3.hpp',R/'tools/m4-capture-direct/capture_direct_v3.cpp',R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',R/'local/mw3-staged/Shared_DLLs/MFC42.DLL']:pin(p)
 for p in out.iterdir():pin(p)
 result=dict(passed=True,scope='Preparation-only genuine chronological13 accepted roots then new MFC1168; same current130 loader/producer/caller domain and complete current physical source state',parent_original130_preparation_sha256=sha(OLD/'report.json'),isolated_MFC_preparation_sha256=sha(MFC/'report.json'),connected_gap_sha256=sha(R/'reports/m4-mfc1168-native/connected-gap-r1/report.json'),original_sequences=1,original_roots=14,original_phases=14,record_bytes=356992,source_frame=0x20001800,ordinary_pages=43,combined_current_source_pages=46,sparse_pack_pages=len(records),pack_bytes=len(pack),pack_sha256=sha(out/'pages.bin'),selected_order=selected,source_spans=spans,new_game_source_rows=len(new_spans),active_source_code_hooks=len(patches),true_MFC_boundary_bytes=664,true_named_API_boundary_bytes=668,named_API_boundary_bound=64,original_executed=False,capture_reader_opened=False,preinvoked_provider=False,source_after_seed=False,predicted_values_supplied_to_observations=False,initializer_credit=0,contracts=str(out/'contracts.json'),files=pins)
 q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,preparation=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
