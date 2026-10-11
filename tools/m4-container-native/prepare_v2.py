"""Additive literal container/CString/null-free derivative of accepted109."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
BASE=ROOT/'reports/m4-fs-native/preparation-r3'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p):return json.loads(Path(p).read_bytes())
def need(v,w):
 if not v:raise ValueError(w)

def main(name,inputs_path):
 out=ROOT/'reports/m4-container-native'/name;need(re.fullmatch('preparation-r[1-9][0-9]*',name)and not out.exists(),'Fresh container derivative');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact frozen physical input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Physical digest conflict');pins[str(p)]=v;return p
 def receipt(p,h):
  r=js(pin(p,h));need(r['passed'],'Successful immutable receipt '+str(p))
  for q,v in r['files'].items():pin(q,v)
  return r
 config=js(pin(inputs_path));pin(__file__);pin(HERE/'container_operations.inc')
 parent=js(pin(ROOT/'reports/m4-joint-startup109-root/acceptance-r1/report.json','697765f750209d9bee79541b973494dca89692f4ec630057d282cbbb450266e0'));need(parent['passed']and parent['connected_roots']==109,'Exact accepted109 certificate; root final gate independently verifies its retained complete closure')
 base=receipt(BASE/'report.json','5ee2a50044e6e887c54d49b7a574806a21be032c7352fefacfbe431397abb35e')
 records={k:receipt(v['path'],v['sha256'])for k,v in config.items()}
 def artifact(role,name):return js(pin(Path(config[role]['path']).parent/name))
 gi=artifact('recovery','instruction-contracts.json');game=records['game_lifts'];attr=records['game_symbols'];cb=artifact('game_callbacks','callbacks.json')['State_offsets_by_original_PC']
 ai=artifact('allocation_interface','allocation-inputs.json');vectors=records['allocation_interface']['vector_endpoints'];borrowed=records['allocation_interface']['borrowed_constructor_inputs'];strings=artifact('allocation_interface','string-inputs.json')
 dispatch=artifact('game_symbols','physical-dispatch.json');pi=artifact('provider_lifts','instruction-contracts.json');prov=records['provider_lifts'];loader=records['loader']
 need(len(gi['roots'])==7 and len(ai)==5 and len(vectors)==5 and len(strings)==3 and len(borrowed)==3,'Exact seven-root normal allocation/input domains')
 need(loader['borrowed_data']['raw_value']==loader['borrowed_data']['post_DllMain_value']==0x5f4cecec,'Actual loader nil DWORD unchanged from physical source')
 need(len(pi['instructions'])==10,'Exact two ten-row literal MFC540 bodies')
 out.mkdir(parents=True)
 for p in BASE.iterdir():
  if p.suffix in('.cpp','.hpp','.inc'):(out/p.name).write_bytes(p.read_bytes())
 (out/'container_operations.inc').write_bytes((HERE/'container_operations.inc').read_bytes())
 old=(out/'fs_contract.inc').read_text()
 wrappers=('instruction','source_spans','source_pages','generated_undefined_sites','source_api_contracts','has_body','dispatch_body','registration_callback','mfc_root_input','mfc_callsite','fs_root','fs_frame_read','fs_frame_install','fs_frame_restore','fs_frame_entry')
 for fn in wrappers:old=re.sub(r'\b'+fn+r'\(', 'accepted109_'+fn+'(',old)
 (out/'fs_contract.inc').write_text(old)
 old=(out/'strings_contract.inc').read_text();old=re.sub(r'\bstring_input\(', 'accepted109_string_input(',old);(out/'strings_contract.inc').write_text(old)
 rows={r['pc']:r for r in gi['instructions']};rows.update({r['pc']:r for r in pi['instructions']})
 regs={r:i for i,r in enumerate(['','eax','ecx','edx','ebx','esp','ebp','esi','edi','al','cl','dl','bl','ah','ch','dh','bh','ax','cx','dx','bx','sp','bp','si','di'])}
 def operand(r,i,x):
  kind=x['kind'];bits=x.get('bits',0)or next((v.get('bits',0)for v in r['decoded_operands']if v.get('bits',0)),32)
  if kind=='register':return '{'+f'1,{bits//8},{regs[x["register"]]},0,0,0,1,0,0,1'+'}'
  if kind=='immediate':return '{'+f'2,{bits//8},0,0,0,0,1,0,{x["value"]&0xffffffffffffffff}ULL,1'+'}'
  need(kind=='memory','Exact integer/FS decoded operand');base_reg=index=0;scale=1
  for term in x['terms']:
   if not base_reg and term['scale']==1:base_reg=regs[term['register']]
   else:index=regs[term['register']];scale=term['scale']
  disp=x['displacement'];disp=disp if disp<2**31 else disp-2**32;access=int(i in r['explicit_memory_reads'])+2*int(i in r['explicit_memory_writes'])
  return '{'+f'3,{bits//8},0,{int(x["segment"]=="fs")},{base_reg},{index},{scale},{disp},0,{access}'+'}'
 frames={}
 for f in artifact('allocation_interface','FS-frame-contracts.json'):
  entry=f['entry'];saved,ret=f['saved'],f['ret'];need(saved in rows and ret in rows and rows[ret]['mnemonic']=='ret','Reached literal FS saved read and RET');frames[entry]=(entry,f['handler'],f['read'],f['install'],saved,f['restore'],ret)
 lines=['} // anonymous composition namespace','namespace mw34::m4_crt_locale_batch {','namespace {',
 'constexpr unsigned container_borrowed_entry=0x5f4020b4,container_accessor_entry=0x5f4020c4,container_borrowed_data=0x5f4ccb54,container_borrowed_loaded=0x5f4cecec;',
 'constexpr FsFrameSpec container_frames[]{']
 lines+=['{'+','.join(map(str,f))+'},'for f in frames.values()]+['};','constexpr MfcRootInput container_mfc_inputs[]{']
 lines+=['{'+','.join(str(r[k])for k in('root','CALL_pc','requested_size','object','publication'))+'},'for r in ai]+['};',
 'struct ContainerBorrowedInput{unsigned root,call,object;};constexpr ContainerBorrowedInput container_borrowed_inputs[]{']
 lines+=['{'+','.join(str(r[k])for k in('root','CALL_pc','object'))+'},'for r in borrowed]+['};',
 'const ContainerBorrowedInput*container_borrowed_input(unsigned root,unsigned call)noexcept{for(const auto&i:container_borrowed_inputs)if(i.root==root&&i.call==call)return &i;return nullptr;}',
 'struct ContainerVector{unsigned root,call,request,publication,publication_pc,end,end_pc,capacity,capacity_pc,free_call;};constexpr ContainerVector container_vectors[]{']
 lines+=['{'+','.join(str(r[k])for k in('root','CALL_pc','requested_size','publication','publication_PC','end_address','end_PC','capacity_address','capacity_PC','free_CALL'))+'},'for r in vectors]+['};',
 'const ContainerVector*container_free_input(unsigned root,unsigned site)noexcept{for(const auto&i:container_vectors)if(i.root==root&&i.free_call==site)return &i;return nullptr;}',
 'struct ContainerVectorStore{unsigned root,pc,call,address,kind;};constexpr ContainerVectorStore container_vector_stores[]{']
 for r in vectors:
  for pc,address,kind in((r['publication_PC'],r['publication'],1),(r['end_PC'],r['end_address'],2),(r['capacity_PC'],r['capacity_address'],3)):
   need(pc in rows,'Exact literal endpoint store PC');lines.append('{'+','.join(map(str,(r['root'],pc,r['CALL_pc'],address,kind)))+'},')
  for index,extra in enumerate(r['additional_empty_pointer_fields']):
   need(extra['PC']in rows and extra['offset']==0,'Exact additional empty vector pointer source stores');lines.append('{'+','.join(map(str,(r['root'],extra['PC'],r['CALL_pc'],extra['address'],4+index)))+'},')
 lines+=['};','const ContainerVectorStore*container_vector_store(unsigned root,unsigned pc)noexcept{for(const auto&i:container_vector_stores)if(i.root==root&&i.pc==pc)return &i;return nullptr;}',
 'constexpr StringInput container_strings[]{']
 for r in strings:lines.append('{'+','.join(map(str,(r['root'],r['source'],r['CALL_pc'],r['size'],len(bytes.fromhex(r['physical_bytes_hex'])))))+','+json.dumps(hashlib.sha256(bytes.fromhex(r['physical_bytes_hex'])).hexdigest())+'},')
 lines+=['};','constexpr SourceInstruction container_instructions[]{']
 for pc,r in sorted(rows.items()):
  ops=r['decoded_operands'];need(len(ops)<=3,'Finite literal operands');rep={None:0,'rep':1,'repe':2,'repz':2,'repne':3,'repnz':3}.get(r.get('repeat'),0)
  lines.append('{'+f'{pc},{r["width"]},{json.dumps(r["mnemonic"])},{{{{'+','.join([operand(r,i,x)for i,x in enumerate(ops)]+['{}']*(3-len(ops)))+'}},'+f'{len(ops)},{rep}'+'},')
 spans=[];raw=bytearray();start=end=None
 for pc,r in sorted(rows.items()):
  if start is not None and pc!=end:spans.append((start,end,bytes(raw)));start=None;raw=bytearray()
  if start is None:start=pc
  raw.extend(bytes.fromhex(r['bytes_hex']));end=pc+r['width']
 if start is not None:spans.append((start,end,bytes(raw)))
 lines+=['};','constexpr SourceSpan container_spans[]{']+['{'+f'{a},{b-a},5,"{hashlib.sha256(raw).hexdigest()}"'+'},'for a,b,raw in spans]+['};','}']
 for field in('read','install','restore','entry'):lines.append(f'const FsFrameSpec*fs_frame_{field}(unsigned pc)noexcept{{for(const auto&i:container_frames)if(i.{field}==pc)return &i;return accepted109_fs_frame_{field}(pc);}}')
 pages={int(k):v for k,v in base['source_pages'].items()};pages.update({0x5f402000:5,0x5f4cc000:3})
 lines+=['bool fs_root(unsigned root)noexcept{switch(root){'+''.join('case '+str(r['entry'])+':return true;'for r in gi['roots'])+'default:return accepted109_fs_root(root);}}',
 'const MfcRootInput*mfc_root_input(unsigned root,unsigned site)noexcept{for(const auto&i:container_mfc_inputs)if(i.root==root&&i.call==site)return &i;return accepted109_mfc_root_input(root,site);}',
 'bool mfc_callsite(unsigned pc)noexcept{return accepted109_mfc_callsite(pc);}',
 'const StringInput*string_input(unsigned root)noexcept{for(const auto&i:container_strings)if(i.root==root)return &i;return accepted109_string_input(root);}',
 'const SourceInstruction*instruction(unsigned pc)noexcept{auto it=std::lower_bound(std::begin(container_instructions),std::end(container_instructions),pc,[](const auto&i,unsigned p){return i.pc<p;});return it!=std::end(container_instructions)&&it->pc==pc?it:accepted109_instruction(pc);}',
 'std::span<const SourceSpan>source_spans()noexcept{static const auto all=[](){auto b=accepted109_source_spans();std::vector<SourceSpan>v(b.begin(),b.end());v.insert(v.end(),std::begin(container_spans),std::end(container_spans));return v;}();return all;}',
 'std::span<const SourcePage>source_pages()noexcept{static const SourcePage p[]{'+','.join('{'+f'{p},{v}'+'}'for p,v in sorted(pages.items()))+'};return p;}',
 'std::span<const SourceApi>source_api_contracts()noexcept{return accepted109_source_api_contracts();}']
 counts={int(pc):len(offsets)for pc,offsets in cb.items()}
 for pc,offsets in pi.get('callbacks',{}).items():counts[int(pc)]=max(counts.get(int(pc),0),len(offsets))
 newlist=[pc for pc,count in sorted(counts.items())for _ in range(count)]
 lines+=['std::span<const unsigned>generated_undefined_sites()noexcept{static const auto all=[](){auto b=accepted109_generated_undefined_sites();std::map<unsigned,unsigned>counts,added;std::vector<unsigned>v;constexpr unsigned n[]{'+','.join(map(str,newlist))+'};for(auto pc:b)++counts[pc];for(auto pc:n)++added[pc];for(auto[pc,num]:added)counts[pc]=std::max(counts[pc],num);for(auto[pc,num]:counts)for(unsigned k=0;k<num;++k)v.push_back(pc);return v;}();return all;}',
 'unsigned registration_callback(unsigned root)noexcept{switch(root){']+['case '+str(r['entry'])+':return '+str(r['registration']['callback'])+';'for r in gi['roots']]+['default:return accepted109_registration_callback(root);}}']
 bodies={}
 for d in dispatch:
  path=pin(d['host_LL'],d['host_sha256']);symbol=d['source_function_symbol'];need(re.search(r'^define ptr @'+re.escape(symbol)+r'\(ptr(?: noalias)? %\w+, i32 %\w+, ptr(?: noalias)? %\w+\)',path.read_text(),re.M),'Actual physical body ABI')
  for level,obj in d['objects'].items():need(obj['machine']==0x8664 and obj['symbol']==symbol and sha(obj['path'])==obj['sha256'],'Exact physical AMD64 body/symbol')
  bodies[d['entry']]=symbol
 for d in prov['source_bodies'].values():bodies[d['entry']]=d['symbol']
 lines+=['extern "C" void*'+s+'(State*,unsigned,void*);'for s in sorted(set(bodies.values()))]
 lines+=['bool has_body(unsigned pc)noexcept{switch(pc){']+['case '+str(pc)+':return true;'for pc in sorted(bodies)]+['default:return accepted109_has_body(pc);}}',
 'void*dispatch_body(unsigned pc,State*s,void*p){switch(pc){']+['case '+str(pc)+':return '+s+'(s,pc,p);'for pc,s in sorted(bodies.items())]+['default:return accepted109_dispatch_body(pc,s,p);}}','}','namespace {']
 (out/'container_contract.inc').write_text('\n'.join(lines)+'\n')
 h=(out/'locale_batch.hpp').read_text();needle='bool research_standalone_{};unsigned registry_root_{};'
 addon='struct ContainerRecord{std::array<std::uint64_t,32>words{};bool operator==(const ContainerRecord&)const=default;};std::vector<ContainerRecord>container_nulls_,container_borrowed_;std::vector<std::array<std::uint64_t,8>>container_imports_;std::vector<std::array<std::uint64_t,16>>container_stores_;std::array<std::uint64_t,16>container_probe_{};unsigned container_null_active_{},container_borrowed_active_{};\n void container_guard();void container_hook(unsigned);void container_read_before(unsigned,unsigned);void container_write_before(unsigned,std::uint64_t,unsigned);void container_write_after(unsigned,std::uint64_t,unsigned);void dump_container(CaptureSink,void*)const;void accepted109_mfc_called(unsigned,unsigned,unsigned);std::uint64_t accepted109_mfc_read(unsigned,std::uint64_t,unsigned);void accepted109_mfc_returned(unsigned,unsigned,unsigned);\n '
 need(h.count(needle)==1,'Exact additive private state insertion');(out/'locale_batch.hpp').write_text(h.replace(needle,addon+needle))
 m=(out/'mfc_operations.inc').read_text()
 for fn in('mfc_called','mfc_read','mfc_returned'):m=m.replace('Binding::'+fn+'(', 'Binding::accepted109_'+fn+'(',1)
 (out/'mfc_operations.inc').write_text(m)
 b=(out/'locale_batch_binding.inc').read_text();needle='void Binding::stable_hook(unsigned point,bool terminal,bool cleaning){';need(b.count(needle)==1,'One genuine observer boundary')
 snapshot='const auto container_nulls=container_nulls_,container_borrowed=container_borrowed_;const auto container_imports=container_imports_;const auto container_stores=container_stores_;const auto container_probe=container_probe_;const auto container_null_active=container_null_active_,container_borrowed_active=container_borrowed_active_;'
 b=b.replace(needle,needle+snapshot,1)
 needle='hook(point);admit_current();';need(b.count(needle)==1,'Actual observer callback then authority admission')
 b=b.replace(needle,needle+'if(container_nulls!=container_nulls_||container_borrowed!=container_borrowed_||container_imports!=container_imports_||container_stores!=container_stores_||container_probe!=container_probe_||container_null_active!=container_null_active_||container_borrowed_active!=container_borrowed_active_)deny("Container observer changed private import/borrowed/null-free/store witnesses",state.gpr.rip.dword);',1)
 (out/'locale_batch_binding.inc').write_text(b)
 o=(out/'locale_batch_operations.inc').read_text();o=o.replace('live_allocations()>64','live_allocations()>80',1)
 o=o.replace('void Binding::batch_guard(){','void Binding::batch_guard(){container_guard();',1)
 needle='fs_read_before(a,n);';need(o.count(needle)==1,'Single checked source read adapter');o=o.replace(needle,'container_read_before(a,n);'+needle,1)
 o=o.replace('fs_write_before(a,v,n);','container_write_before(a,v,n);fs_write_before(a,v,n);',1).replace('fs_write_after(a,v,n);','container_write_after(a,v,n);fs_write_after(a,v,n);',1)
 needle='for(const auto&a:source_api_contracts())if(a.raw==target&&a.tail)';need(o.count(needle)==1,'Exact source missing-tail insertion')
 tail='if(target==mfc_free_entry||target==container_borrowed_entry){const bool free=target==mfc_free_entry;const auto&r=source_accesses_.back();auto&f=calls_.back();const auto thunk=free?0x5abd1aU:0x5abdb0U,slot=free?0x5bb4c8U:0x5bb454U,raw=free?0x80000339U:0x8000021cU;if(r.pc!=thunk||r.address!=slot||r.value!=raw||f.entry!=thunk)deny("Actual checked container ordinal game thunk tail import preserves CALL frame",target);mfc_called(target,f.site,f.frame);f.entry=target;return dispatch_body(target,s,this);}\n '
 o=o.replace(needle,tail+needle,1);o+='\n#include "container_operations.inc"\n'
 # Prior string CALL sites remain admitted; the new roots share two existing
 # sites and introduce only 47AB37. Source recovery proves its actual import.
 stringsites=sorted({r['pc']for r in gi['instructions']if any(x.get('kind')=='memory'and x.get('displacement')==0x5bb670 and not x.get('terms')for x in r['decoded_operands'])})
 marker='state.gpr.rip.dword!=4790915)';need(o.count(marker)==1,'Exact inherited strdup import guard');o=o.replace(marker,'state.gpr.rip.dword!=4790915'+''.join('&&state.gpr.rip.dword!='+str(pc)for pc in stringsites)+')',1)
 (out/'locale_batch_operations.inc').write_text(o)
 c=(out/'registry_library.cpp').read_text().replace('#include "fs_contract.inc"','#include "fs_contract.inc"\n#include "container_contract.inc"',1)
 bridges={b for r in game['source_bodies'].values()for b in r['bridges']}|{b for r in prov['source_bodies'].values()for b in r['bridges']};existing=set(re.findall(r'extern "C" .+?(\w+)\(',c))
 for symbol in sorted(bridges-existing):
  if symbol.endswith('_undefined_8'):c+='\nextern "C" unsigned char '+symbol+'(){return mw34::m4_onexit::undefined();}\n'
  elif symbol.startswith('sub_')or '_direct_'in symbol:c+='\nextern "C" void*'+symbol+'(State*s,unsigned a,void*p){return mw34::m4_onexit::called(p,s,a);}\n'
  else:need(symbol in{'__remill_read_memory_32','__remill_write_memory_32','__remill_write_memory_8','__remill_write_memory_16','__remill_function_call','__remill_function_return','__remill_missing_block'},'Known physical bridge '+symbol)
 (out/'registry_library.cpp').write_text(c)
 contract=(out/'registry_contract.inc').read_text();match=re.search(r'constexpr unsigned registry_game_pages\[\]\{([^}]*)\}',contract);need(match,'Inherited complete game-page declaration')
 gamepages=sorted((set(map(int,match[1].split(',')))|set(gi['source_data_pages']))-{0x5f4cc000})
 contract=contract[:match.start(1)]+','.join(map(str,gamepages))+contract[match.end(1):];(out/'registry_contract.inc').write_text(contract)
 s=(out/'session_impl.inc').read_text().replace('binding->dump_fs(sink,user);','binding->dump_fs(sink,user);binding->dump_container(sink,user);',1)
 s+='\nnamespace mw34::m4_onexit {std::vector<std::array<std::uint64_t,32>>Session::container_nullfree_witnesses()const{std::vector<std::array<std::uint64_t,32>>v;for(const auto&r:impl_->binding->container_nulls_)v.push_back(r.words);return v;}std::vector<std::array<std::uint64_t,32>>Session::container_borrowed_witnesses()const{std::vector<std::array<std::uint64_t,32>>v;for(const auto&r:impl_->binding->container_borrowed_)v.push_back(r.words);return v;}std::array<std::uint64_t,16>Session::container_vector_probe()const noexcept{return impl_->binding->container_probe_;}}\n';(out/'session_impl.inc').write_text(s)
 h=(out/'session.hpp').read_text();needle='std::vector<std::array<std::uint64_t,32>>fs_witnesses()const;';need(h.count(needle)==1,'Stable Session with additive observational getters');h=h.replace(needle,'std::vector<std::array<std::uint64_t,32>>container_nullfree_witnesses()const;std::vector<std::array<std::uint64_t,32>>container_borrowed_witnesses()const;std::array<std::uint64_t,16>container_vector_probe()const noexcept;\n '+needle);(out/'session.hpp').write_text(h)
 objects=dict(base['entry_objects']);objects.update(game['entry_objects']);objects.update(prov['entry_objects'])
 for p,h in objects.items():pin(p,h)
 for p,h in base['libraries'].items():pin(p,h)
 interface=dict(schema='mw34-container-native-interface-v1',frames=list(frames.values()),hooks={90:'genuine null MFC825 entry',91:'genuine MFC825 to CRTfree(NULL) CALL',92:'genuine CRTfree(NULL) RET',93:'genuine MFC825 null RET',94:'borrowed MFC540 entry',95:'before genuine borrowed DWORD read',96:'after genuine borrowed DWORD read',97:'before literal borrowed object store',98:'after committed borrowed object store',99:'genuine MFC540 RET',100:'before exact owned vector endpoint store',101:'after committed endpoint store'},
  nullfree_words=['v','index','root','callerSite','MFCentry','frame','returnPC','zeroArgument','rawGame825','gameReadPC','generationBefore','CRTentry','CRTframe','CRTreturnPC','rawMFCfree','freeReadPC','resolvedCRTentry','CRTreturned','MFCreturned','outerFS0','FS0atCRTentry','FS0afterCRT','FS0afterMFC','APIbefore','APIafter','ownersBefore','ownersAfter','sourceStart','sourceEnd','EAXCRT','EAXMFC','generationAfter'],
  borrowed_words=['v','index','root','entry','site','frame','returnPC','ECXobject','raw540','gameReadPC','accessorFrame','accessorReturnPC','accessorResult','dataAddress','dataPC','dataValue','destination','storePC','storeValue','committed','RETpc','RET_EAX','returned','sourceStart','sourceEnd','FSbefore','FSafter','APIbefore','APIafter','ownersBefore','ownersAfter','reserved'],
  vector_words=['v','index','root','pc','address','width','value','endpointKind','MFCindex','guestBegin','generation','requestedSize','fullNative','roundedExtent','sourceBefore','sourceAfter'],
  borrowed_input=loader['borrowed_data'],mapped_MFC_pages=[0x5f402000,0x5f4cc000],pointee_page_admitted=False,
  normal_new_allocations=8,normal_new_MFC_allocations=5,normal_new_strdups=3,normal_null_frees=5,normal_vector_endpoint_stores=17,normal_game_FS_records=7,normal_total_live_owners=70,live_owner_bound=80,
  scope='Raw native provider page plus genuine loaded reached DWORD identity; borrowed pointee not dereferenced. Genuine free(NULL) literal chain returns; no native HeapFree. Positive empty vectors only; handler/allocation-null/nonemptyold-vector/callback paths remain excluded.')
 (out/'container-interface.json').write_text(json.dumps(interface,indent=2)+'\n');(out/'container-physical-dispatch.json').write_text(json.dumps(dispatch,indent=2)+'\n')
 files=dict(pins)
 for p in out.iterdir():
  if p.is_file():files[str(p.resolve())]=sha(p)
 (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');files[str((out/'pins.json').resolve())]=sha(out/'pins.json')
 report=dict(passed=True,schema='mw34-container-native-preparation-v1',scope='Additive static literal library/physical COFF closure only; actual connected116 capture/review pending',parent_acceptance_sha256=sha(ROOT/'reports/m4-joint-startup109-root/acceptance-r1/report.json'),parent_native_preparation_sha256=sha(BASE/'report.json'),entry_objects=objects,libraries=base['libraries'],source_pages=pages,game_pages=gamepages,native_library=str((out/'registry_library.cpp').resolve()),native_include=str(out.resolve()),new_roots=[r['entry']for r in gi['roots']],all_selected_roots=[r['entry']if isinstance(r,dict)else r for r in gi['selected_order']],new_game_bodies=len(dispatch),provider_bodies_added=2,normal_new_allocations=8,normal_total_live_owners=70,normal_NULL_frees=5,native_executed=False,roots_admitted=0,accepted109_files_modified=False,resource_bounds=dict(liveAllocations=80,events=8192,typedAPIs=4096,sourceAccesses=200000,FsRecords=128,FsEvents=4096,MfcRecords=512,ContainerRecords=512,ContainerStores=4096),files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),objects=len(objects),new_game_bodies=len(dispatch))))

if __name__=='__main__':main(*sys.argv[1:])
