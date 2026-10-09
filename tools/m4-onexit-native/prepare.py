
"""Fresh callback-registry native owner source preparation, preserving old accepted sources."""
import json,hashlib,re,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];HOME=Path(__file__).absolute().parent
BASE=ROOT/'reports/m4-crt-locale-batch/preparation-r9'
BASE_BUILD=ROOT/'reports/m4-crt-locale-batch/build-r9/build.json'
PROV=ROOT/'reports/m4-onexit-native/lifts-r1'
GAME=ROOT/'reports/m4-onexit-source/lifts-r4'
PI=ROOT/'reports/m4-onexit-review/interface-r1/instruction-contracts.json'
GI=ROOT/'reports/m4-onexit-source/interface-r1/instruction-contracts.json'
ATTRIBUTION=ROOT/'reports/m4-onexit-source/symbol-attribution-r2'
GAME_CALLBACKS=ROOT/'reports/m4-onexit-source/game-callbacks-r2'
TAIL=ROOT/'reports/m4-onexit-source/tail-lift-r1'
TAIL_RECEIPT=ROOT/'reports/m4-onexit-source/tail-receipt-r1'
FSQRT_REPAIR=ROOT/'reports/m4-onexit-source/zero-fsqrt-repair-r1'
FSQRT_HARDWARE=ROOT/'reports/m4-onexit-source/zero-fsqrt-hardware-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p):return json.loads(Path(p).read_bytes())
def need(x,w):
 if not x:raise RuntimeError(w)
