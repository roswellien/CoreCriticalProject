"""Fresh string-family derivative of the sealed accepted registration owner."""
import hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];HOME=Path(__file__).absolute().parent
BASE=ROOT/'reports/m4-onexit-native/preparation-r11'
PROV=ROOT/'reports/m4-strings-native/lifts-r1';GAME=ROOT/'reports/m4-strings-source/lifts-r1';REC=ROOT/'reports/m4-strings-source/recovery-r7'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p):return json.loads(Path(p).read_bytes())
def need(x,w):
 if not x:raise RuntimeError(w)
def main(name):
 out=ROOT/'reports/m4-strings-native'/name;need(re.fullmatch('preparation-r[1-9][0-9]*',name) and not out.exists(),'Fresh owned derivative directory');deps={}
 def pin(p,h=None):
  p=Path(p).absolute();v=sha(p);need(h is None or h==v,'Exact parent or source pin '+str(p));deps[str(p)]=v;return p
 accepted=js(pin(ROOT/'reports/m4-joint-startup54-root/acceptance-r1/report.json','5a7feb121fd1a8fc95d4e31da18af67099e91012b3f70e36e17575973b4cd89c'))
 base=js(pin(BASE/'report.json','ffbf18afdcf9756f2e5cee96edccb0e3ecd6ae614c568353e0e6dec4ee5797d4'))
 prov=js(pin(PROV/'report.json','4cfb5495ea88f9abef2f0a891f8b85aac33f32c6cc75b739ba418e402866a13e'))
 game=js(pin(GAME/'report.json','903f755f6f21cf67f873925fb1bfbe4748e543af6b5fdc9de325a925fac17a3a'))
 rec=js(pin(REC/'report.json','972ec961d7617d2e7b789d23ab1ce82da0c33424b37c12e2dc94c23d1e154341'))
 need(base['passed'] and prov['passed'] and game['passed'] and rec['passed'],'Passed frozen parent and literal source preparation')
 for receipt in (base,prov,game,rec):
  for p,h in receipt['files'].items():pin(p,h)
 attrdir=ROOT/'reports/m4-strings-source/symbol-attribution-r1';attr=js(pin(attrdir/'report.json','af1ce72980f8a7d77d1445b9b0d0b41601afe84f80125104a7eb0bfa29c11b1d'))
 for p,h in attr['files'].items():pin(p,h)
 dispatch=js(pin(attrdir/'physical-dispatch.json'))
 cbdir=ROOT/'reports/m4-strings-source/game-callbacks-r1';cb=js(pin(cbdir/'report.json','ed9975573be6803854775877eb94679d78651822e96e7aa42e982552b82e96db'))
 for p,h in cb['files'].items():pin(p,h)
 gamecallbacks=js(pin(cbdir/'callbacks.json','b881e7ed9d73bcae8bdaebf83b88046ebdc4a8221ed63c95490d32da3380b4ad'))['State_offsets_by_original_PC']
 pi=js(pin(PROV/'instruction-contracts.json'));gi=js(pin(REC/'instruction-contracts.json'));inputrows=js(pin(REC/'string-inputs.json'))
 need(len(inputrows)==17 and len(dispatch)==39 and len(pi['instructions'])==117,'Exact 17-root/39-body/117-provider-row family')
 actual_inputs=[r for r in inputrows if r['actual_strdup_called']];need(len(actual_inputs)==16 and len([r for r in inputrows if not r['actual_strdup_called']])==1,'Exact sixteen real strdup calls and one literal null descriptor constructor')
 provider_attrdir=ROOT/'reports/m4-strings-native/symbol-attribution-r1';provider_attr=js(pin(provider_attrdir/'report.json','546a3963ca36f801022d8a5f4ce71407b38035596cc08f42b9b476c010e1c4b9'))
 need(provider_attr['passed'] and provider_attr['body_count']==3 and provider_attr['physical_COFF_count']==6,'Physical AMD64 provider exports')
 for p,h in provider_attr['files'].items():pin(p,h)
 out.mkdir(parents=True)
 for p in BASE.iterdir():
  if p.suffix in ('.cpp','.hpp','.inc'):(out/p.name).write_bytes(p.read_bytes())
 pin(Path(__file__));pin(HOME/'strings_operations.inc')
 (out/'strings_operations.inc').write_bytes((HOME/'strings_operations.inc').read_bytes())
 # Old generated dispatch is immutable in the parent; renamed only in derivative.
 contract=(out/'registry_contract.inc').read_text()
 for fn in ('instruction','source_spans','source_pages','generated_undefined_sites','source_api_contracts','has_body','dispatch_body','registration_callback'):
  contract=re.sub(r'(?<!baseline_)\b'+fn+r'\(', 'accepted_'+fn+'(',contract)
 (out/'registry_contract.inc').write_text(contract)
 rows={r['pc']:r for r in gi['instructions']};rows.update({r['pc']:r for r in pi['instructions']})
 regs={r:i for i,r in enumerate(['','eax','ecx','edx','ebx','esp','ebp','esi','edi','al','cl','dl','bl','ah','ch','dh','bh','ax','cx','dx','bx','sp','bp','si','di'])}
 def operand(r,i,x):
  k=x['kind'];bits=x.get('bits',0) or next((v.get('bits',0) for v in r['decoded_operands'] if v.get('bits',0)),32)
  if k=='register':return '{'+f'1,{bits//8},{regs[x["register"]]},0,0,0,1,0,0,1'+'}'
  if k=='immediate':return '{'+f'2,{bits//8},0,0,0,0,1,0,{x["value"]&0xffffffffffffffff}ULL,1'+'}'
  need(k=='memory','Only integer string-family source operands');base=0;index=0;scale=1
  for t in x['terms']:
   if not base and t['scale']==1:base=regs[t['register']]
   else:index=regs[t['register']];scale=t['scale']
  disp=x['displacement'];disp=disp if disp<2**31 else disp-2**32;access=int(i in r['explicit_memory_reads'])+2*int(i in r['explicit_memory_writes'])
  return '{'+f'3,{bits//8},0,{int(x["segment"]=="fs")},{base},{index},{scale},{disp},0,{access}'+'}'
 lines=['} // anonymous composition namespace','namespace mw34::m4_crt_locale_batch {','namespace {','struct StringInput {unsigned root,source,call,size,physical_size;const char*physical_sha;};','constexpr StringInput string_inputs[]{']
 for r in actual_inputs:lines.append('{'+f'{r["root"]},{r["source"]},{r["CALL_pc"]},{r["size"]},{r["physical_read_end"]-r["source"]},"{hashlib.sha256(bytes.fromhex(r["physical_bytes_hex"])).hexdigest()}"'+'},')
 lines+=['};','const StringInput*string_input(unsigned root)noexcept{for(const auto&i:string_inputs)if(i.root==root)return &i;return nullptr;}','constexpr SourceInstruction string_instructions[]{']
 for pc,r in sorted(rows.items()):
  ops=r['decoded_operands'];need(len(ops)<=3,'Finite operand count');rep={None:0,'rep':1,'repe':2,'repz':2,'repne':3,'repnz':3}.get(r.get('repeat'),0)
  lines.append('{'+f'{pc},{r["width"]},{json.dumps(r["mnemonic"])},{{{{'+','.join([operand(r,i,x) for i,x in enumerate(ops)]+['{}']*(3-len(ops)))+'}},'+f'{len(ops)},{rep}'+'},')
 spans=[];raw=bytearray();start=None;end=None
 for pc,r in sorted(rows.items()):
  if start is not None and pc!=end:spans.append((start,end,bytes(raw)));start=None;raw=bytearray()
  if start is None:start=pc
  raw.extend(bytes.fromhex(r['bytes_hex']));end=pc+r['width']
 if start is not None:spans.append((start,end,bytes(raw)))
 lines+=['};','constexpr SourceSpan string_spans[]{']+['{'+f'{a},{b-a},5,"{hashlib.sha256(raw).hexdigest()}"'+'},' for a,b,raw in spans]+['};']
 providerpages={int(p):v for p,v in base['source_pages'].items()}
 for a,b,_ in spans:
  if a>=0x78000000:
   for page in range(a&~4095,(b+4095)&~4095,4096):providerpages[page]=5
 lines+=['constexpr SourcePage string_pages[]{']+['{'+f'{p},{v}'+'},' for p,v in sorted(providerpages.items())]+['};','}']
 lines+=['const SourceInstruction*instruction(unsigned pc)noexcept{auto it=std::lower_bound(std::begin(string_instructions),std::end(string_instructions),pc,[](const auto&i,unsigned p){return i.pc<p;});return it!=std::end(string_instructions)&&it->pc==pc?it:accepted_instruction(pc);}',
 'std::span<const SourceSpan>source_spans()noexcept{static const auto all=[](){auto b=accepted_source_spans();std::vector<SourceSpan>v(b.begin(),b.end());v.insert(v.end(),std::begin(string_spans),std::end(string_spans));return v;}();return all;}',
 'std::span<const SourcePage>source_pages()noexcept{return string_pages;}',
 'std::span<const SourceApi>source_api_contracts()noexcept{return accepted_source_api_contracts();}']
 callbacks=js(PROV/'callbacks.json')['State_offsets_by_original_PC'];counts={int(pc):len(offsets) for pc,offsets in callbacks.items()}
 for pc,offsets in gamecallbacks.items():counts[int(pc)]=max(counts.get(int(pc),0),len(offsets))
 newlist=[pc for pc,count in sorted(counts.items()) for _ in range(count)]
 lines+=['std::span<const unsigned>generated_undefined_sites()noexcept{static const auto all=[](){auto b=accepted_generated_undefined_sites();std::vector<unsigned>v;constexpr unsigned n[]{'+','.join(map(str,newlist))+'};std::map<unsigned,unsigned>counts;for(auto pc:b)++counts[pc];std::map<unsigned,unsigned>added;for(auto pc:n)++added[pc];for(auto[pc,num]:added)counts[pc]=std::max(counts[pc],num);for(auto[pc,num]:counts)for(unsigned k=0;k<num;++k)v.push_back(pc);return v;}();return all;}']
 lines+=['unsigned registration_callback(unsigned root)noexcept{switch(root){']+['case '+str(r['entry'])+':return '+str(r['registration']['callback'])+';' for r in gi['roots']]+['default:return accepted_registration_callback(root);}}']
 bodies={v['entry']:v['symbol'] for v in prov['source_bodies'].values()};physical=[]
 for d in dispatch:
  path=pin(d['host_LL'],d['host_sha256']);text=path.read_text();symbol=d['source_function_symbol'];need(re.search(r'^define ptr @'+re.escape(symbol)+r'\(ptr(?: noalias)? %\w+, i32 %\w+, ptr(?: noalias)? %\w+\)',text,re.M),'Exact physical ptr(ptr,i32,ptr) game ABI')
  for level,o in d['objects'].items():need(o['machine']==0x8664 and o['symbol']==symbol and sha(o['path'])==o['sha256'],'Physical game COFF symbol attribution')
  bodies[d['entry']]=symbol;physical.append(d)
 lines+=['extern "C" void*'+symbol+'(State*,unsigned,void*);' for symbol in sorted(set(bodies.values()))]
 lines+=['bool has_body(unsigned pc)noexcept{switch(pc){']+['case '+str(pc)+':return true;' for pc in sorted(bodies)]+['default:return accepted_has_body(pc);}}','void*dispatch_body(unsigned pc,State*s,void*p){switch(pc){']+['case '+str(pc)+':return '+symbol+'(s,pc,p);' for pc,symbol in sorted(bodies.items())]+['default:return accepted_dispatch_body(pc,s,p);}}','}','namespace {']
 (out/'strings_contract.inc').write_text('\n'.join(lines)+'\n')
 h=(out/'locale_batch.hpp').read_text().replace('std::array<mg::Access,1024>api_accesses{};std::array<mg::Event,1024>events{};','std::array<mg::Access,4096>api_accesses{};std::array<mg::Event,8192>events{};')
 needle='bool research_standalone_{};unsigned registry_root_{};'
 addition='struct StringRecord{std::array<std::uint64_t,32>words{};std::vector<std::byte>input;bool operator==(const StringRecord&)const=default;};\n std::vector<StringRecord>string_records_;std::array<std::uint64_t,5>string_copy_probe_{};\n StringRecord*current_string()noexcept;void string_hook(unsigned);void string_called(unsigned,unsigned,unsigned);void string_returned(unsigned,unsigned,unsigned);void string_write_before(unsigned,std::uint64_t,unsigned);void string_write_after(unsigned,unsigned);void dump_strings(CaptureSink,void*)const;\n '
 need(needle in h,'Exact private owner extension point');h=h.replace(needle,addition+needle);(out/'locale_batch.hpp').write_text(h)
 o=(out/'locale_batch_operations.inc').read_text().replace('live_allocations()>16','live_allocations()>32').replace('native_apis_.size()>1024','native_apis_.size()>4096').replace('native_apis_.size()>=1024','native_apis_.size()>=4096')
 o=o.replace('check_source_access(a,v,n,true);','check_source_access(a,v,n,true);string_write_before(a,v,n);',1).replace('expected_store(a,&v,n);source_access(a,v,n,true);','expected_store(a,&v,n);source_access(a,v,n,true);string_write_after(a,n);',1)
 # Exact declared original IAT relocation; no overwrite of the raw guest slot.
 sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage,read_binary
 image=PEImage(read_binary(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')));off,_=image.rva_range(0x5bb670-image.image_base,4);raw=int.from_bytes(image.read(off,4),'little')
 callsites=sorted({r['CALL_pc'] for r in actual_inputs});condition='&&'.join('state.gpr.rip.dword!='+str(p) for p in callsites)
 needle='return v;}\nvoid Binding::write'
 replacement='if(n==4&&a==0x5bb670){if(v!='+str(raw)+'||('+condition+'))deny("Exact string source import relocation",a);research_projections_.push_back({5,state.gpr.rip.dword,a,unsigned(v),0x78010a6d,0,0,0});return 0x78010a6d;}return v;}\nvoid Binding::write'
 need(o.count(needle)==1,'Exact source read IAT extension');o=o.replace(needle,replacement)
 needle='const auto kind=target==probe?1U:0U;'
 need(o.count(needle)==1,'Exact checked literal CALL extension');o=o.replace(needle,'string_called(target,w.pc,w.address);\n '+needle)
 needle='calls_.pop_back();event(50,r.pc,target,r.address);';need(o.count(needle)==1,'Exact checked literal RET extension');o=o.replace(needle,'string_returned(f.entry,state.gpr.rax.dword,f.frame);\n '+needle)
 o=o.replace('object->kind=batch_phase_==3?2:1;','object->kind=batch_phase_==3?2:1;for(const auto&f:calls_)if(f.entry==0x78010a6d)object->kind=3;')
 o=o.replace('auto result=dispatch_body(target,&state,this);','if(target==0x78010a6d)string_called(target,0,frame);auto result=dispatch_body(target,&state,this);',1)
 needle='if(owned_handle_&&!release_noexcept())throw std::runtime_error("Actual heap release failed; private ownership retained");';need(o.count(needle)==1,'Exact whole owner HeapDestroy release point')
 o=o.replace(needle,'if(owned_handle_){if(!release_noexcept())throw std::runtime_error("Actual heap release failed; private ownership retained");destroy_after=measured_api("HeapDestroy",reinterpret_cast<std::uintptr_t>(&::HeapDestroy));if(destroy_before!=destroy_after)throw std::runtime_error("Measured HeapDestroy identity changed across actual complete cleanup");}')
 o+='\n#include "strings_operations.inc"\n';(out/'locale_batch_operations.inc').write_text(o)
 s=(out/'session_impl.inc').read_text()
 # Fresh observation pages for new game objects/string inputs; preserve all old ones.
 prior=re.search(r'constexpr unsigned registry_game_pages\[\]\{([^}]*)\}',contract);need(prior,'Exact parent game page inventory');gamepages=sorted(set(map(int,prior[1].split(',')))|set(gi['source_data_pages']))
 contract=contract[:prior.start(1)]+','.join(map(str,gamepages))+contract[prior.end(1):];(out/'registry_contract.inc').write_text(contract)
 needle='const auto begin=r.memory().load<unsigned>({0x7803788c});auto*a=binding->allocation_for(begin);';need(s.count(needle)==1,'Exact ordinary source cleanup insertion point')
 cleanup='for(auto&owned:binding->owned_allocations_)if(owned->kind==3&&owned->native){const auto oldsp=s.gpr.rsp.dword;const auto sp=oldsp-4;const auto guest=owned->guest;r.memory().store<unsigned>({sp},guest);binding->expected_store(sp,&guest,4);binding->research_accesses_.push_back({s.gpr.rip.dword,sp,guest,4,1});s.gpr.rsp.dword=sp;binding->external_source_call(lb::free_entry,0xffffff70);s.gpr.rsp.dword=oldsp;require(owned->source_freed&&!owned->native,"Genuine source free released still-live duplicated string");}\n    '
 s=s.replace(needle,cleanup+needle)
 s=s.replace('binding->dump(sink,user);','binding->dump(sink,user);binding->dump_strings(sink,user);',1)
 marker=' void finish(){';probe=' void probe_string(unsigned entry,unsigned marker){\n  check();if(!bootstrapped||(entry!=0x78010a6d&&entry!=0x78002f32&&entry!=0x78002fab))throw std::runtime_error("Only literal string probe entries after actual bootstrap");InvocationHostBoundary host;fn::LastErrorBoundary errors;::project(s,r.cpu());fresh_external_pages();activate();\n  try{binding->external_source_call(entry,marker);r.cpu()=::cpu(s);pause();}catch(...){r.cpu()=::cpu(s);poison();throw;}\n }\n'
 need(s.count(marker)==1,'Exact public probe insertion');s=s.replace(marker,probe+marker)
 s+='\nnamespace mw34::m4_onexit {void Session::probe_string(unsigned entry,unsigned marker){impl_->probe_string(entry,marker);}std::vector<std::array<std::uint64_t,32>>Session::string_witnesses()const{std::vector<std::array<std::uint64_t,32>>v;for(const auto&r:impl_->binding->string_records_){auto w=r.words;for(const auto&a:impl_->binding->owned_allocations_)if(a->generation==w[12]){w[18]=a->source_freed;w[19]=a->cleanup_freed;w[28]=a->native!=nullptr;w[29]=a->mapped;}v.push_back(w);}return v;}std::array<std::uint64_t,5>Session::string_copy_probe()const noexcept{return impl_->binding->string_copy_probe_;}}\n';(out/'session_impl.inc').write_text(s)
 h=(out/'session.hpp').read_text().replace('#include <memory>','#include <memory>\n#include <vector>').replace('void finish();void dump','void probe_string(unsigned entry,unsigned marker=0xffffff60);\n std::vector<std::array<std::uint64_t,32>>string_witnesses()const;std::array<std::uint64_t,5>string_copy_probe()const noexcept;\n void finish();void dump');(out/'session.hpp').write_text(h)
 c=(out/'registry_library.cpp').read_text().replace('#include "registry_contract.inc"','#include "registry_contract.inc"\n#include "strings_contract.inc"')
 bridges={v for b in prov['source_bodies'].values() for v in b['bridges']};bridges.update(v for b in game['source_bodies'].values() for v in b['bridges']);existing=set(re.findall(r'extern "C" .+?(\w+)\(',c));extra=[]
 for symbol in sorted(bridges-existing):
  if symbol in {'__remill_read_memory_32','__remill_write_memory_32','__remill_write_memory_8','__remill_function_return'}:continue
  if symbol.endswith('_undefined_8'):extra.append('extern "C" unsigned char '+symbol+'(){return mw34::m4_onexit::undefined();}')
  elif symbol.startswith('sub_') or '_direct_' in symbol:extra.append('extern "C" void*'+symbol+'(State*s,unsigned a,void*p){return mw34::m4_onexit::called(p,s,a);}')
  elif symbol=='__remill_write_memory_16':extra.append('extern \"C\" void*__remill_write_memory_16(void*p,unsigned a,unsigned short v){return mw34::m4_onexit::write(p,a,v,2);}')
  elif symbol=='mw34_onexit_game_write16':extra.append('extern \"C\" void*mw34_onexit_game_write16(void*p,unsigned a,unsigned short v){return mw34::m4_onexit::write(p,a,v,2);}')
  else:raise RuntimeError('Unclassified fresh string bridge '+symbol)
 c+='\n'.join(extra)+'\n';(out/'registry_library.cpp').write_text(c)
 objects=dict(base['entry_objects']);objects.update(prov['entry_objects']);objects.update(game['entry_objects']);need(len(objects)==426,'Immutable342 parent COFF plus84 additive string COFFs')
 for p,h in objects.items():pin(p,h)
 for p,h in base['libraries'].items():pin(p,h)
 (out/'strings-physical-dispatch.json').write_text(json.dumps(dict(provider=prov['source_bodies'],game=physical),indent=2)+'\n')
 witness=['v','index','root','entry','sourceptr','CALLframe','returnPC','NULextent','strlenResult','mallocRequested','ownedGuest','fullNative','generation','roundedExtent','strcpyDest','strcpyResult','committedCopyBytes','strdupReturned','sourceFreed','cleanupFreed','strlenFrame','mallocFrame','strcpyFrame','strdupResult','ledgerStart','ledgerEnd','lastCopyPC','lastCopyAddress','liveNative','mapped','reserved','reserved']
 (out/'strings-interface.json').write_text(json.dumps(dict(witness_words=witness,copy_probe_words=['pc','address','bytes','value','committed_before'],control_points={'50':'strdup entry','51':'strlen RET','52':'strcpy entry','53':'before literal copy write','54':'after committed literal copy write','55':'strdup RET'},source_cleanup='Each kind3 actual source-published duplicate is freed through literal free before registry sourcefree and HeapDestroy; failed sessions retain prefix and use actual owner safeguard',IAT=dict(slot=0x5bb670,raw=raw,target=0x78010a6d,callsites=callsites)),indent=2)+'\n')
 files=dict(deps)
 for p in out.iterdir():
  if p.is_file():files[str(p.absolute())]=sha(p)
 roots=lambda rows:[r['entry'] if isinstance(r,dict) else r for r in rows]
 report=dict(passed=True,schema='mw34-strings-native-preparation-v1',scope='Fresh checked source derivative only; integration and controls pending',parent_acceptance_sha256=sha(ROOT/'reports/m4-joint-startup54-root/acceptance-r1/report.json'),parent_native_preparation_sha256=sha(BASE/'report.json'),entry_objects=objects,libraries=base['libraries'],source_pages=providerpages,game_pages=gamepages,new_roots=[r['entry'] for r in gi['roots']],all_selected_roots=roots(gi['selected_order']),physical_dispatch_entries=sorted(bodies),provider_bodies=3,new_game_bodies=39,native_executed=False,roots_admitted=0,accepted54_files_modified=False,resource_bounds=dict(events=8192,API_accesses=4096,typedAPIs=4096,liveAllocations=32,stringRecords=1024,sourceAccesses=200000),strings_interface_sha256=sha(out/'strings-interface.json'),cleanup_measurement='Additive actual post-HeapDestroy measurement, no changed accepted Binding',files=files)
 (out/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),objects=len(objects),newroots=17)))
if __name__=='__main__':main(sys.argv[1])
