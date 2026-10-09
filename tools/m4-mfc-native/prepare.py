"""Fresh additive MFC owner from immutable accepted71 source/COFF closure."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HOME=Path(__file__).parent
BASE=ROOT/'reports/m4-strings-native/preparation-r5'
PROV=ROOT/'reports/m4-mfc-native/lifts-r1'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p):return json.loads(Path(p).read_bytes())
def need(v,w):
 if not v:raise ValueError(w)


def main(name,recpath,rechash,gamepath,gamehash,attrpath,attrhash,cbpath,cbhash,allocpath,allochash):
 out=ROOT/'reports/m4-mfc-native'/name;need(re.fullmatch('preparation-r[1-9][0-9]*',name)and not out.exists(),'Fresh owned MFC derivative');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact sealed native/source input '+str(p));pins[str(p)]=v;return p
 def receipt(p,h=None):
  v=js(pin(p,h));need(v['passed'],'Successful physical/source preparation')
  for q,d in v['files'].items():pin(q,d)
  return v
 acceptance=js(pin(ROOT/'reports/m4-joint-startup71-root/acceptance-r1/report.json','64c010e01930d4f84d7df9cb8cd932669ce25b6f3f1dc21989f197282025fdfc'));need(acceptance['passed'],'Accepted connected71')
 base=receipt(BASE/'report.json','94382b5470bfe5d6bd1b0bbbabeca69df13c52de5a910c43de606c0db29524bf')
 prov=receipt(PROV/'report.json','3c49ba0a564416ec1c3eb1b3c656f82381947cfd47cabc8a076209246eecf73d')
 pattr=receipt(ROOT/'reports/m4-mfc-native/symbol-attribution-r1/report.json','9c0533366c101555011a098eaf4846d2ca3443bf9f9ba76912a12fb17c4d46c0')
 loader=receipt(ROOT/'reports/m4-mfc-source/loader-identity-r1/report.json','7925f659144954487b1b13d781d4aee48aa0b8d20887ce9ee8aa40ce7a12b09b')
 rec=receipt(recpath,rechash);game=receipt(gamepath,gamehash);attr=receipt(attrpath,attrhash);cb=receipt(cbpath,cbhash);alloc=receipt(allocpath,allochash)
 recdir=Path(recpath).parent;attrdir=Path(attrpath).parent;cbdir=Path(cbpath).parent
 gi=js(pin(recdir/'instruction-contracts.json'));pi=js(pin(PROV/'instruction-contracts.json'))
 inputs=js(pin(Path(allocpath).parent/'allocation-inputs.json'));dispatch=js(pin(attrdir/'physical-dispatch.json'))
 callbacks=js(pin(cbdir/'callbacks.json'))['State_offsets_by_original_PC']
 need(len(gi['roots'])==32 and len(inputs)>=32 and len(pi['instructions'])==23,'Exact32-root MFC family plus all actual source allocation sites')
 need(len({(r['root'],r['CALL_pc'])for r in inputs})==len(inputs),'Distinct genuine per-root allocation sites including multi-allocation constructors')
 need(loader['MFC_handler']['post_loader_value']==loader['MFC_handler']['physical_raw_value']==0xffffffff,'Measured initialized MFC handler is exact raw original input')
 rawmap={r['name']:r for r in loader['bindings']};need(rawmap['malloc']['actual_loader_target']==0x780012b3 and rawmap['free']['actual_loader_target']==0x78001390,'Actual loaded original named CRT exports')
 out.mkdir(parents=True)
 for p in BASE.iterdir():
  if p.suffix in('.cpp','.hpp','.inc'):(out/p.name).write_bytes(p.read_bytes())
 pin(__file__);pin(HOME/'mfc_operations.inc');(out/'mfc_operations.inc').write_bytes((HOME/'mfc_operations.inc').read_bytes())
 old=(out/'strings_contract.inc').read_text()
 for fn in('instruction','source_spans','source_pages','generated_undefined_sites','source_api_contracts','has_body','dispatch_body','registration_callback'):
  old=re.sub(r'\b'+fn+r'\(', 'accepted71_'+fn+'(',old)
 (out/'strings_contract.inc').write_text(old)
 rows={r['pc']:r for r in gi['instructions']};rows.update({r['pc']:r for r in pi['instructions']})
 regs={r:i for i,r in enumerate(['','eax','ecx','edx','ebx','esp','ebp','esi','edi','al','cl','dl','bl','ah','ch','dh','bh','ax','cx','dx','bx','sp','bp','si','di'])}
 def operand(r,i,x):
  k=x['kind'];bits=x.get('bits',0)or next((v.get('bits',0)for v in r['decoded_operands']if v.get('bits',0)),32)
  if k=='register':return '{'+f'1,{bits//8},{regs[x["register"]]},0,0,0,1,0,0,1'+'}'
  if k=='immediate':return '{'+f'2,{bits//8},0,0,0,0,1,0,{x["value"]&0xffffffffffffffff}ULL,1'+'}'
  need(k=='memory','Integer MFC source operands');base=index=0;scale=1
  for t in x['terms']:
   if not base and t['scale']==1:base=regs[t['register']]
   else:index=regs[t['register']];scale=t['scale']
  disp=x['displacement'];disp=disp if disp<2**31 else disp-2**32;access=int(i in r['explicit_memory_reads'])+2*int(i in r['explicit_memory_writes'])
  return '{'+f'3,{bits//8},0,{int(x["segment"]=="fs")},{base},{index},{scale},{disp},0,{access}'+'}'
 local=js(pin(ROOT/'reports/m4-strings-native/next-mfc-r1/provider-local.json','67b6e3f0402a2c148b00ed4ab120578f2dd59940b864e67c8046cef582bea9fd'))
 callsites=sorted({r['pc']for r in gi['instructions']if r['decoded_operands']and any(x['kind']=='memory'and x['displacement']==0x5bb4bc and not x['terms']for x in r['decoded_operands'])})
 lines=['} // anonymous composition namespace','namespace mw34::m4_crt_locale_batch {','namespace {',
        'constexpr unsigned mfc_allocate_entry=0x5f401ea0,mfc_free_entry=0x5f401782,mfc_image_base=0x5f400000,mfc_image_size=0xed000;',
        f'constexpr unsigned mfc_raw_malloc={rawmap["malloc"]["raw_bound_IAT"]},mfc_raw_free={rawmap["free"]["raw_bound_IAT"]},mfc_handler=0xffffffff,mfc_game_iat=0x5bb4bc,mfc_game_raw={local["game_IAT"]["raw_bound"]};',
        'struct MfcRootInput{unsigned root,call,request,object,publication;};','constexpr MfcRootInput mfc_inputs[]{']
 for r in inputs:lines.append('{'+','.join(str(r[k])for k in('root','CALL_pc','requested_size','object','publication'))+'},')
 lines+=['};','const MfcRootInput*mfc_root_input(unsigned root,unsigned call)noexcept{for(const auto&i:mfc_inputs)if(i.root==root&&i.call==call)return &i;return nullptr;}',
         'bool mfc_callsite(unsigned pc)noexcept{switch(pc){'+''.join('case '+str(pc)+':return true;'for pc in callsites)+'default:return false;}}','constexpr SourceInstruction mfc_instructions[]{']
 for pc,r in sorted(rows.items()):
  ops=r['decoded_operands'];need(len(ops)<=3,'Finite source operands');rep={None:0,'rep':1,'repe':2,'repz':2,'repne':3,'repnz':3}.get(r.get('repeat'),0)
  lines.append('{'+f'{pc},{r["width"]},{json.dumps(r["mnemonic"])},{{{{'+','.join([operand(r,i,x)for i,x in enumerate(ops)]+['{}']*(3-len(ops)))+'}},'+f'{len(ops)},{rep}'+'},')
 spans=[];raw=bytearray();start=end=None
 for pc,r in sorted(rows.items()):
  if start is not None and pc!=end:spans.append((start,end,bytes(raw)));start=None;raw=bytearray()
  if start is None:start=pc
  raw.extend(bytes.fromhex(r['bytes_hex']));end=pc+r['width']
 if start is not None:spans.append((start,end,bytes(raw)))
 lines+=['};','constexpr SourceSpan mfc_spans[]{']+['{'+f'{a},{b-a},5,"{hashlib.sha256(raw).hexdigest()}"'+'},'for a,b,raw in spans]+['};','}']
 pages={int(p):v for p,v in base['source_pages'].items()};pages.update({0x5f401000:5,0x5f498000:1})
 lines+=['const SourceInstruction*instruction(unsigned pc)noexcept{auto it=std::lower_bound(std::begin(mfc_instructions),std::end(mfc_instructions),pc,[](const auto&i,unsigned p){return i.pc<p;});return it!=std::end(mfc_instructions)&&it->pc==pc?it:accepted71_instruction(pc);}',
         'std::span<const SourceSpan>source_spans()noexcept{static const auto all=[](){auto b=accepted71_source_spans();std::vector<SourceSpan>v(b.begin(),b.end());v.insert(v.end(),std::begin(mfc_spans),std::end(mfc_spans));return v;}();return all;}',
         'std::span<const SourcePage>source_pages()noexcept{static const SourcePage p[]{'+','.join('{'+f'{p},{v}'+'}'for p,v in sorted(pages.items()))+'};return p;}',
         'std::span<const SourceApi>source_api_contracts()noexcept{return accepted71_source_api_contracts();}']
 counts={int(pc):len(offsets)for pc,offsets in js(PROV/'callbacks.json')['State_offsets_by_original_PC'].items()}
 for pc,offsets in callbacks.items():counts[int(pc)]=max(counts.get(int(pc),0),len(offsets))
 newlist=[pc for pc,count in sorted(counts.items())for _ in range(count)]
 lines+=['std::span<const unsigned>generated_undefined_sites()noexcept{static const auto all=[](){auto b=accepted71_generated_undefined_sites();std::vector<unsigned>v;constexpr unsigned n[]{'+','.join(map(str,newlist))+'};std::map<unsigned,unsigned>counts;for(auto pc:b)++counts[pc];std::map<unsigned,unsigned>added;for(auto pc:n)++added[pc];for(auto[pc,num]:added)counts[pc]=std::max(counts[pc],num);for(auto[pc,num]:counts)for(unsigned k=0;k<num;++k)v.push_back(pc);return v;}();return all;}']
 lines+=['unsigned registration_callback(unsigned root)noexcept{switch(root){']+['case '+str(r['entry'])+':return '+str(r['registration']['callback'])+';'for r in gi['roots']]+['default:return accepted71_registration_callback(root);}}']
 bodies={v['entry']:v['symbol']for v in prov['source_bodies'].values()};physical=[]
 for d in dispatch:
  path=pin(d['host_LL'],d['host_sha256']);symbol=d['source_function_symbol'];need(re.search(r'^define ptr @'+re.escape(symbol)+r'\(ptr(?: noalias)? %\w+, i32 %\w+, ptr(?: noalias)? %\w+\)',path.read_text(),re.M),'Exact physical game body ABI')
  for level,o in d['objects'].items():need(o['machine']==0x8664 and o['symbol']==symbol and sha(o['path'])==o['sha256'],'Physical AMD64 game body export')
  bodies[d['entry']]=symbol;physical.append(d)
 lines+=['extern "C" void*'+s+'(State*,unsigned,void*);'for s in sorted(set(bodies.values()))]
 lines+=['bool has_body(unsigned pc)noexcept{switch(pc){']+['case '+str(pc)+':return true;'for pc in sorted(bodies)]+['default:return accepted71_has_body(pc);}}',
         'void*dispatch_body(unsigned pc,State*s,void*p){switch(pc){']+['case '+str(pc)+':return '+s+'(s,pc,p);'for pc,s in sorted(bodies.items())]+['default:return accepted71_dispatch_body(pc,s,p);}}','}','namespace {']
 (out/'mfc_contract.inc').write_text('\n'.join(lines)+'\n')
 h=(out/'locale_batch.hpp').read_text();needle='bool research_standalone_{};unsigned registry_root_{};'
 addon='struct MfcRecord{std::array<std::uint64_t,32>words{};bool operator==(const MfcRecord&)const=default;};std::vector<MfcRecord>mfc_records_;std::vector<std::array<std::uint64_t,8>>mfc_imports_,mfc_stores_;std::array<std::uint64_t,8>mfc_store_probe_{};unsigned mfc_free_active_{};\n MfcRecord*current_mfc()noexcept;MfcRecord*mfc_for_generation(unsigned)noexcept;void mfc_hook(unsigned);void mfc_called(unsigned,unsigned,unsigned);std::uint64_t mfc_read(unsigned,std::uint64_t,unsigned);void mfc_returned(unsigned,unsigned,unsigned);void mfc_write_before(unsigned,std::uint64_t,unsigned);void mfc_write_after(unsigned,std::uint64_t,unsigned);void dump_mfc(CaptureSink,void*)const;\n '
 need(h.count(needle)==1,'Exact private owner extension');h=h.replace(needle,addon+needle);(out/'locale_batch.hpp').write_text(h)
 live_bound=((17+len(inputs)+15)//16)*16
 o=(out/'locale_batch_operations.inc').read_text().replace('live_allocations()>32','live_allocations()>'+str(live_bound))
 o=o.replace('string_write_before(a,v,n);','string_write_before(a,v,n);mfc_write_before(a,v,n);',1).replace('string_write_after(a,n);','string_write_after(a,n);mfc_write_after(a,v,n);',1)
 needle='return v;}\nvoid Binding::write';need(o.count(needle)==1,'Exact source-read extension');o=o.replace(needle,'return mfc_read(a,v,n);}\nvoid Binding::write')
 o=o.replace('string_called(target,w.pc,w.address);','string_called(target,w.pc,w.address);mfc_called(target,w.pc,w.address);',1)
 o=o.replace('string_returned(f.entry,state.gpr.rax.dword,f.frame);','string_returned(f.entry,state.gpr.rax.dword,f.frame);mfc_returned(f.entry,state.gpr.rax.dword,f.frame);',1)
 o=o.replace('if(f.entry==0x78010a6d)object->kind=3;','if(f.entry==0x78010a6d)object->kind=3;for(const auto&f:calls_)if(f.entry==mfc_allocate_entry)object->kind=4;',1)
 needle='if(target==0x78010a6d)string_called(target,0,frame);';need(o.count(needle)==1,'Exact research-call extension');o=o.replace(needle,needle+'if(target==mfc_allocate_entry||target==mfc_free_entry)mfc_called(target,0,frame);')
 needle='for(const auto&a:source_api_contracts())if(a.raw==target&&a.tail)';need(o.count(needle)==1,'Exact original tail-dispatch extension')
 tail='if(target==mfc_allocate_entry){const auto&r=source_accesses_.back();auto&f=calls_.back();if(r.pc!=0x5abd26||r.address!=mfc_game_iat||r.value!=mfc_game_raw||f.entry!=0x5abd26)deny("Actual MFC ordinal823 game thunk tail import",target);mfc_called(target,f.site,f.frame);f.entry=target;return dispatch_body(target,s,this);}\n if(target==0x5f41b01e){auto*r=current_mfc();if(!r||r->words[20]||r->words[16]||!r->words[12])deny("Exact genuine MFC null allocator branch",target);deny("Genuine MFC null allocation TLS/handler frontier remains unrecovered",target);}\n '
 o=o.replace(needle,tail+needle);o+='\n#include "mfc_operations.inc"\n';(out/'locale_batch_operations.inc').write_text(o)
 contract=(out/'registry_contract.inc').read_text();m=re.search(r'constexpr unsigned registry_game_pages\[\]\{([^}]*)\}',contract);need(m,'Exact old game pages');gamepages=sorted(set(map(int,m[1].split(',')))|set(gi['source_data_pages']));contract=contract[:m.start(1)]+','.join(map(str,gamepages))+contract[m.end(1):];(out/'registry_contract.inc').write_text(contract)
 c=(out/'registry_library.cpp').read_text().replace('#include "strings_contract.inc"','#include "strings_contract.inc"\n#include "mfc_contract.inc"')
 rawpage='std::array<std::byte,4096> mfc_raw_page(std::span<const std::byte>file,unsigned address){\n require(m4::sha256(file)=="5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8","Exact MFC source image");auto dw=[&](unsigned p){require(std::uint64_t(p)+4<=file.size(),"MFC PE DWORD bounds");unsigned v{};std::memcpy(&v,file.data()+p,4);return v;};auto sw=[&](unsigned p){require(std::uint64_t(p)+2<=file.size(),"MFC PE WORD bounds");unsigned short v{};std::memcpy(&v,file.data()+p,2);return v;};const auto pe=dw(60),opt=pe+24;require(dw(opt+28)==0x5f400000&&dw(opt+56)==0xed000,"Exact MFC preferred source extent");std::array<std::byte,4096>b{};unsigned matches{};for(unsigned i=0;i<sw(pe+6);++i){const auto s=opt+sw(pe+20)+40*i,rva=dw(s+12),size=dw(s+16),raw=dw(s+20),wanted=address-0x5f400000;if(wanted>=rva&&std::uint64_t(wanted)+4096<=std::uint64_t(rva)+size){require((dw(s+36)&0x40000000)&&std::uint64_t(raw)+wanted-rva+4096<=file.size(),"Bounded readable literal MFC page");std::memcpy(b.data(),file.data()+raw+wanted-rva,4096);++matches;}}require(matches==1,"Unique literal MFC source-backed page");return b;}\n'
 c=c.replace('struct MatherrBinding {',rawpage+'struct MatherrBinding {',1)
 bridges={v for b in prov['source_bodies'].values()for v in b['bridges']}|{v for b in game['source_bodies'].values()for v in b['bridges']};existing=set(re.findall(r'extern "C" .+?(\w+)\(',c));extra=[]
 for symbol in sorted(bridges-existing):
  if symbol in {'__remill_read_memory_32','__remill_write_memory_32','__remill_write_memory_8','__remill_write_memory_16','__remill_function_call','__remill_function_return','__remill_missing_block'}:continue
  if symbol.endswith('_undefined_8'):extra.append('extern "C" unsigned char '+symbol+'(){return mw34::m4_onexit::undefined();}')
  elif symbol.startswith('sub_')or '_direct_'in symbol:extra.append('extern "C" void*'+symbol+'(State*s,unsigned a,void*p){return mw34::m4_onexit::called(p,s,a);}')
  else:raise ValueError('Unclassified fresh MFC bridge '+symbol)
 c+='\n'.join(extra)+'\n';(out/'registry_library.cpp').write_text(c)
 s=(out/'session_impl.inc').read_text().replace('std::vector<std::byte>provider;','std::vector<std::byte>provider,mfc_provider;')
 s=s.replace('std::span<const std::byte>raw):self(session)','std::span<const std::byte>raw,std::span<const std::byte>mfc):self(session)').replace('provider(raw.begin(),raw.end()){','provider(raw.begin(),raw.end()),mfc_provider(mfc.begin(),mfc.end()){')
 s=s.replace('const auto original=provider_raw_page(provider,p.address);','const auto original=p.address>=lb::mfc_image_base&&p.address<lb::mfc_image_base+lb::mfc_image_size?mfc_raw_page(mfc_provider,p.address):provider_raw_page(provider,p.address);')
 s=s.replace('if(address<0x78000000&&address<0x31000000)','if(address<0x78000000&&address<0x31000000&&!(address>=lb::mfc_image_base&&address<lb::mfc_image_base+lb::mfc_image_size))')
 needle='for(auto&owned:binding->owned_allocations_)if(owned->kind==3&&owned->native)';need(s.count(needle)==1,'Exact source object cleanup insertion')
 cleanup='for(auto&owned:binding->owned_allocations_)if(owned->kind==4&&owned->native){const auto oldsp=s.gpr.rsp.dword,sp=oldsp-4,guest=owned->guest;r.memory().store<unsigned>({sp},guest);binding->expected_store(sp,&guest,4);binding->research_accesses_.push_back({s.gpr.rip.dword,sp,guest,4,1});s.gpr.rsp.dword=sp;binding->external_source_call(lb::mfc_free_entry,0xffffff50);s.gpr.rsp.dword=oldsp;require(owned->source_freed&&!owned->native,"Genuine MFC825 then literal CRTfree released whole MFC object");}\n    '
 s=s.replace(needle,cleanup+needle).replace('binding->dump_strings(sink,user);','binding->dump_strings(sink,user);binding->dump_mfc(sink,user);')
 probe=' void probe_mfc(unsigned entry,unsigned marker){\n  check();if(!bootstrapped||(entry!=lb::mfc_allocate_entry&&entry!=lb::mfc_free_entry))throw std::runtime_error("Only original MFC823/825 research entries after bootstrap");InvocationHostBoundary host;fn::LastErrorBoundary errors;::project(s,r.cpu());fresh_external_pages();activate();\n  try{binding->external_source_call(entry,marker);r.cpu()=::cpu(s);pause();}catch(...){r.cpu()=::cpu(s);poison();throw;}\n }\n'
 need(s.count(' void finish(){')==1,'Exact additive MFC research-call entry');s=s.replace(' void finish(){',probe+' void finish(){',1)
 s=s.replace('}catch(...){pause();throw;}\n }\n void dump','}catch(...){poison();throw;}\n }\n void dump',1)
 needle='std::make_unique<SessionImpl>(*this,r,provider)';need(s.count(needle)==1,'Exact public Session implementation constructor')
 s=s.replace(needle,'std::make_unique<SessionImpl>(*this,r,provider,std::span<const std::byte>{})')
 s+='\nnamespace mw34::m4_onexit {Session::Session(m4_runtime::Runtime&r,std::span<const std::byte>crt,std::span<const std::byte>mfc):impl_(std::make_unique<SessionImpl>(*this,r,crt,mfc)){}void Session::probe_mfc(unsigned entry,unsigned marker){impl_->probe_mfc(entry,marker);}std::vector<std::array<std::uint64_t,32>>Session::mfc_witnesses()const{std::vector<std::array<std::uint64_t,32>>v;for(const auto&r:impl_->binding->mfc_records_){auto w=r.words;for(const auto&a:impl_->binding->owned_allocations_)if(a->generation==w[18]){w[30]=a->source_freed;w[31]=a->cleanup_freed;}v.push_back(w);}return v;}std::array<std::uint64_t,8>Session::mfc_store_probe()const noexcept{return impl_->binding->mfc_store_probe_;}}\n';(out/'session_impl.inc').write_text(s)
 h=(out/'session.hpp').read_text().replace('Session(m4_runtime::Runtime&,std::span<const std::byte>);','Session(m4_runtime::Runtime&,std::span<const std::byte>);\n Session(m4_runtime::Runtime&,std::span<const std::byte>,std::span<const std::byte>);\n void probe_mfc(unsigned entry,unsigned marker=0xffffff40);\n std::vector<std::array<std::uint64_t,32>>mfc_witnesses()const;std::array<std::uint64_t,8>mfc_store_probe()const noexcept;');(out/'session.hpp').write_text(h)
 objects=dict(base['entry_objects']);objects.update(prov['entry_objects']);objects.update(game['entry_objects'])
 for p,h in objects.items():pin(p,h)
 for p,h in base['libraries'].items():pin(p,h)
 interface=dict(witness_words=['v','index','root','entry','callerSite','frame','returnPC','request','mallocRawIAT','mallocTarget','mallocReadPC','mallocCallPC','mallocFrame','mallocRequest','handlerReadPC','handlerValue','ownedGuest','fullNative','generation','roundedExtent','allocatorResult','allocatorReturned','entryECX','publicationCount','objectStoreBytes','freeEntry','freeFrame','freeCALLframe','freeRawIAT','freeTarget','sourceFreed','cleanupFreed'],import_words=['v','index','root','pc','address','raw','projected','kind'],store_words=['v','index','root','pc','address','bytes','value','kind'],hooks={'70':'MFCentry','71':'before literal CALL EBX frame commit','72':'genuine mallocRET','73':'before object/publication store','74':'after committed store','75':'MFCallocatorRET','76':'genuine MFC825→CRTfree dispatch','77':'genuine MFC825RET'},normal_allocation_count=len(inputs),live_owner_bound=live_bound,normal_live_owners=17+len(inputs),MFC_pages=[0x5f401000,0x5f498000],loader_identity_sha256=sha(ROOT/'reports/m4-mfc-source/loader-identity-r1/report.json'),null_frontier=0x5f41b01e)
 (out/'mfc-interface.json').write_text(json.dumps(interface,indent=2)+'\n');(out/'mfc-physical-dispatch.json').write_text(json.dumps(dict(provider=prov['source_bodies'],game=physical),indent=2)+'\n')
 files=dict(pins)
 for p in out.iterdir():
  if p.is_file():files[str(p.resolve())]=sha(p)
 report=dict(passed=True,schema='mw34-mfc-native-preparation-v1',scope='Fresh derivative static library/interface/COFF closure; connected103 build/capture/review pending',parent_acceptance_sha256=sha(ROOT/'reports/m4-joint-startup71-root/acceptance-r1/report.json'),parent_native_preparation_sha256=sha(BASE/'report.json'),entry_objects=objects,libraries=base['libraries'],source_pages=pages,game_pages=gamepages,new_roots=[r['entry']for r in gi['roots']],all_selected_roots=[r['entry']if isinstance(r,dict)else r for r in gi['selected_order']],physical_dispatch_entries=sorted(bodies),provider_bodies=2,new_game_bodies=len(dispatch),normal_MFC_allocations=len(inputs),normal_live_owners=17+len(inputs),native_executed=False,roots_admitted=0,accepted71_files_modified=False,resource_bounds=dict(liveAllocations=live_bound,events=8192,typedAPIs=4096,sourceAccesses=200000,MfcRecords=512,MfcStoreRows=8192),files=files)
 (out/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),objects=len(objects),game_bodies=len(dispatch),MFC_allocations=len(inputs))))


if __name__=='__main__':main(*sys.argv[1:])
