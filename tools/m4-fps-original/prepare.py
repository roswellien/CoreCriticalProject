"""Append genuine fps40F000 and exact cdecl vsprintf observation to font6."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-fps-original';OLD=R/'reports/m4-font479590-original/preparation-r1';T=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def one(s,a,b):need(s.count(a)==1,'Exact derivative '+a[:85]);return s.replace(a,b,1)
def bridge(name,side):
 lines=[f'PUBLIC {name}',f'{name} PROC']
 for i,reg in enumerate(('eax','ecx','edx','ebx','esp','ebp','esi','edi')):lines.append(f' mov DWORD PTR fps_cpu[{4*i}],{reg}')
 lines+=[' mov DWORD PTR fps_cpu[36],05a2f6eh']if side else[' mov eax,fps_target',' mov DWORD PTR fps_cpu[36],eax']
 lines += [f' mov fps_kind,{side}',' mov esp,mixed_host_esp',' pushfd',' pop DWORD PTR fps_cpu[32]',' cld',' mov eax,DWORD PTR fs:[0]',' mov fps_head,eax',' mov ax,ds',' mov fps_ds,ax',' mov ax,es',' mov fps_es,ax',' mov ax,ss',' mov fps_ss,ax',' fxsave fps_fx',' fnstenv fps_env',' fldenv fps_env',' call fps_observe',' fxrstor fps_fx',' fldenv fps_env',' push DWORD PTR fps_cpu[32]',' popfd']
 for i,reg in enumerate(('eax','ecx','edx','ebx','esp','ebp','esi','edi')):
  if reg!='esp':lines.append(f' mov {reg},DWORD PTR fps_cpu[{4*i}]')
 lines+=[' mov esp,DWORD PTR fps_cpu[16]']
 lines+=[' db 08bh,086h,038h,002h,000h,000h',' jmp DWORD PTR fps_continue']if side else[' jmp DWORD PTR fps_target']
 return '\n'.join(lines+[f'{name} ENDP'])+'\n'
def main(name):
 out=B/name;need(not out.exists(),'Fresh preparation');out.mkdir(parents=True);pins={};passed=False;commands=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(p.suffix!='.mwb','No capture archive');need(h is None or h==v,'Exact physical input '+str(p));pins[str(p)]=v;return p
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  old=read(OLD/'report.json','56dab048c049f8cf634c494ed894a8444bba8c50da0d4dc99c7a22cfeab50ab9');need(old['passed']and old['original_roots']==6,'Frozen genuine font6 worker')
  actual=read(R/'reports/m4-font479590-original/validation-r1/report.json','3b5e6b93cd4f6600c765666d9489bf28e821aa5269ec7c522e849a75a0e972a9');need(actual['passed']and actual['all_reader_aliases_closed'],'Measured font6 inputs')
  for p,h in old['files'].items():pin(p,h)
  remaining=R/'reports/m4-remaining-service-source/preparation-r2';read(remaining/'report.json','e137cf7e923009c39de1ba3b6135e0e8ca5b43826f0ec993396f77bd82acc2c4')
  graphs=read(remaining/'all-seven-graphs.json');frontier=read(R/'reports/m4-joint-startup116-root/next-frontier-r1/remaining-roots.json','d2faf2654877f203cef768634038254a7072bcdcdc4948bda3e9e93988ea3152');selected=next(x for x in frontier if x['entry']==0x40f000)
  game=PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());crt=PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
  exp=next(v for v in crt.exports()if 'vsprintf'in v['names']);need(crt.image_base+exp['rva']==0x780230dd and exp['ordinal']==733,'Physical named CRTvsprintf export')
  off,_=game.rva_range(0x5e1590-game.image_base,4);need(game.data[off:off+4]==b'fps\0','Exact physical format literal')
  off,_=game.rva_range(0x5cfd48-game.image_base,4);need(struct.unpack_from('<I',game.data,off)[0]==0x409b30,'Exact new reached-candidate virtual slot')
  recovery=load(R/'tools/m4-onexit-batch-recovery/recover.py','fps_physical_decoder');module=recovery.Module(pin(R/'MW3/Mech3.exe'))
  for g in graphs.values():recovery.ingest(module,g['instructions'])
  newtarget,deferred=recovery.closure(module,[0x409b30],out,commands,maximum=10);need(not deferred,'Focused physical virtual target closure');need(0x409b30 in newtarget,'New exact callback source')
  fontgraphs={str(e):graphs[str(e)]for e in selected['local_entries']if str(e)in graphs};fontgraphs.update({str(e):g for e,g in newtarget.items()});rows={r['pc']:r for g in fontgraphs.values()for r in g['instructions']}
  # All immutable code includes dormant source alternatives; their reach and
  # service domains are still unadmitted until genuine normal observations.
  pack=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();n=struct.unpack_from('<I',pack,8)[0];need(len(pack)==12+n*4104,'Whole current sparse pack')
  records={struct.unpack_from('<I',pack,12+i*4104)[0]:(struct.unpack_from('<I',pack,16+i*4104)[0],bytearray(pack[20+i*4104:4116+i*4104]))for i in range(n)};spans=copy.deepcopy(old['source_spans']);known={v['pc']:v for v in spans};newspans=[];overlay=[]
  for row in rows.values():
   pc=row['pc'];b=bytes.fromhex(row['bytes']);off,_=game.rva_range(pc-game.image_base,len(b));need(game.data[off:off+len(b)]==b,'Whole physical new source row')
   if pc in known:need(known[pc]==dict(pc=pc,size=len(b),image_offset=off,origin=0),'Identical overlapping source row');continue
   for j,value in enumerate(b):
    page=(pc+j)&~4095;o=(pc+j)&4095
    if page not in records:records[page]=(1,bytearray(b'\xcc'*4096))
    need(records[page][0]==1 and len(records[page][1])==4096,'Whole RX sparse source page');oldbyte=records[page][1][o];need(oldbyte in(0xcc,value),'Physical source overlays padding only')
    if oldbyte!=value:overlay.append(dict(address=pc+j,old=oldbyte,new=value,source_PC=pc))
    records[page][1][o]=value
   v=dict(pc=pc,size=len(b),image_offset=off,origin=0);spans.append(v);newspans.append(v);known[pc]=v
  need(struct.unpack_from('<I',records[0x5e0000][1],0x50)[0]==0x40f000,'Actual original selected table entry')
  for p in OLD.iterdir():
   if p.is_file()and p.name not in('report.json','pins.json'):(out/p.name).write_bytes(pin(p).read_bytes())
  fresh=b'MW4J124P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,perm)+b for p,(perm,b)in records.items());need(len(fresh)==12+len(records)*4104 and all(len(b)==4096 for _,b in records.values()),'Exact pack geometry');(out/'pages.bin').write_bytes(fresh)
  spec=text(OLD/'spec.hpp');spec=one(spec,old['pack_sha256'],sha(out/'pages.bin'));spec=re.sub(r'pack_size=\d+','pack_size='+str(len(fresh)),spec)
  for field,values in(('entries',None),('table_slots',None),('page_bases',list(records)),('page_permissions',[v[0]for v in records.values()])):
   m=re.search(r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{([^}]+)\};',spec);need(m is not None,'Exact source array '+field)
   values=[int(x,16)for x in m[1].split(',')]+[0x40f000 if field=='entries'else 0x5e0050]if values is None else values
   spec=one(spec,m[0],f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};')
  m=re.search(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',spec);spec=one(spec,m[0],f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings'+'{{'+','.join('{'+','.join(hex(v[k])for k in('pc','size','image_offset','origin'))+'}'for v in spans)+'}};');(out/'spec.hpp').write_text(spec)
  protocol=one(text(OLD/'protocol.hpp'),'sequences=1, roots=6','sequences=1, roots=7');(out/'protocol.hpp').write_text(protocol)
  ref=one(text(OLD/'reference.cpp'),'#include "widget_observer.hpp"','#include "widget_observer.hpp"\n#include "fps_observer.hpp"');ref=re.sub(r'std::array<void\*,159> pages',f'std::array<void*,{len(records)}> pages',ref)
  # Add true FS observers only at newly introduced whole source opcodes.
  fs=read(OLD/'fs-hook-bindings.json');fsnew=[];used={b['PC']for b in fs}
  for row in rows.values():
   if 'fs:'not in row['operands']or row['pc']in used:continue
   b=row['bytes'];need(b in('64a100000000','64892500000000','64890d00000000'),'Exact supported source FS opcode');fsnew.append(dict(PC=row['pc'],kind={'64a100000000':0,'64892500000000':1,'64890d00000000':2}[b],raw_bytes=b,continuation=row['pc']+row['size'],declared_observer=f'fs_hook_{row["pc"]:x}'))
  declarations='\n'.join(f'extern "C" void {b["declared_observer"]}();\nextern "C" const unsigned fs_continue_{b["PC"]:x}=0x{b["continuation"]:x};'for b in fsnew)+'\n';ref=one(ref,'struct FsHook',declarations+'struct FsHook')
  m=re.search(r'const std::array<FsHook,(\d+)>\s*fs_hooks\{\{(.*?)\}\};',ref,re.S);add=''.join(',{0x'+format(b['PC'],'x')+','+str(len(bytes.fromhex(b['raw_bytes'])))+','+str(b['kind'])+',&'+b['declared_observer']+',{'+','.join('0x'+format(v,'x')for v in bytes.fromhex(b['raw_bytes']))+'}}'for b in fsnew);ref=ref[:m.start()]+f'const std::array<FsHook,{len(fs)+len(fsnew)}>fs_hooks'+'{{'+m[2]+add+'}};'+ref[m.end():]
  ref=one(ref,'    auto*crtbegin=', '    fps_target=reinterpret_cast<unsigned>(GetProcAddress(crt,"vsprintf"));require(fps_target==0x780230dd,"Exact actual named stagedvsprintf");*reinterpret_cast<unsigned*>(0x5bb53c)=fps_target;\n    auto*crtbegin=')
  install='''    {DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(0x5bb53c),4,PAGE_READWRITE,&prior),"FPS owning IAT protection");require(*reinterpret_cast<unsigned*>(0x5bb53c)==fps_target,"Actual vsprintf before observation");*reinterpret_cast<unsigned*>(0x5bb53c)=reinterpret_cast<unsigned>(&fps_entry);require(VirtualProtect(reinterpret_cast<void*>(0x5bb53c),4,prior,&ignored),"FPS IAT permissions");}
    {const unsigned char raw[6]{0x8b,0x86,0x38,0x02,0,0};require(!std::memcmp(reinterpret_cast<void*>(0x5a2f6e),raw,6),"Exact fullFPSreturn source span");DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(0x5a2f6e),6,PAGE_EXECUTE_READWRITE,&prior),"FPS return observer protection");auto*p=reinterpret_cast<unsigned char*>(0x5a2f6e);p[0]=0xe9;const unsigned d=reinterpret_cast<unsigned>(&fps_return)-0x5a2f73;std::memcpy(p+1,&d,4);p[5]=0x90;require(VirtualProtect(p,6,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),p,6),"FPSreturn observer permissions");}
'''
  ref=one(ref,'    owner=GetCurrentThreadId();',install+'    owner=GetCurrentThreadId();')
  ref=one(ref,'    out.append("widget/identity.bin",', '    const std::array<unsigned,4> fps_identity{0x5bb53c,fps_target,reinterpret_cast<unsigned>(&fps_entry),0x78000000};out.append("fps/identity.bin",fps_identity.data(),sizeof(fps_identity));\n    out.append("widget/identity.bin",')
  ref=one(ref,'            widget_count=0;widget_error=0;', '            fps_count=0;fps_error=0;std::memset(fps_snapshots,0,sizeof(fps_snapshots));\n            widget_count=0;widget_error=0;')
  exports='''            const auto fstem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/fps";require(!fps_error&&fps_count<=8,"Bounded authentic FPS observations before export");out.append(fstem+"-count.bin",&fps_count,4);out.append(fstem+"-snapshots.bin",fps_snapshots,fps_count*sizeof(FpsSnapshot));out.append(fstem+"-segments.bin",fps_segments,fps_count*sizeof(WidgetSegments));
'''
  ref=one(ref,'            const auto wstem=',exports+'            const auto wstem=')
  proof='''if(0x5a2f6e<=span.pc&&span.pc+span.size<=0x5a2f74){const unsigned off=span.pc-0x5a2f6e;const unsigned char raw[6]{0x8b,0x86,0x38,0x02,0,0};require(!std::memcmp(origin.data()+span.image_offset,raw+off,span.size),"ExactFPSreturn physical row");const unsigned d=reinterpret_cast<unsigned>(&fps_return)-0x5a2f73;for(unsigned i=0;i<span.size;++i){const unsigned n=off+i;const unsigned char expected=n==0?0xe9:n<5?static_cast<unsigned char>(d>>(8*(n-1))):0x90;require(*reinterpret_cast<unsigned char*>(span.pc+i)==expected,"ExactFPSreturn observer byte");}hooked=true;}'''
  ref=one(ref,'if(!hooked)require(',proof+'if(!hooked)require(')
  restore='''    {DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(0x5bb53c),4,PAGE_READWRITE,&prior),"FPS owning IAT restoration");require(*reinterpret_cast<unsigned*>(0x5bb53c)==reinterpret_cast<unsigned>(&fps_entry),"ExactFPSentry before restoration");*reinterpret_cast<unsigned*>(0x5bb53c)=fps_target;require(VirtualProtect(reinterpret_cast<void*>(0x5bb53c),4,prior,&ignored),"FPS named import restored");}
    {const unsigned char raw[6]{0x8b,0x86,0x38,0x02,0,0};DWORD prior{},ignored{};require(VirtualProtect(reinterpret_cast<void*>(0x5a2f6e),6,PAGE_EXECUTE_READWRITE,&prior),"FPSreturn restoration");std::memcpy(reinterpret_cast<void*>(0x5a2f6e),raw,6);require(VirtualProtect(reinterpret_cast<void*>(0x5a2f6e),6,prior,&ignored)&&FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(0x5a2f6e),6),"ExactFPSreturn source restored");}
'''
  ref=one(ref,'    for(unsigned i=0;i<pages.size();++i)if(page_permissions[i]!=2){',restore+'    for(unsigned i=0;i<pages.size();++i)if(page_permissions[i]!=2){')
  ref=one(ref,'            bool gdi_byte=false;', '            if(0x5bb53c<=pc&&pc<0x5bb540){require(actual[byte]==reinterpret_cast<const unsigned char*>(&fps_target)[pc-0x5bb53c],"Exact named vsprintf IAT after restoration");continue;}\n            bool gdi_byte=false;')
  ref=one(ref,'Six genuine widget/font initializer endpoints captured','Seven genuine widget/font/fps initializer endpoints captured');(out/'reference.cpp').write_text(ref)
  fsasm=text(OLD/'fs_observer_x86.asm');template=re.search(r'PUBLIC fs_hook_4e78d7\nfs_hook_4e78d7 PROC\n.*?fs_hook_4e78d7 ENDP\n',fsasm,re.S)[0];generated=[]
  for b in fsnew:generated.append(template.replace('4e78d7',format(b['PC'],'x')).replace(' mov fs_event_kind,0',f' mov fs_event_kind,{b["kind"]}').replace(' db 064h,0a1h,000h,000h,000h,000h',' db '+','.join('0'+format(v,'02x')+'h'for v in bytes.fromhex(b['raw_bytes']))))
  fsasm=one(fsasm,'.code\n','\n'.join(f'EXTERN fs_continue_{b["PC"]:x}:DWORD'for b in fsnew)+'\n.code\n');fsasm=one(fsasm,'END\n',''.join(generated)+'END\n');(out/'fs_observer_x86.asm').write_text(fsasm);(out/'fs-hook-bindings.json').write_text(json.dumps(fs+fsnew,indent=2)+'\n')
  (out/'fps_observer.hpp').write_text(text(T/'fps_observer.hpp'))
  assembly='.686p\n.xmm\n.model flat,C\nassume fs:nothing\noption casemap:none\n'+'\n'.join('EXTERN '+n+':'+t for n,t in [('mixed_host_esp','DWORD'),('fps_head','DWORD'),('fps_ds','WORD'),('fps_es','WORD'),('fps_ss','WORD'),('fps_cpu','BYTE'),('fps_fx','BYTE'),('fps_env','BYTE'),('fps_kind','DWORD'),('fps_target','DWORD'),('fps_continue','DWORD'),('fps_observe','PROC')])+'\n.code\n'+bridge('fps_entry',0)+bridge('fps_return',1)+'END\n';(out/'fps_observer_x86.asm').write_text(assembly)
  cmake=one(text(OLD/'CMakeLists.txt'),'widget_observer_x86.asm "','widget_observer_x86.asm fps_observer_x86.asm "');(out/'CMakeLists.txt').write_text(cmake)
  contract=read(OLD/'normal-contracts.json');knownrows={v['pc']for v in contract['instructions']};parser=load(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py','fps_operand_contracts')
  for row in rows.values():
   if row['pc']in knownrows:continue
   x=dict(pc=row['pc'],width=row['size'],bytes_hex=row['bytes'],mnemonic=row['mnemonic'],operands=row['operands'].split(' <')[0]);contract['instructions'].append(parser.instruction_contract(x))
  registration=next(v for v in read(remaining/'registration-roots.json')if v['entry']==0x40f000);contract['roots'].append(dict(root=0x40f000,slot=0x5e0050,callback=registration['callback'],push_PC=0x40f020,CALL_pc=0x40f025,return_PC=0x40f02a,callback_executed=False))
  contract['normal_patch_spans'] += [dict(family='FS',PC=b['PC'],size=len(bytes.fromhex(b['raw_bytes'])),raw=b['raw_bytes'])for b in fsnew]+[dict(family='FPS-return',PC=0x5a2f6e,size=6,raw='8b8638020000')]
  for i,a in enumerate(contract['normal_patch_spans']):
   for b in contract['normal_patch_spans'][i+1:]:need(a['PC']+a['size']<=b['PC']or b['PC']+b['size']<=a['PC'],'Every active source patch family disjoint')
  contract.update(fps=dict(root=0x40f000,slot=0x5e0050,object=0x5fc378,extent=0x4bc,format=0x5e1590,format_physical_hex='66707300',IAT=0x5bb53c,named_export='vsprintf',physical_target=0x780230dd,CALL_pc=0x5a2f68,return_PC=0x5a2f6e,argc=3,caller_cleanup=12,actual_true_cdecl_entry_and_return_frames_prepared=True,snapshot_bytes=529700,bound=8,output_observed_only=True,source_output_seed=False,new_virtual=dict(CALL_pc=0x5a2f86,source_vptr=0x5cfd28,source_vptr_store_PC=0x5a0114,slot=0x5cfd48,target=0x409b30,measured=False)),sequence_scope='Prior measured relative widget5/font479590 order then40F000; full original startup order remains unclaimed',real_fps_formatter40F000_admitted=False,normal_counts_are_unmeasured=True)
  (out/'normal-contracts.json').write_text(json.dumps(contract,indent=2)+'\n');(out/'new-game-graphs.json').write_text(json.dumps(fontgraphs,indent=2)+'\n');(out/'new-source-overlay.json').write_text(json.dumps(overlay,indent=2)+'\n')
  broker=text(OLD/'original_broker.hpp');m=re.search(r'inline constexpr std::array<std::uint32_t,(\d+)> bases\{([^}]+)\};',broker);reserved=[int(v,16)for v in m[2].split(',')];need(all(p&~65535 in reserved for p in records),'All code/data sparse pages pre-reserved')
  pin(__file__);pin(R/'tools/m4-capture-direct/capture_direct_v3.cpp');pin(R/'tools/m4-capture-direct/capture_direct_v3.hpp')
  for p in out.iterdir():pin(p)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report={k:copy.deepcopy(v)for k,v in old.items()if k!='files'}if'old'in locals()else{}
  report.update(passed=passed,scope='Authentic seven-root normal fps observer preparation only; actual provider/source closure pending',parent_preparation_sha256=sha(OLD/'report.json'),original_roots=7,original_phases=7,source_spans=spans if'spans'in locals()else [],new_source_rows=len(newspans)if'newspans'in locals()else 0,new_source_bytes=sum(v['size']for v in newspans)if'newspans'in locals()else 0,game_rows=len(contract['instructions'])if'contract'in locals()else 0,game_instruction_bytes=sum(v['width']for v in contract['instructions'])if'contract'in locals()else 0,sparse_pack_pages=len(records)if'records'in locals()else 0,FS_hooks=len(fs)+len(fsnew)if'fs'in locals()else 0,fps_snapshot_bytes=529700,fps_observations_bound=8,pack_sha256=sha(out/'pages.bin')if(out/'pages.bin').exists()else None,commands=commands,original_executed=False,trace_executed=False,trace_admitted=False,source_after_seed=False,provider_preinvoked=False,predicted_counts_supplied_to_execution=False,initializer_credit=0,files=pins)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