def main(name):
 out=ROOT/'reports/m4-onexit-native'/name;need(re.fullmatch('preparation-r[1-9][0-9]*',name) and not out.exists(),'Fresh owned source preparation')
 deps={}
 def pin(p,h=None):
  p=Path(p).absolute();v=sha(p);need(h is None or h==v,'Pinned source dependency '+str(p));deps[str(p)]=v;return p
 base=js(pin(BASE/'report.json'));oldbuild=js(pin(BASE_BUILD));prov=js(pin(PROV/'report.json','eafc011b1efe88620a86b1a04e6fa5659212836052e30416424d2ab5c6d5bc45'));game=js(pin(GAME/'report.json','03c369d138fb0c00a018f5bcc5c2640f71e4822aec2815816139048edf5bfd0e'))
 for receipt in (base,prov,game):
  for p,h in receipt['files'].items():pin(p,h)
 for p,h in js(BASE/'pins.json')['files'].items():pin(p,h)
 need(oldbuild['passed'] and prov['passed'] and game['passed'],'Compiled source baselines')
 pi=js(pin(PI,'9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d'));gi=js(pin(GI));pin(Path(__file__))
 attribution=js(pin(ATTRIBUTION/'report.json','190dca3427791734853f033623a37604daccefbf8d6979adc19f0e09272a33d9'))
 need(attribution['passed'] and attribution['source_signature_checked'] and attribution['body_count']==64 and attribution['physical_COFF_count']==128,'Physical game attribution receipt')
 for p,h in attribution['files'].items():pin(p,h)
 attributed={v['entry']:v for v in js(pin(ATTRIBUTION/'physical-dispatch.json'))}
 tail=js(pin(TAIL/'report.json','58085b78a8c4b646bf6bda9b65f870bff626a438b6ae965ee8cc06d9f7a9d845'))
 tail_receipt=js(pin(TAIL_RECEIPT/'report.json','a1b5cf012701ae2c3dd668a4335c10d674ae8d5f403b6d924cb3668788ed41c8'))
 need(tail['passed'] and tail_receipt['passed'] and tail_receipt['tail_entry']==0x42a570 and tail_receipt['source_bytes']==22 and tail_receipt['instructions']==10 and tail_receipt['body_count']==1 and tail_receipt['physical_COFF_count']==2 and tail_receipt['original64_preserved'],'Exact additive lower shared tail receipt')
 for receipt in (tail,tail_receipt):
  for p,h in receipt['files'].items():pin(p,h)
 tail_dispatch=js(pin(TAIL_RECEIPT/'dispatch.json','a7e1ca3f6c614f0beca6e13f3e7ee2579387252acba5deea686731c96ec8ec62'))
 need(len(tail_dispatch)==1 and tail_dispatch[0]['entry']==0x42a570,'One additive shared tail entry')
 tail_rows=js(pin(TAIL_RECEIPT/'instruction-contracts.json'))['instructions'];game_rows={r['pc']:r for r in gi['instructions']}
 need(len(tail_rows)==10 and all(game_rows.get(r['pc'])==r for r in tail_rows),'Supplemental shared tail operands match sealed game source rows')
 fsqrt_repair=js(pin(FSQRT_REPAIR/'report.json','fc15b5f079f15c73480ab25b72f8e3cff6ea2f0de3513cfc2b35729a3bc9be72'))
 need(fsqrt_repair['passed'] and fsqrt_repair['overrides_entry']==0x4020d0 and fsqrt_repair['source_PC']==0x4020f5 and fsqrt_repair['removed_State_zero_stores']==[2755,2753,2745] and not fsqrt_repair['sealed_original64_modified'] and fsqrt_repair['physical_COFF_count']==2 and not fsqrt_repair['native_executed'],'Exact zero FSQRT sticky-state derivative scope')
 for p,h in fsqrt_repair['files'].items():pin(p,h)
 repaired_dispatch=js(pin(FSQRT_REPAIR/'dispatch.json','1d359fced5b86a535db8f7e23cac31033a966fc87abae0c32342983d50e36cc5'))
 need(len(repaired_dispatch)==1 and repaired_dispatch[0]['entry']==0x4020d0 and repaired_dispatch[0]['symbol']=='mw34_onexit_game_f_4020d0_sticky_body','One distinct physical zero FSQRT derivative')
 fsqrt_contract=js(pin(FSQRT_REPAIR/'repair.json'))
 need(fsqrt_contract['source_bytes_hex']=='d9fa' and fsqrt_contract['predicate']=='Exact raw80 IsZero(ST0) only' and fsqrt_contract['preserved_nonzero_semantics'] and fsqrt_contract['preserved_raw80_value'] and fsqrt_contract['preserved_CW_and_TOP'] and not fsqrt_contract['AFTER_machine_seed'],'Narrow source sticky-state repair policy')
 original_sqrt=pin(GAME/'f_4020d0-host.ll');repaired_sqrt=pin(FSQRT_REPAIR/'f_4020d0_sticky-host.ll')
 original_text=original_sqrt.read_text();repaired_text=repaired_sqrt.read_text()
 need(original_text.count(fsqrt_contract['before_branch'])==1 and original_text.replace(fsqrt_contract['before_branch'],fsqrt_contract['after_branch'],1).replace('@'+fsqrt_contract['physical_source_symbol']+'(','@'+fsqrt_contract['physical_repaired_symbol']+'(',1)==repaired_text,'Derivative changes only exact zero-branch stores and distinct function name')
 need(repaired_dispatch[0]['bridges']==fsqrt_repair['dispatch_manifest'][0]['bridges'] and set(repaired_dispatch[0]['bridges'])==set(game['source_bodies']['f_4020d0']['bridges']),'Sticky-state derivative retains exact source bridge vocabulary')
 fsqrt_hardware=js(pin(FSQRT_HARDWARE/'report.json','4bb43cc941d3925fda389109124da3999950bbb730c6da1f481edeeff3b18f0a'))
 need(fsqrt_hardware['passed'] and fsqrt_hardware['cases']==192 and fsqrt_hardware['all_IE_DE_PE_preserved'] and fsqrt_hardware['all_CW_TOP_raw80_zero_preserved'] and fsqrt_hardware['host_full_FX_restored'] and not fsqrt_hardware['native_derivative_body_executed'],'Independent finite exact D9FA zero FSQRT hardware evidence')
 for p,h in fsqrt_hardware['files'].items():pin(p,h)
 out.mkdir(parents=True)
 for p in BASE.iterdir():
  if p.suffix in ('.cpp','.hpp','.inc'):(out/p.name).write_bytes(p.read_bytes())
 for p in HOME.iterdir():
  if p.suffix in ('.hpp','.inc'):(out/p.name).write_bytes(p.read_bytes());pin(p)
 h=(out/'locale_batch.hpp').read_text().replace('namespace mw34::m4_crt_locale_batch {','namespace mw34::m4_onexit {struct SessionImpl;}\nnamespace mw34::m4_crt_locale_batch {',1)
 h=h.replace(' private:\n',' private:\n friend struct mw34::m4_onexit::SessionImpl;\n friend class mw34::m4_onexit::Session;\n bool research_standalone_{};unsigned registry_root_{};\n std::vector<std::array<std::uint64_t,32>>registry_growth_;\n void native_heap_size(unsigned,unsigned,unsigned);void native_heap_realloc(unsigned,unsigned,unsigned);\n',1)
 h=h.replace('unsigned guest{},requested{},extent{},mapped_bytes{},generation{},kind{};','unsigned guest{},requested{},extent{},mapped_bytes{},generation{},kind{},capacity{},retired_guest{};bool pending{};std::vector<std::byte>pending_native;')
 (out/'locale_batch.hpp').write_text(h)
 b=(out/'locale_batch_binding.inc').read_text().replace('cm::outer_owner_guard(*admitted_parent_);','if(!research_standalone_)cm::outer_owner_guard(*admitted_parent_);').replace('cm::outer_owner_guard(c);','if(!research_standalone_)cm::outer_owner_guard(c);')
 b=b.replace('if(!locale_complete_)deny("Complete genuine default locale required",0x78003dda);return;','if(!(research_standalone_?static_complete_:locale_complete_))deny("Complete genuine selected bootstrap required",0x78003dda);return;')
 b=b.replace('void Binding::first(const char*w,unsigned a,unsigned pc){if(!failed){','void Binding::first(const char*w,unsigned a,unsigned pc){if(!registry_growth_.empty())registry_growth_.back()[21]=1;if(!failed){')
 b=b.replace('if(extra)extra(*this,point);','if(extra)extra(*this,point);')
 (out/'locale_batch_binding.inc').write_text(b)
 o=(out/'locale_batch_operations.inc').read_text()
 o=o.replace('native_apis_.size()>128','native_apis_.size()>1024').replace('native_apis_.size()>=128','native_apis_.size()>=1024')
 o=o.replace('if(b!=p->expected||!p->native||std::memcmp(p->native,p->expected.data(),p->extent))','if(b!=p->expected||!p->native||(p->pending?(!p->pending_native.empty()&&std::memcmp(p->native,p->pending_native.data(),p->pending_native.size())):std::memcmp(p->native,p->expected.data(),p->extent)))')
 o=o.replace('checkpoint(runtime,"locale-static-locks-returned");batch_phase_=2;','checkpoint(runtime,"locale-static-locks-returned");if(research_standalone_)return;batch_phase_=2;')
 o=o.replace('source_accesses_.push_back({state.gpr.rip.dword,a,v,n,unsigned(write)});last_source_pc_=state.gpr.rip.dword;','source_accesses_.push_back({state.gpr.rip.dword,a,v,n,unsigned(write)});last_source_pc_=state.gpr.rip.dword;')
 o=o.replace('source_access(a,v,n,false);return v;','source_access(a,v,n,false);if(n==4&&a==0x5bb52c){if(v!=0x1decb0||state.gpr.rip.dword!=0x5ac11e)deny("Exact onexit source import relocation",a);research_projections_.push_back({5,state.gpr.rip.dword,a,unsigned(v),0x78004a36,0,0,0});return 0x78004a36;}if(n==4&&a==0x5bb530){if(v!=0x1deca2||state.gpr.rip.dword!=0x5ac580)deny("Exact dllonexit source import relocation",a);research_projections_.push_back({5,state.gpr.rip.dword,a,unsigned(v),0x78002fe5,0,0,0});return 0x78002fe5;}return v;')
 o=o.replace('for(const auto&a:source_api_contracts())if(a.raw==target&&a.tail)', 'if(target==0x78002fe5&&state.gpr.rip.dword==target){if(source_accesses_.empty()||source_accesses_.back().pc!=0x5ac580||source_accesses_.back().address!=0x5bb530||source_accesses_.back().value!=0x1deca2)deny("Actual DLL registration tail import relocation",target);return dispatch_body(target,s,this); }\n for(const auto&a:source_api_contracts())if(a.raw==target&&a.tail)')
 o=o.replace('if(!has_body(target))deny("Required source CALL dependency remains unrecovered",target,w.pc);','if(!has_body(target))deny("Required source CALL dependency remains unrecovered",target,w.pc);\n if(registry_root_&&target==0x5ac140&&runtime.memory().load<unsigned>({w.address+4})!=registration_callback(registry_root_))deny("Exact literal callback for current initializer required",w.address+4,w.pc);')
 o=o.replace('std::span(source_accesses_)),context);','std::span(source_accesses_)),context);')
 o=o.replace('sink("locale-diagnostic.bin",','for(std::size_t n=0;n<registry_growth_.size();++n)sink("registry-growth-"+std::to_string(n)+"-witness.bin",std::as_bytes(std::span(registry_growth_[n])),context);\n sink("locale-diagnostic.bin",')
 o=o.replace('if(!cleanup_sections_noexcept()||!cleanup_allocations_noexcept())','if(!cleanup_sections_noexcept()||!cleanup_allocations_noexcept())')
 o=o.replace('(active&&!failed&&!builder_complete_)','(active&&!failed&&!builder_complete_&&!research_standalone_)')
 o=o.replace('else if(std::string(spec->name)=="HeapFree")native_free(site,frame,argc);','else if(std::string(spec->name)=="HeapFree")native_free(site,frame,argc);\n else if(std::string(spec->name)=="HeapSize")native_heap_size(site,frame,argc);\n else if(std::string(spec->name)=="HeapReAlloc")native_heap_realloc(site,frame,argc);')
 o=o.replace('object->extent=request;object->mapped_bytes=mapped;','object->extent=request;object->mapped_bytes=mapped;object->capacity=0;')
 o=o.replace('if(p->native&&p->mapped&&a>=p->guest','if(p->native&&p->mapped&&!p->pending&&a>=p->guest')
 o=o.replace('if(s!=&state||p!=this||state.gpr.rip.dword!=target||calls_.empty())deny("Exact source branch continuation State/private token required",target);','if(research_standalone_&&target==0x5ac3ec&&registry_root_==0x5ac3d8&&s==&state&&p==this&&calls_.empty())throw SentinelComplete{};\n if(s!=&state||p!=this||state.gpr.rip.dword!=target||calls_.empty())deny("Exact source branch continuation State/private token required",target);')
 o=o.replace('return this;\n}\nvoid*Binding::batch_missing','if(research_standalone_&&calls_.empty())stable_hook(45);\n return this;\n}\nvoid*Binding::batch_missing')
 o=o.replace('if(!p.native&&p.mapped){try{runtime.memory().unmap({p.guest});p.mapped=false;}catch(...){okay=false;}}','if(!p.native&&p.mapped){try{runtime.memory().unmap({p.guest});p.mapped=false;if(p.retired_guest){runtime.memory().unmap({p.retired_guest});p.retired_guest=0;}}catch(...){okay=false;}}')
 (out/'locale_batch_operations.inc').write_text(o+'\n#include "registry_api.inc"\n')
 # Preserve strict named/owner/RVA proof and admit only the two physically
 # verified allocator aliases required by the new actual API domain.
 forward=(out/'forward_identity.inc').read_text()
 needle='const std::array<std::pair<const char*,const char*>,5>allowed{{{"HeapAlloc","RtlAllocateHeap"},'
 need(forward.count(needle)==1,'Exact frozen native export proof allowlist patch site')
 forward=forward.replace(needle,'const std::array<std::pair<const char*,const char*>,7>allowed{{{"HeapSize","RtlSizeHeap"},{"HeapReAlloc","RtlReAllocateHeap"},{"HeapAlloc","RtlAllocateHeap"},',1)
 (out/'forward_identity.inc').write_text(forward)
 # Rename only the old generated metadata/dispatch entry functions, preserving old literal object names.
 contract=(out/'source_contract.inc').read_text()
 for old in ('instruction','source_spans','source_pages','generated_undefined_sites','source_api_contracts','has_body','dispatch_body'):
  contract=re.sub(r'\b'+old+r'\(', 'baseline_'+old+'(',contract)
 (out/'source_contract.inc').write_text(contract)
 # Generate the exact additive decoded operand checker and source dispatch.
 rows={r['pc']:r for r in pi['instructions']}
 rows.update({r['pc']:r for r in gi['instructions']})
 regs={r:i for i,r in enumerate(['','eax','ecx','edx','ebx','esp','ebp','esi','edi','al','cl','dl','bl','ah','ch','dh','bh','ax','cx','dx','bx','sp','bp','si','di'])}
 def operand(r,i,x):
  k=x['kind'];bits=x.get('bits',0) or next((v.get('bits',0) for v in r['decoded_operands'] if v.get('bits',0)),32)
  if k=='register':return '{'+f'1,{bits//8},{regs[x["register"]]},0,0,0,1,0,0,1'+'}'
  if k=='immediate':return '{'+f'2,{bits//8},0,0,0,0,1,0,{x["value"]&0xffffffffffffffff}ULL,1'+'}'
  if k=='x87_register':return '{}'
  need(k=='memory','Decoded source operand kind '+k);terms=x['terms'];base=0;index=0;scale=1
  for t in terms:
   if not base and t['scale']==1:base=regs[t['register']]
   else:index=regs[t['register']];scale=t['scale']
  disp=x['displacement'];disp=disp if disp<2**31 else disp-2**32
  access=int(i in r['explicit_memory_reads'])+2*int(i in r['explicit_memory_writes'])
  return '{'+f'3,{bits//8},0,{int(x["segment"]=="fs")},{base},{index},{scale},{disp},0,{access}'+'}'
 lines=['} // composition anonymous namespace','namespace mw34::m4_crt_locale_batch {','namespace {','constexpr SourceInstruction registry_instructions[]{']
 for pc,r in sorted(rows.items()):
  ops=r['decoded_operands'];need(len(ops)<=3,'Bounded decoded operand count');rep={None:0,'rep':1,'repe':2,'repz':2,'repne':3,'repnz':3}.get(r.get('repeat'),0)
  lines.append('{'+f'{pc},{r["width"]},{json.dumps(r["mnemonic"])},{{{{'+','.join([operand(r,i,x) for i,x in enumerate(ops)]+['{}']*(3-len(ops)))+'}},'+f'{len(ops)},{rep}'+'},')
 # Source identity spans are compacted exact unique original rows; no mutable data claimed code.
 newrows={r['pc']:r for r in gi['instructions']};allowed=[(s['start'],s['stop']) for s in pi['new_spans']]
 newrows.update({r['pc']:r for r in pi['instructions'] if any(a<=r['pc']<b for a,b in allowed)})
 spans=[];raw=bytearray();start=None;end=None
 for pc,r in sorted(newrows.items()):
  if start is not None and pc!=end:spans.append((start,end,bytes(raw)));start=None;raw=bytearray()
  if start is None:start=pc
  raw.extend(bytes.fromhex(r['bytes_hex']));end=pc+r['width']
 if start is not None:spans.append((start,end,bytes(raw)))
 lines+=['};','constexpr SourceSpan registry_spans[]{']+['{'+f'{a},{b-a},5,"{hashlib.sha256(code).hexdigest()}"'+'},' for a,b,code in spans]+['};']
 # Provider source/data pages are accepted raw original input. Game pages are already image-owned.
 pages={int(p):v for p,v in base['source_pages'].items()}
 for a,b,_ in spans:
  if a>=0x78000000:
   for page in range(a&~4095,(b+4095)&~4095,4096):pages[page]=5
 lines+=['constexpr unsigned registry_game_pages[]{'+','.join(map(str,sorted(set(gi['source_data_pages'])|{0x63c000})))+'};']
 lines+=['constexpr SourcePage registry_pages[]{']+['{'+f'{p},{v}'+'},' for p,v in sorted(pages.items())]+['};']
 # Actual named game IATs map to exact provider entry, a declared source-import relocation.
 lines+=['constexpr SourceApi registry_apis[]{{0x780015b5,0x7802e1dc,0x34bd0,3,"HeapSize",0},{0x78011c27,0x7802e0b4,0x3464a,4,"HeapReAlloc",0}};','}']
 lines+=['const SourceInstruction*instruction(unsigned pc)noexcept{auto it=std::lower_bound(std::begin(registry_instructions),std::end(registry_instructions),pc,[](const auto&i,unsigned p){return i.pc<p;});return it!=std::end(registry_instructions)&&it->pc==pc?it:baseline_instruction(pc);}',
 'std::span<const SourceSpan>source_spans()noexcept{static const auto all=[](){auto b=baseline_source_spans();std::vector<SourceSpan>v(b.begin(),b.end());v.insert(v.end(),std::begin(registry_spans),std::end(registry_spans));return v;}();return all;}',
 'std::span<const SourcePage>source_pages()noexcept{return registry_pages;}',
 'std::span<const SourceApi>source_api_contracts()noexcept{static const auto all=[](){auto b=baseline_source_api_contracts();std::vector<SourceApi>v(b.begin(),b.end());v.insert(v.end(),std::begin(registry_apis),std::end(registry_apis));return v;}();return all;}']
 bodies={}
 for k,v in prov['source_bodies'].items():
  text=(PROV/(k+'-host.ll')).read_text();symbol=re.search(r'^define ptr @(\w+)\(',text,re.M)[1];bodies[v['entry']]=symbol
 game_symbols=[]
 for v in game['dispatch_manifest']:
  component='f_'+format(v['entry'],'x');host_path=pin(GAME/(component+'-host.ll'))
  text=host_path.read_text();matches=re.findall(r'^define ptr @(\w+)\(([^\n]+)\)(?: #\d+)? \{',text,re.M)
  need(len(matches)==1,'One physical game literal entry define')
  physical_symbol,args=matches[0]
  need(re.fullmatch(r'ptr(?: noalias)? %\w+, i32 %\w+, ptr(?: noalias)? %\w+',args) is not None,'Literal game body has ptr(ptr,i32,ptr) signature')
  need(physical_symbol==v['symbol']+'_body' and physical_symbol=='mw34_onexit_game_'+component+'_body','Physical game entry attribution agrees with literal source entry')
  actual=attributed[v['entry']]
  need(actual['source_function_symbol']==physical_symbol and actual['source_signature']=='ptr (ptr, i32, ptr)' and Path(actual['host_LL']).absolute()==host_path and actual['host_sha256']==sha(host_path),'Independent physical attribution agrees with LLVM entry/signature')
  for level,obj in actual['objects'].items():
   sealed=v['objects'][level]
   need(obj['machine']==0x8664 and obj['symbol']==physical_symbol and Path(obj['path']).absolute()==Path(sealed['path']).absolute() and sealed['sha256']==obj['sha256'],'Independent physical COFF attribution agrees with frozen literal object')
  bodies[v['entry']]=physical_symbol
  game_symbols.append(dict(entry=v['entry'],metadata_symbol=v['symbol'],physical_symbol=physical_symbol,source_signature='ptr (ptr, i32, ptr)',native_declaration='void*(State*,unsigned,void*)',host_path=str(host_path),host_sha256=sha(host_path),objects=v['objects']))
 for v in tail_dispatch:
  host_path=pin(TAIL/('f_'+format(v['entry'],'x')+'-host.ll'));matches=re.findall(r'^define ptr @(\w+)\(([^\n]+)\)(?: #\d+)? \{',host_path.read_text(),re.M)
  need(len(matches)==1 and matches[0][0]==v['symbol'] and re.fullmatch(r'ptr(?: noalias)? %\w+, i32 %\w+, ptr(?: noalias)? %\w+',matches[0][1]) is not None,'Actual additive shared tail ptr(ptr,i32,ptr) define')
  need(v['entry'] not in bodies,'Additive shared tail does not replace any frozen literal entry')
  for level,obj in v['objects'].items():
   sealed=tail['dispatch_manifest'][0]['objects'][level]
   need(obj['machine']==0x8664 and obj['symbol']==v['symbol'] and Path(obj['path']).absolute()==Path(sealed['path']).absolute() and obj['sha256']==sealed['sha256'],'Actual additive shared tail COFF export attribution')
  bodies[v['entry']]=v['symbol']
  game_symbols.append(dict(entry=v['entry'],metadata_symbol=v['symbol'],physical_symbol=v['symbol'],source_signature='ptr (ptr, i32, ptr)',native_declaration='void*(State*,unsigned,void*)',host_path=str(host_path),host_sha256=sha(host_path),objects=v['objects'],additive_shared_tail=True))
 repaired_overrides=[]
 for v in repaired_dispatch:
  host_path=repaired_sqrt;matches=re.findall(r'^define ptr @(\w+)\(([^\n]+)\)(?: #\d+)? \{',host_path.read_text(),re.M)
  need(len(matches)==1 and matches[0][0]==v['symbol'] and re.fullmatch(r'ptr(?: noalias)? %\w+, i32 %\w+, ptr(?: noalias)? %\w+',matches[0][1]) is not None,'Actual zero FSQRT derivative ptr(ptr,i32,ptr) define')
  need(bodies[v['entry']]==fsqrt_contract['physical_source_symbol'] and v['symbol'] not in bodies.values(),'Derivative overrides only the exact frozen 4020D0 entry with a distinct symbol')
  for level,obj in v['objects'].items():
   sealed=fsqrt_repair['dispatch_manifest'][0]['objects'][level]
   need(obj['machine']==0x8664 and obj['symbol']==v['symbol'] and obj==sealed and sha(obj['path'])==obj['sha256'],'Actual zero FSQRT derivative COFF physical attribution')
  repaired_overrides.append(dict(entry=v['entry'],sealed_symbol=bodies[v['entry']],selected_symbol=v['symbol'],source_PC=0x4020f5,source_signature='ptr (ptr, i32, ptr)',native_declaration='void*(State*,unsigned,void*)',host_path=str(host_path),host_sha256=sha(host_path),objects=v['objects'],repair_report_sha256=sha(FSQRT_REPAIR/'report.json'),hardware_report_sha256=sha(FSQRT_HARDWARE/'report.json')))
  bodies[v['entry']]=v['symbol']
 (out/'game-dispatch-attribution.json').write_text(json.dumps(dict(passed=True,scope='Frozen LLVM entry/signature and physical AMD64 COFFs plus additive shared tail and explicit 4020D0 zero-FSQRT sticky-state derivative; original COFFs retained, runtime acceptance pending',attribution_report_sha256=sha(ATTRIBUTION/'report.json'),shared_tail_receipt_sha256=sha(TAIL_RECEIPT/'report.json'),entries=game_symbols,selected_semantic_overrides=repaired_overrides),sort_keys=True,indent=2)+'\n')
 bridge_path=pin(HOME/'game_fp_bridges.inc');bridge_text=bridge_path.read_text()
 expected_signature='extern "C" void mw34_onexit_game_fsqrt_raw80(const void*input,void*result)'
 need(bridge_text.count(expected_signature)==1 and '"r"(result),"r"(input)' in bridge_text,'Raw80 FSQRT bridge preserves exact input then output pointer direction')
 sqrt_calls=[]
 for host_path in [Path(v['host_path']) for v in game_symbols]+[repaired_sqrt]:
  source=host_path.read_text()
  for match in re.finditer(r'call void @mw34_onexit_game_fsqrt_raw80\(ptr (%onexit\.sqrt\.in\.(\d+)), ptr (%onexit\.sqrt\.out\.\2)\)',source):
   before=source[:match.start()];after=source[match.end():]
   need(re.search(r'store x86_fp80 %\w+, ptr '+re.escape(match[1])+r', align 16',before) is not None and re.search(r'load x86_fp80, ptr '+re.escape(match[3])+r', align 16',after) is not None,'Exact typed raw80 FSQRT scratch input store/output load')
   sqrt_calls.append(dict(host_path=str(host_path),host_sha256=sha(host_path),call_line=source[:match.start()].count('\n')+1,input_pointer=match[1],output_pointer=match[3],scratch_type='x86_fp80',scratch_alignment=16))
  need(source.count('call void @mw34_onexit_game_fsqrt_raw80(')==sum(1 for c in sqrt_calls if c['host_path']==str(host_path)),'Every raw80 FSQRT call has exact input/output pointer contract')
 need(len(sqrt_calls)==2,'Original and derivative exact raw80 FSQRT call attribution')
 (out/'fsqrt-pointer-contract.json').write_text(json.dumps(dict(passed=True,scope='Static physical LLVM call and fresh C++ bridge pointer attribution; no native call execution',symbol='mw34_onexit_game_fsqrt_raw80',LLVM_signature='void(ptr input,ptr output)',CXX_signature=expected_signature,input_operand='asm operand1: fldt',output_operand='asm operand0: fstpt',bridge_path=str(bridge_path),bridge_sha256=sha(bridge_path),calls=sqrt_calls,fix='Swap declared parameter order to input/output while retaining asm input/output operands',native_executed=False),sort_keys=True,indent=2)+'\n')
 callbacks=js(pin(ROOT/'reports/m4-onexit-review/callbacks-r1/callbacks.json'))
 # Pre-IR NEXT_PC source markers and optimized State writes attribute each
 # callback to its actual original instruction, including register-driven PC
 # stores. Body-entry fallback would invent a site for these game paths.
 callback_report=js(pin(GAME_CALLBACKS/'report.json','f68b5352c52e02455cd4e4177ca451be6c16c3c2b2d86f398c37d712229e7ba0'))
 need(callback_report['passed'] and callback_report['bodies']==64 and callback_report['unique_sites']==18,'Exact frozen game source callback attribution')
 for p,h in callback_report['files'].items():pin(p,h)
 game_callbacks=js(pin(GAME_CALLBACKS/'callbacks.json','df3f761e5672e290a01d8ef729f6bef3489d9d9a5520c532ee685e0d689d4076'))
 tail_callbacks=js(pin(TAIL_RECEIPT/'callbacks.json','9317687a6f188709479dc00a7a9406ed38463ac3d3f2bc7125b3456ca429cbd0'))
 need(tail_callbacks['State_offsets_by_original_PC']=={'4367737':[2069]} and game_callbacks['State_offsets_by_original_PC']['4367737']==[2069],'Additive tail 42A579 XOR AF attribution matches existing original instruction map')
 need(game_callbacks['State_offsets_by_original_PC']['4262442']==[2069],'Actual 410A2A XOR AF callback attribution')
 repaired_callbacks=js(pin(FSQRT_REPAIR/'callbacks.json'))['State_offsets_by_original_PC']
 need(all(game_callbacks['State_offsets_by_original_PC'].get(pc)==offsets for pc,offsets in repaired_callbacks.items()) and set(repaired_callbacks)=={'4202737','4202739','4202746'},'Sticky-state derivative preserves exact source undefined callback attribution')
 counts={int(pc):len(offsets) for pc,offsets in callbacks['State_offsets_by_original_PC'].items()}
 newcounts={int(pc):len(offsets) for pc,offsets in game_callbacks['State_offsets_by_original_PC'].items()}
 for pc,count in newcounts.items():counts[pc]=max(counts.get(pc,0),count)
 (out/'callback-attribution.json').write_text(json.dumps(dict(passed=True,scope='Exact frozen original-PC callback multiplicity, no changed State/FX/source objects',provider_callback_path=str(ROOT/'reports/m4-onexit-review/callbacks-r1/callbacks.json'),provider_callback_sha256=sha(ROOT/'reports/m4-onexit-review/callbacks-r1/callbacks.json'),game_callback_report_sha256=sha(GAME_CALLBACKS/'report.json'),game_callback_sha256=sha(GAME_CALLBACKS/'callbacks.json'),new_callback_counts={str(pc):count for pc,count in sorted(counts.items())},fixed_example=dict(pc=0x410a2a,mnemonic='xor',State_offsets=[2069])),sort_keys=True,indent=2)+'\n')
 newlist=[pc for pc,count in sorted(counts.items()) for _ in range(count)]
 lines+=['std::span<const unsigned>generated_undefined_sites()noexcept{static const auto all=[](){auto b=baseline_generated_undefined_sites();std::vector<unsigned>v;constexpr unsigned n[]{'+','.join(map(str,newlist))+'};std::map<unsigned,unsigned>counts;for(auto pc:b)++counts[pc];std::map<unsigned,unsigned>added;for(auto pc:n)++added[pc];for(auto[pc,num]:added)counts[pc]=std::max(counts[pc],num);for(auto[pc,num]:counts)for(unsigned k=0;k<num;++k)v.push_back(pc);return v;}();return all;}']
 lines+=['unsigned registration_callback(unsigned root)noexcept{switch(root){']+['case '+str(r['entry'])+':return '+str(r['registration']['callback'])+';' for r in gi['registration_roots']]+['default:return 0;}}']
 for symbol in sorted(set(bodies.values())):lines.append('extern "C" void*'+symbol+'(State*,unsigned,void*);')
 lines+=['bool has_body(unsigned pc)noexcept{switch(pc){']+['case '+str(pc)+':return true;' for pc in sorted(bodies)]+['default:return baseline_has_body(pc);}}','void*dispatch_body(unsigned pc,State*s,void*p){switch(pc){']+['case '+str(pc)+':return '+symbol+'(s,pc,p);' for pc,symbol in sorted(bodies.items())]+['default:return baseline_dispatch_body(pc,s,p);}}','}','namespace {']
 (out/'registry_contract.inc').write_text('\n'.join(lines)+'\n')
 c=(out/'composition.cpp').read_text();c='#include <map>\n#include "session.hpp"\n#define main mw34_archived_driver_main\n'+c
 c=c.replace('#include "main_v2.inc"','')
 forward='namespace mw34::m4_onexit {void registry_checkpoint(m4_runtime::Runtime&,const char*); }\n'
 forward+='namespace {void entry_checkpoint(Runtime&r){m4_onexit::registry_checkpoint(r,"entry-projected");}void matherr_checkpoint(Runtime&r,const char*n){m4_onexit::registry_checkpoint(r,n);}void control_checkpoint(Runtime&r,const char*n){m4_onexit::registry_checkpoint(r,n);}void initterm_checkpoint(Runtime&r,const char*n){m4_onexit::registry_checkpoint(r,n);}void mainargs_checkpoint(Runtime&r,const char*n){m4_onexit::registry_checkpoint(r,n);}}\n'
 for namespace in ('m4_crt_filename','m4_crt_commandline_carry','m4_crt_parser_prefix','m4_crt_locale_default','m4_crt_heap_init','m4_crt_heap_create','m4_crt_heap_mode','m4_crt_heap_version','m4_crt_heap_return','m4_crt_allocation','m4_crt_locale_batch'):
  forward+='namespace mw34::'+namespace+' {void checkpoint(Runtime&r,const char*n){m4_onexit::registry_checkpoint(r,n);}}\n'
 c+='\n'+forward
 c=c.replace('#include "source_contract.inc"','#include "source_contract.inc"\n#include "registry_contract.inc"')
 c=c.replace('namespace {thread_local Binding*authority{};thread_local Binding*capture_binding{};struct CallerComplete{};}','namespace {thread_local Binding*authority{};thread_local Binding*capture_binding{};struct CallerComplete{};struct SentinelComplete{};}')
 # declaration belongs before Binding::batch_called uses the generated callback lookup
 h=(out/'locale_batch.hpp').read_text().replace('bool has_body(unsigned)noexcept;','bool has_body(unsigned)noexcept;unsigned registration_callback(unsigned)noexcept;');(out/'locale_batch.hpp').write_text(h)
 b=(out/'locale_batch_binding.inc').read_text().replace('struct CallerComplete{};','struct CallerComplete{};struct SentinelComplete{};');(out/'locale_batch_binding.inc').write_text(b)
 conflicting={'__remill_read_memory_32','__remill_write_memory_32','__remill_write_memory_8','__remill_function_return'}
 cl=[]
 for line in c.splitlines():
  m=re.match(r'extern "C" .+?(\w+)\([^\n]*?\)\s*(?:noexcept\(false\))?\s*\{',line)
  if m and m[1] in conflicting:continue
  cl.append(line)
 c='\n'.join(cl)+'\n#include "session_impl.inc"\n'
 bridges={name for v in prov['source_bodies'].values() for name in v['bridges']}
 bridges.update(name for v in game['source_bodies'].values() for name in v['bridges'])
 bridges.update(name for v in tail['source_bodies'].values() for name in v['bridges'])
 bridges.update(name for v in fsqrt_repair['source_bodies'].values() for name in v['bridges'])
 existing=set(re.findall(r'extern "C" .+?(\w+)\(',c))
 extra=[]
 for name in sorted(bridges-existing):
  if name.endswith('_undefined_8'):extra.append('extern "C" unsigned char '+name+'(){return mw34::m4_onexit::undefined();}')
  elif name.startswith('sub_') or '_direct_' in name:extra.append('extern "C" void*'+name+'(State*s,unsigned a,void*p){return mw34::m4_onexit::called(p,s,a);}')
  elif name.startswith('mw34_onexit_game_read'):
   suffix=name.split('read',1)[1]
   if suffix.startswith('f'):continue
   typ={'8':'unsigned char','16':'unsigned short','32':'unsigned','64':'std::uint64_t'}[suffix];extra.append('extern "C" '+typ+' '+name+'(void*p,unsigned a){return static_cast<'+typ+'>(mw34::m4_onexit::read(p,a,'+str(int(suffix)//8)+'));}')
  elif name.startswith('mw34_onexit_game_write'):
   suffix=name.split('write',1)[1]
   if suffix.startswith('f'):continue
   typ={'8':'unsigned char','16':'unsigned short','32':'unsigned','64':'std::uint64_t'}[suffix];extra.append('extern "C" void*'+name+'(void*p,unsigned a,'+typ+' v){return mw34::m4_onexit::write(p,a,v,'+str(int(suffix)//8)+');}')
  elif name in ('mw34_onexit_game_call','mw34_onexit_game_return','mw34_onexit_game_jump','mw34_onexit_game_missing'):
   method={'mw34_onexit_game_call':'called','mw34_onexit_game_return':'returned','mw34_onexit_game_jump':'missing','mw34_onexit_game_missing':'missing'}[name];extra.append('extern "C" void*'+name+'(State*s,unsigned a,void*p){return mw34::m4_onexit::'+method+'(p,s,a);}')
  elif name.startswith('mw34_onexit_game_fpu') or name=='mw34_onexit_game_fsqrt_raw80':continue
  elif name in conflicting:continue
  else:raise RuntimeError('Unclassified additive bridge '+name)
 c+='\n'.join(extra)+'\n#include "game_fp_bridges.inc"\n';(out/'registry_library.cpp').write_text(c)
 # Preserved originalcomposition remains archival comparison input only; library has renamedunuseddriver.
 objects=dict(oldbuild['entry_objects']);objects.update(prov['entry_objects']);objects.update(game['entry_objects'])
 objects.update(tail['entry_objects'])
 objects.update({obj['path']:obj['sha256'] for v in repaired_dispatch for obj in v['objects'].values()})
 for p,h in objects.items():pin(p,h)
 for p,h in oldbuild['libraries'].items():pin(p,h)
 files=dict(deps)
 for p in out.iterdir():
  if p.is_file():files[str(p.resolve())]=sha(p)
 report=dict(passed=True,schema='mw34-m4-onexit-native-preparation-v1',native_executed=False,State_reseed_after_writer=False,entry_objects=objects,libraries=oldbuild['libraries'],source_pages=pages,source_bodies_modified=False,exact_new_provider_entries=22,exact_new_game_entries=65,additive_shared_tail=dict(entry=0x42a570,source_bytes=22,instructions=10,lift_report_sha256=sha(TAIL/'report.json'),physical_receipt_sha256=sha(TAIL_RECEIPT/'report.json'),original64_modified=False),summary_word_15='Currently live native heap handle; zero after cleanup; historical acquisition retained only in inherited owner/API witnesses',game_body_signature='ptr(ptr,i32,ptr); C++ void*(State*,unsigned,void*)',game_symbol_attribution_report_sha256=sha(ATTRIBUTION/'report.json'),bootstrap_observation_exports='Existing HeapCreate/GetVersionExA witnesses, registry, query buffers, access/event/scheduler fields and create/query/destroy measured API identities; absent phases remain zero; no new host calls or fabricated export proof',caller_error_semantics='Inherited owner caller_error is immutable historical bootstrap input; per-Session invocation LastErrorBoundary preserves current external caller error',whole_M4_complete=False,files=files)
 report['selected_semantic_overrides']=repaired_overrides
 report['source_bodies_modified_semantics']='Sealed original source/COFF files remain unchanged; selected 4020D0 is an explicit additive semantic derivative retaining sticky IE/DE/PE only on literal zero-FSQRT path'
 report['fsqrt_pointer_contract_sha256']=sha(out/'fsqrt-pointer-contract.json')
 report['fsqrt_bridge_fix']='Physical LLVM input/output scratch pointer order; original asm operations retained'
 (out/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');files[str((out/'report.json').resolve())]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),sort_keys=True,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
