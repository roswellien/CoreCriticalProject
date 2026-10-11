"""Add four literal Lockit roots and the observed initialized provider domain."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
BASE=ROOT/'reports/m4-vtable-native/preparation-r4'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def one(s,a,b):need(s.count(a)==1,'One derivative anchor '+a[:100]);return s.replace(a,b)
def main(name,provider_lifts_path,provider_lifts_sha,provider_interface_path,provider_interface_sha):
 out=ROOT/'reports/m4-lockit-native'/name;need(not out.exists(),'Fresh preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'No physical pin conflicts');pins[str(p)]=v;return p
 def receipt(p,h=None):
  r=json.loads(pin(p,h).read_bytes());need(r['passed'],'Passed input');
  for q,v in r.get('files',{}).items():pin(q,v)
  return r
 parent=receipt(ROOT/'reports/m4-joint-startup120-root/acceptance-r1/report.json','e640ff4eaa068a039a5e810ad99b4c0ca0336821b8b1a6f33f81012ad43ed0ee')
 need(parent['connected_roots']==120,'Accepted120 parent')
 base=receipt(BASE/'report.json','b52c62a1ec6e1306a9629f53fbe80621be96404907d322efbbeef136ec10ee93')
 rec=receipt(ROOT/'reports/m4-lockit-source/recovery-r1/report.json','25a04a5a9e4cec894c5272d398794850aeab968a22f77b21494706680015fa4d')
 lift=receipt(ROOT/'reports/m4-lockit-source/lifts-r1/report.json','044316594ce299d04ff9e3aac5bd3bbc157c5ed758f7693db0238c1d727dcb0d')
 pl=receipt(provider_lifts_path,provider_lifts_sha)
 pi=receipt(provider_interface_path,provider_interface_sha)
 receipt(ROOT/'reports/m4-lockit-source/symbol-attribution-r1/report.json','7b9388578825ad9bf2a5028a7213a23fbb9e2e328f633e71947e05d1790d5952')
 receipt(ROOT/'reports/m4-lockit-source/game-callbacks-r1/report.json','b955ca73bfa5bcaa2caac56e70f8b3f56542232639d11d4754666aadcb7a7200')
 receipt(ROOT/'reports/m4-lockit-review/static-r1/report.json','e8ad1f6dcd34c63fb08f984299d698a0ae020422cde4a73b2f5794a0a1bfba35')
 gi=json.loads(pin(ROOT/'reports/m4-lockit-source/recovery-r1/instruction-contracts.json').read_bytes());dispatch=json.loads(pin(ROOT/'reports/m4-lockit-source/symbol-attribution-r1/physical-dispatch.json').read_bytes());callbacks=json.loads(pin(ROOT/'reports/m4-lockit-source/game-callbacks-r1/callbacks.json').read_bytes())['State_offsets_by_original_PC']
 loaded=json.loads(pin(ROOT/'reports/m4-lockit-original/loader-execution-r1/observations.json').read_bytes());need(loaded['post_DllMain_state']==2 and not loaded['state_seeded'],'Genuine loaded state2')
 inputpage=pin(ROOT/'reports/m4-lockit-original/loader-execution-r1/post-DllMain-78145000-page.bin');data=inputpage.read_bytes();need(len(data)==4096 and int.from_bytes(data[0x658:0x65c],'little')==2,'Complete observed data input')
 out.mkdir(parents=True)
 for p in BASE.iterdir():
  if p.suffix in('.cpp','.hpp','.inc'):(out/p.name).write_bytes(p.read_bytes())
 pin(__file__);pin(HERE/'lockit_operations.inc');(out/'lockit_operations.inc').write_bytes((HERE/'lockit_operations.inc').read_bytes())
 wrappers=('instruction','source_spans','source_pages','generated_undefined_sites','has_body','dispatch_body','registration_callback','fs_root','fs_frame_read','fs_frame_install','fs_frame_restore','fs_frame_entry')
 s=(out/'vtable_contract.inc').read_text()
 for fn in wrappers:s=re.sub(r'\b'+fn+r'\(', 'accepted120_'+fn+'(',s)
 (out/'vtable_contract.inc').write_text(s)
 s=(out/'container_contract.inc').read_text()
 for fn in('mfc_root_input','source_api_contracts'):s=re.sub(r'\b'+fn+r'\(', 'accepted120_'+fn+'(',s)
 (out/'container_contract.inc').write_text(s)
 regs={r:i for i,r in enumerate(['','eax','ecx','edx','ebx','esp','ebp','esi','edi','al','cl','dl','bl','ah','ch','dh','bh','ax','cx','dx','bx','sp','bp','si','di'])}
 def operand(r,i,x):
  kind=x['kind'];bits=x.get('bits',0)or next((v.get('bits',0)for v in r['decoded_operands']if v.get('bits',0)),32)
  if kind=='register':return '{'+f'1,{bits//8},{regs[x["register"]]},0,0,0,1,0,0,1'+'}'
  if kind=='immediate':return '{'+f'2,{bits//8},0,0,0,0,1,0,{x["value"]&0xffffffffffffffff}ULL,1'+'}'
  need(kind=='memory','Decoded integer operand');base_reg=index=0;scale=1
  for term in x['terms']:
   if not base_reg and term['scale']==1:base_reg=regs[term['register']]
   else:index=regs[term['register']];scale=term['scale']
  d=x['displacement'];d=d if d<2**31 else d-2**32;access=int(i in r['explicit_memory_reads'])+2*int(i in r['explicit_memory_writes'])
  return '{'+f'3,{bits//8},0,{int(x["segment"]=="fs")},{base_reg},{index},{scale},{d},0,{access}'+'}'
 provider_contract=pi['instruction_contracts'];provider=json.loads(pin(provider_contract,pi['instruction_contracts_sha256']).read_bytes())
 rows={r['pc']:r for r in gi['instructions']};rows.update({r['pc']:r for r in provider['instructions']});need(len(provider['instructions'])==17,'Observed initialized provider17 rows')
 lr={r['entry']:r for r in gi['roots']};calls=gi['Lockit_calls'];lines=['} // composition anonymous namespace','namespace mw34::m4_crt_locale_batch {','namespace {','struct LockitInput{unsigned root,ctor,dtor,ctor_offset,dtor_offset;};constexpr LockitInput lockit_inputs[]{']
 for root in lr:
  cs=[c for c in calls if c['root']==root];ctor=next(c for c in cs if c['kind']=='constructor');dtor=next(c for c in cs if c['kind']=='destructor')
  offsets=provider['game_scratch_offsets'][str(root)];lines.append('{'+','.join(map(str,(root,ctor['CALL_pc'],dtor['CALL_pc'],offsets['constructor'],offsets['destructor'])))+'},')
 lines+=['};','const LockitInput*lockit_input(unsigned root)noexcept{for(const auto&i:lockit_inputs)if(i.root==root)return &i;return nullptr;}','const std::array<std::byte,4096>lockit_loaded_page{'+','.join('std::byte{'+str(v)+'}'for v in data)+'};','constexpr FsFrameSpec lockit_frames[]{']
 lines+=['{'+','.join(str(f[k])for k in('entry','handler','read','install','saved','restore','ret'))+'},'for f in gi['FS_frame_contracts']]+['};','constexpr MfcRootInput lockit_mfc_inputs[]{']
 for a in gi['allocations']:
  root=a['root'];obj=lr[root]['objects'][0]['address'];address=a['header_global']if a['conditional']else obj+4;lines.append('{'+','.join(map(str,(root,a['CALL_pc'],a['requested'],obj,address)))+'},')
 lines+=['};','constexpr SourceInstruction lockit_instructions[]{']
 for pc,r in sorted(rows.items()):
  ops=r['decoded_operands'];need(len(ops)<=3,'Finite operand count');rep={None:0,'rep':1,'repe':2,'repz':2,'repne':3,'repnz':3}.get(r.get('repeat'),0)
  lines.append('{'+f'{pc},{r["width"]},{json.dumps(r["mnemonic"])},{{{{'+','.join([operand(r,i,x)for i,x in enumerate(ops)]+['{}']*(3-len(ops)))+'}},'+f'{len(ops)},{rep}'+'},')
 spans=[];raw=bytearray();start=end=None
 for pc,r in sorted(rows.items()):
  if start is not None and pc!=end:spans.append((start,end,bytes(raw)));start=None;raw=bytearray()
  if start is None:start=pc
  raw.extend(bytes.fromhex(r['bytes_hex']));end=pc+r['width']
 if start is not None:spans.append((start,end,bytes(raw)))
 lines+=['};','constexpr SourceSpan lockit_spans[]{']+['{'+f'{a},{b-a},5,"{hashlib.sha256(raw).hexdigest()}"'+'},'for a,b,raw in spans]+['};','}']
 for field in('read','install','restore','entry'):lines.append(f'const FsFrameSpec*fs_frame_{field}(unsigned pc)noexcept{{for(const auto&i:lockit_frames)if(i.{field}==pc)return &i;return accepted120_fs_frame_{field}(pc);}}')
 pages={int(k):v for k,v in base['source_pages'].items()};pages.update({0x7810a000:5,0x78145000:3,0x78146000:3})
 lines+=['const MfcRootInput*mfc_root_input(unsigned root,unsigned site)noexcept{for(const auto&i:lockit_mfc_inputs)if(i.root==root&&i.call==site)return &i;return accepted120_mfc_root_input(root,site);}',
 'std::span<const SourceApi>source_api_contracts()noexcept{static const auto all=[](){auto b=accepted120_source_api_contracts();std::vector<SourceApi>v(b.begin(),b.end());v.push_back({0x7810a30b,0x78146198,0x866ae,1,"EnterCriticalSection",0});v.push_back({0x7810a35e,0x78146184,0x86718,1,"LeaveCriticalSection",0});return v;}();return all;}',
 'bool fs_root(unsigned root)noexcept{return lockit_input(root)||accepted120_fs_root(root);}',
 'const SourceInstruction*instruction(unsigned pc)noexcept{auto it=std::lower_bound(std::begin(lockit_instructions),std::end(lockit_instructions),pc,[](const auto&i,unsigned p){return i.pc<p;});return it!=std::end(lockit_instructions)&&it->pc==pc?it:accepted120_instruction(pc);}',
 'std::span<const SourceSpan>source_spans()noexcept{static const auto all=[](){auto b=accepted120_source_spans();std::vector<SourceSpan>v(b.begin(),b.end());v.insert(v.end(),std::begin(lockit_spans),std::end(lockit_spans));return v;}();return all;}',
 'std::span<const SourcePage>source_pages()noexcept{static const SourcePage p[]{'+','.join('{'+f'{p},{v}'+'}'for p,v in sorted(pages.items()))+'};return p;}']
 added=[int(pc)for pc,count in callbacks.items()for _ in count]
 lines+=['std::span<const unsigned>generated_undefined_sites()noexcept{static const auto all=[](){auto b=accepted120_generated_undefined_sites();std::map<unsigned,unsigned>counts,added;std::vector<unsigned>v;constexpr unsigned n[]{'+','.join(map(str,added))+'};for(auto pc:b)++counts[pc];for(auto pc:n)++added[pc];for(auto[pc,num]:added)counts[pc]=std::max(counts[pc],num);for(auto[pc,num]:counts)for(unsigned k=0;k<num;++k)v.push_back(pc);return v;}();return all;}','unsigned registration_callback(unsigned root)noexcept{switch(root){']+['case '+str(r['entry'])+':return '+str(r['normal']['registration']['callback'])+';'for r in gi['roots']]+['default:return accepted120_registration_callback(root);}}']
 bodies={d['entry']:d['source_function_symbol']for d in dispatch};bodies.update({b['entry']:b['symbol']+'_body'for b in pl['source_bodies'].values()})
 lines+=['extern "C" void*'+s+'(State*,unsigned,void*);'for s in sorted(set(bodies.values()))]+['bool has_body(unsigned pc)noexcept{switch(pc){']+['case '+str(pc)+':return true;'for pc in sorted(bodies)]+['default:return accepted120_has_body(pc);}}','void*dispatch_body(unsigned pc,State*s,void*p){switch(pc){']+['case '+str(pc)+':return '+s+'(s,pc,p);'for pc,s in sorted(bodies.items())]+['default:return accepted120_dispatch_body(pc,s,p);}}','}','namespace {'];(out/'lockit_contract.inc').write_text('\n'.join(lines)+'\n')
 h=(out/'locale_batch.hpp').read_text();needle='bool research_standalone_{};unsigned registry_root_{};';addon='bool lockit_admitted_{};unsigned lockit_generation_{};std::vector<std::byte>lockit_source_cs_;std::vector<std::array<std::uint64_t,8>>lockit_imports_;std::vector<std::array<std::uint64_t,16>>lockit_calls_;std::vector<std::array<std::byte,40>>lockit_native_images_;void lockit_bootstrap();void lockit_guard();std::uint64_t lockit_read(unsigned,std::uint64_t,unsigned);void lockit_called(unsigned,unsigned,unsigned);void lockit_returned(unsigned,unsigned,unsigned);void lockit_section_after(unsigned);void dump_lockit(CaptureSink,void*)const;\n '
 (out/'locale_batch.hpp').write_text(one(h,needle,addon+needle))
 s=(out/'locale_batch_binding.inc').read_text();needle='void Binding::stable_hook(unsigned point,bool terminal,bool cleaning){';snapshot='const auto lockit_calls=lockit_calls_;const auto lockit_imports=lockit_imports_;const auto lockit_images=lockit_native_images_;const auto lockit_cs=lockit_source_cs_;const auto lockit_generation=lockit_generation_;const auto lockit_admitted=lockit_admitted_;std::array<std::byte,40>lockit_native{};for(const auto&p:owned_sections_)if(p->guest==0x78145640)std::memcpy(lockit_native.data(),&p->native,40);';s=one(s,needle,needle+snapshot);needle='hook(point);admit_current();';guard='if(lockit_calls!=lockit_calls_||lockit_imports!=lockit_imports_||lockit_images!=lockit_native_images_||lockit_cs!=lockit_source_cs_||lockit_generation!=lockit_generation_||lockit_admitted!=lockit_admitted_)deny("Lockit observer changed private resource/source witnesses",0x78145640);for(const auto&p:owned_sections_)if(p->guest==0x78145640&&std::memcmp(lockit_native.data(),&p->native,40))deny("Lockit observer changed actual native resource bytes",0x78145640);';s=one(s,needle,needle+guard);(out/'locale_batch_binding.inc').write_text(s)
 s=(out/'locale_batch_operations.inc').read_text();s=one(s,'void Binding::batch_guard(){container_guard();','void Binding::batch_guard(){lockit_guard();container_guard();');s=one(s,'return mfc_read(a,v,n);','return lockit_read(a,mfc_read(a,v,n),n);');s=one(s,'vtable_called(target,w.pc,w.address);','lockit_called(target,w.pc,w.address);vtable_called(target,w.pc,w.address);');s=one(s,'vtable_returned(f.entry,state.gpr.rax.dword,f.frame);','lockit_returned(f.entry,state.gpr.rax.dword,f.frame);vtable_returned(f.entry,state.gpr.rax.dword,f.frame);');s=one(s,'api.words[14]=1;api.words[18]=section->depth;','api.words[14]=1;api.words[18]=section->depth;lockit_section_after(site);');s=one(s,'n=="HeapFree"?reinterpret_cast<std::uintptr_t>(&::HeapFree):n=="LeaveCriticalSection"','n=="InitializeCriticalSection"?reinterpret_cast<std::uintptr_t>(&::InitializeCriticalSection):n=="HeapFree"?reinterpret_cast<std::uintptr_t>(&::HeapFree):n=="LeaveCriticalSection"');s+='\n#include "lockit_operations.inc"\n';(out/'locale_batch_operations.inc').write_text(s)
 c=(out/'registry_library.cpp').read_text();c=one(c,'#include "vtable_contract.inc"','#include "vtable_contract.inc"\n#include "lockit_contract.inc"');existing=set(re.findall(r'extern "C" .+?(\w+)\(',c));bridges={b for r in list(lift['source_bodies'].values())+list(pl['source_bodies'].values())for b in r['bridges']}
 for symbol in sorted(bridges-existing):
  if symbol.endswith('_undefined_8'):c+='\nextern "C" unsigned char '+symbol+'(){return mw34::m4_onexit::undefined();}\n'
  elif symbol.startswith('sub_')or '_direct_'in symbol:c+='\nextern "C" void*'+symbol+'(State*s,unsigned a,void*p){return mw34::m4_onexit::called(p,s,a);}\n'
  else:need(False,'Unexpected provider/game bridge '+symbol)
 # MSVCP source pages use its exact PE32 file; loaded RW input is separately pinned.
 c=c.replace('struct MatherrBinding {','std::array<std::byte,4096> lockit_raw_page(std::span<const std::byte>file,unsigned address){require(m4::sha256(file)=="91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a","Exact MSVCP50 image");auto dw=[&](unsigned p){unsigned v{};require(p+4<=file.size(),"MSVCP PE bounds");std::memcpy(&v,file.data()+p,4);return v;};auto sw=[&](unsigned p){unsigned short v{};require(p+2<=file.size(),"MSVCP PE bounds");std::memcpy(&v,file.data()+p,2);return v;};const auto pe=dw(60),opt=pe+24;require(dw(opt+28)==0x780c0000,"MSVCP base");std::array<std::byte,4096>b{};unsigned matches{};for(unsigned i=0;i<sw(pe+6);++i){unsigned s=opt+sw(pe+20)+40*i,rva=dw(s+12),size=dw(s+16),raw=dw(s+20),wanted=address-0x780c0000;if(wanted>=rva&&wanted+4096<=rva+size){require(raw+wanted-rva+4096<=file.size(),"MSVCP source page bounds");std::memcpy(b.data(),file.data()+raw+wanted-rva,4096);++matches;}}require(matches==1,"One raw MSVCP source page");return b;}\nstruct MatherrBinding {',1)
 (out/'registry_library.cpp').write_text(c)
 h=(out/'session.hpp').read_text();h=one(h,' void probe_mfc(', ' Session(m4_runtime::Runtime&,std::span<const std::byte>,std::span<const std::byte>,std::span<const std::byte>);\n void probe_mfc(');(out/'session.hpp').write_text(h)
 s=(out/'session_impl.inc').read_text();s=one(s,'std::vector<std::byte>provider,mfc_provider;','std::vector<std::byte>provider,mfc_provider,lockit_provider;');s=one(s,'std::span<const std::byte>mfc):self','std::span<const std::byte>mfc,std::span<const std::byte>msvcp={}):self');s=one(s,'mfc_provider(mfc.begin(),mfc.end()){','mfc_provider(mfc.begin(),mfc.end()),lockit_provider(msvcp.begin(),msvcp.end()){');s=one(s,'const auto original=p.address>=lb::mfc_image_base','const auto original=p.address==0x78145000?lb::lockit_loaded_page:(p.address==0x7810a000||p.address==0x78146000)?lockit_raw_page(lockit_provider,p.address):p.address>=lb::mfc_image_base');s=one(s,'"Actual source heap and four static critical sections established");','"Actual source heap and four static critical sections established");binding->lockit_bootstrap();');s=one(s,'binding->dump_vtable(sink,user);','binding->dump_vtable(sink,user);binding->dump_lockit(sink,user);');s+='\nnamespace mw34::m4_onexit {Session::Session(m4_runtime::Runtime&r,std::span<const std::byte>crt,std::span<const std::byte>mfc,std::span<const std::byte>msvcp):impl_(std::make_unique<SessionImpl>(*this,r,crt,mfc,msvcp)) {}}\n';(out/'session_impl.inc').write_text(s)
 objects=dict(base['entry_objects']);objects.update(lift['entry_objects']);objects.update(pl['entry_objects'])
 for p,h in objects.items():pin(p,h)
 for p,h in base['libraries'].items():pin(p,h)
 for p in out.iterdir():
  if p.is_file():pin(p)
 (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');files=dict(pins);files[str((out/'pins.json').resolve())]=sha(out/'pins.json')
 report=dict(passed=True,scope='Additive literal four-root and initialized Lockit resource preparation; native/original combined acceptance pending',entry_objects=objects,libraries=base['libraries'],source_pages=pages,game_pages=base['game_pages'],native_library=str((out/'registry_library.cpp').resolve()),native_include=str(out.resolve()),new_roots=list(lr),all_selected_roots=[r['entry']for r in gi['selected_order']],new_game_bodies=10,new_provider_bodies=2,observed_loaded_state=2,loaded_input_page=str(inputpage),loaded_input_page_sha256=sha(inputpage),normal_new_allocations=8,normal_new_FS_records=4,native_executed=False,roots_admitted=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),objects=len(objects))))
if __name__=='__main__':main(*sys.argv[1:])
