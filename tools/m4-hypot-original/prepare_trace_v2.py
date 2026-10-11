"""Prepare separate genuine game/CRT single-instruction observations."""
from pathlib import Path
import hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];BASE=R/'reports/m4-hypot-original';PARENT=BASE/'prefix-preparation-r2';REC=BASE/'recovery-r1'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def one(s,a,b):need(s.count(a)==1,'One exact trace change '+a[:90]);return s.replace(a,b,1)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh separate trace preparation');files={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix not in('.mwb','.zip'),'No inherited capture opened');v=sha(p);need(h is None or h==v,'Exact current physical input '+str(p));files[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 pin(BASE/'prefix-validation-r2/report.json','80a4e558e8fc5d11bc2fb0f6fa9446d881c848690b8fd44c8543beca014ff313')
 parent=json.loads(pin(PARENT/'report.json','e959fc8606b80b88f8eebd9582ffeec87c05d3e1a5304ec722d719d4640f2a47').read_bytes());recovery=json.loads(pin(REC/'report.json','eac482b63a16938e9f931f34baa294e59aa8c216b861528426c24a988079eb77').read_bytes())
 for record in(parent,recovery):
  for p,h in record['files'].items():pin(p,h)
 A=load(R/'tools/m4-service-initializers/recover.py','hypot_trace_physical');D=load(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py','hypot_trace_operand')
 modules={k:A.Module(pin(R/p,A.IDENTITIES[p]))for k,p in [('game','MW3/Mech3.exe'),('CRT','local/mw3-staged/Shared_DLLs/MSVCRT.DLL')]}
 rows={}
 for label,fn in [('game','game-graphs.json'),('CRT','CRT-provider-graphs.json')]:
  for g in json.loads(pin(REC/fn).read_bytes()).values():
   for r in g['instructions']:
    raw=bytes.fromhex(r['bytes']);m=modules[label];off,_=m.image.rva_range(r['pc']-m.base,len(raw));need(m.image.data[off:off+len(raw)]==raw,'Exact whole physical game/CRT instruction');value=dict(r,module=label);need(r['pc']not in rows or rows[r['pc']]==value,'Unique physical instruction boundary');rows[r['pc']]=value
 ordered=sorted(rows.values(),key=lambda v:v['pc']);need(all(a['pc']+a['size']<=b['pc']for a,b in zip(ordered,ordered[1:])),'Disjoint physical instruction boundaries')
 original_operand=D.operand
 def operand(v):
  v=v.strip()
  if v=='st':return dict(kind='x87-register',index=0,bits=80)
  match=re.fullmatch(r'st\((\d)\)',v)
  if match:return dict(kind='x87-register',index=int(match[1]),bits=80)
  if v.startswith('tbyte ptr '):value=original_operand(v.replace('tbyte ptr ','qword ptr ',1));value['bits']=80;return value
  if v in('cs','ds','es','fs','gs','ss'):return dict(kind='segment-register',register=v,bits=16)
  return original_operand(v)
 D.operand=operand;regs=['eax','ecx','edx','ebx','esp','ebp','esi','edi'];descriptors=[];gaps=[]
 for row in ordered:
  op=row['mnemonic'];args=row['operands'].split(' <')[0];repeat=None
  if op in('rep','repe','repz','repne','repnz'):repeat=op;op,args=args.split(None,1)
  n=dict(pc=row['pc'],width=row['size'],bytes_hex=row['bytes'],mnemonic=op,operands=args,module=row['module'])
  if repeat:n['repeat']=repeat
  cells=[];contract=None
  try:
   contract=D.instruction_contract(n)
   if op.startswith('f'):
    memory=[i for i,v in enumerate(contract['decoded_operands'])if v['kind']=='memory'];store=op in('fst','fstp','fist','fistp','fisttp','fnstcw','fstcw','fnstsw','fstsw','fnstenv','fstenv','fnsave','fsave')
    contract['explicit_memory_reads']=[]if store else memory;contract['explicit_memory_writes']=memory if store else [];contract['x87_effects']='Actual stopped CONTEXT; no numerical expected values or source effect injection'
   for i,v in enumerate(contract['decoded_operands']):
    if v['kind']!='memory':continue
    rd=i in contract['explicit_memory_reads'];wr=i in contract['explicit_memory_writes']
    if not(rd or wr):continue
    bits=v['bits'] or next((x['bits']for x in contract['decoded_operands']if x['kind']in('register','segment-register')),32);coef=[0]*8
    for term in v['terms']:coef[regs.index(term['register'])]+=term['scale']
    need(v['segment']in('default','fs','ds','es','ss'),'Explicit flat32 or actual FS base');cells.append(dict(displacement=v['displacement'],coefficients=coef,width=bits//8,read=int(rd),write=int(wr),segment=int(v['segment']=='fs')))
   for v in contract['implicit_memory']:
    coef=[0]*8;kind=v['kind'];wr=kind in('stack-write','string-write')
    if kind.startswith('stack'):coef[5 if v['address']=='SSBASE+EBP'else 4]=1;disp=0xfffffffc if wr else 0
    else:coef[6 if v['address'].endswith('ESI')else 7]=1;disp=0
    cells.append(dict(displacement=disp,coefficients=coef,width=v['bits']//8,read=int(not wr),write=int(wr),segment=0))
   if op in('scasb','scasw','scasd','lodsb','lodsw','lodsd','movsb','movsw'):
    width={'b':1,'w':2,'d':4}[op[-1]];coef=[0]*8;coef[7 if op.startswith('scas')else 6]=1;cells.append(dict(displacement=0,coefficients=coef,width=width,read=1,write=0,segment=0))
    if op.startswith('movs'):coef=[0]*8;coef[7]=1;cells.append(dict(displacement=0,coefficients=coef,width=width,read=0,write=1,segment=0))
   need(len(cells)<=4 and all(0<c['width']<=16 for c in cells),'Complete bounded integer/raw80 operands')
  except Exception as e:cells=[];gaps.append(dict(pc=row['pc'],mnemonic=op,operands=args,reason=str(e)))
  descriptors.append(dict(**n,opcode=int(row['bytes'][:2],16),cells=cells,contract=contract,descriptor_complete=not any(v['pc']==row['pc']for v in gaps)))
 out.mkdir(parents=True)
 for p in PARENT.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(pin(p).read_bytes())
 (out/'trace-instruction-contracts.json').write_text(json.dumps(dict(instructions=descriptors,descriptor_gaps=gaps),indent=2)+'\n')
 cell=lambda c:'{'+','.join([hex(c['displacement']),'{'+','.join(map(str,c['coefficients']))+'}',str(c['width']),str(c['read']),str(c['write']),str(c['segment'])])+'}'
 header='#pragma once\nstruct HypotTraceMemory{unsigned displacement,coefficients[8],width,read,write,segment;};\nstruct HypotTracePoint{unsigned pc,width,opcode,count;HypotTraceMemory cells[4];};\ninline constexpr std::array<HypotTracePoint,'+str(len(descriptors))+'> hypot_trace_points{{\n'
 for d in descriptors:header+='{'+','.join(map(str,[d['pc'],d['width'],d['opcode'],len(d['cells'])]))+',{'+','.join(cell(c)for c in d['cells'])+'}},\n'
 (out/'trace_points.hpp').write_text(header+'}};\n')
 counts={**D.API_ARGUMENTS,'TlsGetValue':1,'TlsSetValue':2,'TlsAlloc':0,'TlsFree':1,'GetLastError':0,'SetLastError':1,'GetCurrentThreadId':0,'GetVersion':0,'GetVersionExA':1,'GetModuleHandleA':1,'GetProcAddress':2,'DeleteCriticalSection':1,'HeapAlloc':3,'HeapFree':3,'HeapReAlloc':4,'HeapSize':3,'GetCurrentProcess':0,'ExitProcess':1,'_hypot':4}
 imports=[]
 for label,m in modules.items():
  for i,v in m.imports.items():
   if label=='game'and i!=0x5bb5b0:continue
   imports.append(dict(module=label,iat=i,name=v.get('name')or('#'+str(v.get('ordinal'))),argc=counts.get(v.get('name'),0xffffffff),library=v['library']))
 need(any(v['iat']==0x5bb5b0 and v['name']=='_hypot'for v in imports),'Exact game owning named hypot import')
 (out/'api-imports.json').write_text(json.dumps(imports,indent=2)+'\n');api='#pragma once\nstruct HypotTraceImport{unsigned iat,argc;const char*name;};\ninline constexpr std::array<HypotTraceImport,'+str(len(imports))+'> hypot_trace_imports{{\n'+''.join('{'+str(v['iat'])+','+str(v['argc'])+',"'+v['name']+'"},\n'for v in imports)+'}};\n';(out/'api_imports.hpp').write_text(api)
 (out/'hypot_trace.hpp').write_bytes(pin(Path(__file__).parent/'trace_v2.hpp').read_bytes())
 ref=(out/'reference.cpp').read_text();ref=one(ref,'#include "hypot_observer.hpp"','#include "hypot_observer.hpp"\n#include "hypot_trace.hpp"');ref=one(ref,'bool mw34::original_broker::handle_debug_checkpoint(HANDLE child,const DEBUG_EVENT&event){','bool mw34::original_broker::handle_debug_checkpoint(HANDLE child,const DEBUG_EVENT&event){\n if(hypot_trace_debug(child,event))return true;')
 ref=one(ref,'const bool debugger=argc>1&&std::string(argv[argc-1])=="--checkpoint";mw34::original_broker::checkpoint_mode=debugger;','const bool debugger=false;mw34::original_broker::checkpoint_mode=true;')
 ref=re.sub(r'^    \{DWORD prior\{\},ignored\{\};require\(VirtualProtect\(reinterpret_cast<void\*>\(0x5bb5b0\).*?\}\n','',ref,flags=re.M)
 ref=re.sub(r'^    for\(const auto&hook:hypot_hooks\).*?\n','',ref,flags=re.M)
 start='for(const auto&hook:hypot_hooks)if(hook.pc<=span.pc&&span.pc+span.size<=hook.pc+hook.size)';a=ref.index(start);b=ref.index('if(!hooked)require(',a);ref=ref[:a]+ref[b:]
 ref=one(ref,'reinterpret_cast<unsigned>(&hypot_entry),reinterpret_cast<unsigned>(crt)','0,reinterpret_cast<unsigned>(crt)')
 ref=one(ref,'r->tag.status=execute();fs_phase_root=0;','hypot_trace_begin();r->tag.status=execute();hypot_trace_finish();fs_phase_root=0;')
 ref=one(ref,'require(hypot_count==4,"Actual two _hypot entry/first-game-return pairs");','require(hypot_count==0,"Separate source trace has no normal cdecl observer replay");')
 marker='            require(registry_API_count<=32,'
 output='''            const auto tstem="phase/"+std::to_string(sequence)+"/"+std::to_string(phase)+"/hypot-trace/";const std::array<unsigned,8> tschema{sizeof(HypotTraceEvent),sizeof(HypotTraceApi),sizeof(HypotTraceCell),sizeof(CONTEXT),hypot_trace_count,hypot_trace_api_count,hypot_trace_teb,hypot_trace_epoch};out.append(tstem+"schema.bin",tschema.data(),sizeof(tschema));out.append(tstem+"events.bin",hypot_trace_events,hypot_trace_count*sizeof(HypotTraceEvent));out.append(tstem+"APIs.bin",hypot_trace_apis,hypot_trace_api_count*sizeof(HypotTraceApi));out.append(tstem+"targets.bin",hypot_trace_targets,sizeof(hypot_trace_targets));out.append(tstem+"segments.bin",hypot_trace_segments,sizeof(hypot_trace_segments));out.append(tstem+"segments-ready.bin",&hypot_trace_segments_ready,4);
'''
 ref=one(ref,marker,output+marker);(out/'reference.cpp').write_text(ref)
 broker=(out/'original_broker.hpp').read_text();begin=broker.index('const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;std::cerr<<');end=broker.index('\n            if(handle_debug_checkpoint',begin);broker=broker[:begin]+'const auto code=event.u.Exception.ExceptionRecord.ExceptionCode;'+broker[end:];(out/'original_broker.hpp').write_text(broker)
 pin(__file__);pin(sys.executable)
 for p in out.iterdir():pin(p)
 report=dict(**{k:v for k,v in parent.items()if k not in('files','scope')},scope='Separate genuine six-case game/hypot/provider debugger instruction observations; no normal wrapper replay, source expected inputs or numerical predicted results',parent_preparation_sha256=sha(PARENT/'report.json'),normal_validation_sha256='80a4e558e8fc5d11bc2fb0f6fa9446d881c848690b8fd44c8543beca014ff313',trace_descriptors=len(descriptors),trace_event_bytes=1840,trace_api_bytes=9800,trace_cell_bytes=60,trace_context_bytes=716,trace_event_bound=32768,trace_API_bound=256,descriptor_gaps=gaps,provider_imports=len(imports),normal_return_replay_used=False,debugger_TF_RF_projection_mask=0x10100,files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');pin(p);(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),descriptors=len(descriptors),descriptor_gaps=len(gaps))))
if __name__=='__main__':main(sys.argv[1])
