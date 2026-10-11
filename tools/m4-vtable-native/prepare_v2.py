"""Frozen additive four-root native derivative; accepted116 remains immutable."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;BASE=ROOT/'reports/m4-container-native/preparation-r2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-vtable-native'/name;need(not out.exists(),'Fresh derivative');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact frozen input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'No pin conflicts');pins[str(p)]=v;return p
 def receipt(p,h):
  r=json.loads(pin(p,h).read_bytes());need(r['passed'],'Passed receipt');
  for q,v in r.get('files',{}).items():pin(q,v)
  return r
 parent=pin(ROOT/'reports/m4-joint-startup116-root/acceptance-r1/report.json','de76b4e006e5ad2ce0b90f634054379f2271abd14ecb8591643c24e72cc4c0e6');need(json.loads(parent.read_bytes())['connected_roots']==116,'Accepted116 certificate')
 base=receipt(BASE/'report.json','4d1eb214d383b99a857e927e90768e3de4f87429f1c4def90c49067340e02164')
 rec=receipt(ROOT/'reports/m4-next-source/recovery-r1/report.json','99e59ac4b9adeb98f2227361f80db78e12eead87e35212d71b4147a8ba9effeb')
 lifts=receipt(ROOT/'reports/m4-next-source/lifts-r1/report.json','f5fc110ad15832c19d8be342c6b0f39a91c8ded617e0821f9cf37c661176df2b')
 receipt(ROOT/'reports/m4-next-source/symbol-attribution-r2/report.json','26447bc827f72a895914636f2268a4dab0f5d56e9773657582cc2455ec707b07');receipt(ROOT/'reports/m4-next-source/game-callbacks-r1/report.json','845cf43363195c5dc13bc0998004cb79164dea98a2583151222d30fa36860fd0')
 gi=json.loads(pin(ROOT/'reports/m4-next-source/recovery-r1/instruction-contracts.json').read_bytes());dispatch=json.loads(pin(ROOT/'reports/m4-next-source/symbol-attribution-r2/physical-dispatch.json').read_bytes());callbacks=json.loads(pin(ROOT/'reports/m4-next-source/game-callbacks-r1/callbacks.json').read_bytes())['State_offsets_by_original_PC']
 need(len(gi['roots'])==4 and len(dispatch)==15 and len(gi['selected_order'])==120 and not gi['allocations']and not gi['string_inputs'],'Exact four-root owner-free geometry')
 out.mkdir(parents=True)
 for p in BASE.iterdir():
  if p.suffix in('.cpp','.hpp','.inc'):(out/p.name).write_bytes(p.read_bytes())
 pin(__file__);pin(HERE/'vtable_operations.inc');(out/'vtable_operations.inc').write_bytes((HERE/'vtable_operations.inc').read_bytes())
 wrappers=('instruction','source_spans','source_pages','generated_undefined_sites','has_body','dispatch_body','registration_callback','fs_root','fs_frame_read','fs_frame_install','fs_frame_restore','fs_frame_entry')
 text=(out/'container_contract.inc').read_text()
 for fn in wrappers:text=re.sub(r'\b'+fn+r'\(', 'accepted116_'+fn+'(',text)
 (out/'container_contract.inc').write_text(text)
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
 rows={r['pc']:r for r in gi['instructions']};lines=['} // composition anonymous namespace','namespace mw34::m4_crt_locale_batch {','namespace {','struct VtableInput{unsigned root,site,slot,target,ecx,argument,cleanup,object,vtable,publication_pc;};constexpr VtableInput vtable_inputs[]{']
 for r in gi['static_indirect_inputs']:lines.append('{'+','.join(str(v)for v in(r['root'],r['CALL_pc'],r['slot'],r['target'],r['entry_ECX'],r['argument']if r['argument']is not None else 0xffffffff,r['RET_cleanup'],r['source_object'],r.get('source_vtable',0),r.get('dominating_vtable_store_PC',0)))+'},')
 lines+=['};','const VtableInput*vtable_input(unsigned root,unsigned site)noexcept{for(const auto&i:vtable_inputs)if(i.root==root&&i.site==site)return &i;return nullptr;}','bool vtable_root(unsigned root)noexcept{for(const auto&i:vtable_inputs)if(i.root==root)return true;return false;}','constexpr FsFrameSpec vtable_frames[]{']
 lines+=['{'+','.join(str(f[k])for k in('entry','handler','read','install','saved','restore','ret'))+'},'for f in gi['FS_frame_contracts']]+['};','constexpr SourceInstruction vtable_instructions[]{']
 for pc,r in sorted(rows.items()):
  ops=r['decoded_operands'];need(len(ops)<=3,'Finite operand count');rep={None:0,'rep':1,'repe':2,'repz':2,'repne':3,'repnz':3}.get(r.get('repeat'),0)
  lines.append('{'+f'{pc},{r["width"]},{json.dumps(r["mnemonic"])},{{{{'+','.join([operand(r,i,x)for i,x in enumerate(ops)]+['{}']*(3-len(ops)))+'}},'+f'{len(ops)},{rep}'+'},')
 spans=[];raw=bytearray();start=end=None
 for pc,r in sorted(rows.items()):
  if start is not None and pc!=end:spans.append((start,end,bytes(raw)));start=None;raw=bytearray()
  if start is None:start=pc
  raw.extend(bytes.fromhex(r['bytes_hex']));end=pc+r['width']
 if start is not None:spans.append((start,end,bytes(raw)))
 lines+=['};','constexpr SourceSpan vtable_spans[]{']+['{'+f'{a},{b-a},5,"{hashlib.sha256(raw).hexdigest()}"'+'},'for a,b,raw in spans]+['};','}']
 for field in('read','install','restore','entry'):lines.append(f'const FsFrameSpec*fs_frame_{field}(unsigned pc)noexcept{{for(const auto&i:vtable_frames)if(i.{field}==pc)return &i;return accepted116_fs_frame_{field}(pc);}}')
 pages={int(k):v for k,v in base['source_pages'].items()}
 lines+=['bool fs_root(unsigned root)noexcept{return root==0x47f5f0||accepted116_fs_root(root);}','const SourceInstruction*instruction(unsigned pc)noexcept{auto it=std::lower_bound(std::begin(vtable_instructions),std::end(vtable_instructions),pc,[](const auto&i,unsigned p){return i.pc<p;});return it!=std::end(vtable_instructions)&&it->pc==pc?it:accepted116_instruction(pc);}','std::span<const SourceSpan>source_spans()noexcept{static const auto all=[](){auto b=accepted116_source_spans();std::vector<SourceSpan>v(b.begin(),b.end());v.insert(v.end(),std::begin(vtable_spans),std::end(vtable_spans));return v;}();return all;}','std::span<const SourcePage>source_pages()noexcept{static const SourcePage p[]{'+','.join('{'+f'{p},{v}'+'}'for p,v in sorted(pages.items()))+'};return p;}']
 added=[int(pc)for pc,count in callbacks.items()for _ in count]
 lines+=['std::span<const unsigned>generated_undefined_sites()noexcept{static const auto all=[](){auto b=accepted116_generated_undefined_sites();std::map<unsigned,unsigned>counts,added;std::vector<unsigned>v;constexpr unsigned n[]{'+','.join(map(str,added))+'};for(auto pc:b)++counts[pc];for(auto pc:n)++added[pc];for(auto[pc,num]:added)counts[pc]=std::max(counts[pc],num);for(auto[pc,num]:counts)for(unsigned k=0;k<num;++k)v.push_back(pc);return v;}();return all;}','unsigned registration_callback(unsigned root)noexcept{switch(root){']+['case '+str(r['entry'])+':return '+str(r['registration']['callback'])+';'for r in gi['roots']]+['default:return accepted116_registration_callback(root);}}']
 bodies={d['entry']:d['source_function_symbol']for d in dispatch}
 lines+=['extern "C" void*'+s+'(State*,unsigned,void*);'for s in sorted(set(bodies.values()))]
 lines+=['bool has_body(unsigned pc)noexcept{switch(pc){']+['case '+str(pc)+':return true;'for pc in sorted(bodies)]+['default:return accepted116_has_body(pc);}}','void*dispatch_body(unsigned pc,State*s,void*p){switch(pc){']+['case '+str(pc)+':return '+s+'(s,pc,p);'for pc,s in sorted(bodies.items())]+['default:return accepted116_dispatch_body(pc,s,p);}}','}','namespace {'];(out/'vtable_contract.inc').write_text('\n'.join(lines)+'\n')
 h=(out/'locale_batch.hpp').read_text();needle='bool research_standalone_{};unsigned registry_root_{};';need(h.count(needle)==1,'Private derivative insertion')
 addon='std::vector<std::array<std::uint64_t,32>>vtable_records_;std::vector<std::array<std::uint64_t,16>>vtable_stores_;std::array<std::uint64_t,8>vtable_read_probe_{},vtable_vptr_{};std::array<std::uint64_t,16>vtable_store_probe_{};unsigned vtable_active_{};\n void vtable_hook(unsigned);void vtable_read_before(unsigned,unsigned);void vtable_read_after(unsigned,std::uint64_t,unsigned);void vtable_called(unsigned,unsigned,unsigned);void vtable_returned(unsigned,unsigned,unsigned);void vtable_write_before(unsigned,std::uint64_t,unsigned);void vtable_write_after(unsigned,std::uint64_t,unsigned);void dump_vtable(CaptureSink,void*)const;\n '
 (out/'locale_batch.hpp').write_text(h.replace(needle,addon+needle))
 b=(out/'locale_batch_binding.inc').read_text();needle='void Binding::stable_hook(unsigned point,bool terminal,bool cleaning){';snapshot='const auto vrecords=vtable_records_;const auto vstores=vtable_stores_;const auto vread=vtable_read_probe_,vptr=vtable_vptr_;const auto vprobe=vtable_store_probe_;const auto vactive=vtable_active_;';need(b.count(needle)==1,'One genuine stable observer');b=b.replace(needle,needle+snapshot,1)
 needle='hook(point);admit_current();';need(b.count(needle)==1,'One checked observer return');b=b.replace(needle,needle+'if(vrecords!=vtable_records_||vstores!=vtable_stores_||vread!=vtable_read_probe_||vptr!=vtable_vptr_||vprobe!=vtable_store_probe_||vactive!=vtable_active_)deny("Vtable observer changed private source-cell/frame/store witnesses",state.gpr.rip.dword);',1);(out/'locale_batch_binding.inc').write_text(b)
 o=(out/'locale_batch_operations.inc').read_text();o=o.replace('container_read_before(a,n);','vtable_read_before(a,n);container_read_before(a,n);',1).replace('source_access(a,v,n,false);','source_access(a,v,n,false);vtable_read_after(a,v,n);',1).replace('container_write_before(a,v,n);','vtable_write_before(a,v,n);container_write_before(a,v,n);',1).replace('container_write_after(a,v,n);','vtable_write_after(a,v,n);container_write_after(a,v,n);',1)
 needle='string_called(target,w.pc,w.address);';need(o.count(needle)==1,'Genuine CALL dispatch insertion');o=o.replace(needle,'vtable_called(target,w.pc,w.address);'+needle,1);needle='string_returned(f.entry,state.gpr.rax.dword,f.frame);';need(o.count(needle)==1,'Genuine RET witness insertion');o=o.replace(needle,'vtable_returned(f.entry,state.gpr.rax.dword,f.frame);'+needle,1);o+='\n#include "vtable_operations.inc"\n';(out/'locale_batch_operations.inc').write_text(o)
 c=(out/'registry_library.cpp').read_text().replace('#include "container_contract.inc"','#include "container_contract.inc"\n#include "vtable_contract.inc"',1);existing=set(re.findall(r'extern "C" .+?(\w+)\(',c));bridges={b for r in lifts['source_bodies'].values()for b in r['bridges']}
 for symbol in sorted(bridges-existing):
  if symbol.endswith('_undefined_8'):c+='\nextern "C" unsigned char '+symbol+'(){return mw34::m4_onexit::undefined();}\n'
  elif symbol.startswith('sub_')or '_direct_'in symbol:c+='\nextern "C" void*'+symbol+'(State*s,unsigned a,void*p){return mw34::m4_onexit::called(p,s,a);}\n'
  else:need(False,'Unexpected new bridge '+symbol)
 (out/'registry_library.cpp').write_text(c)
 contract=(out/'registry_contract.inc').read_text();m=re.search(r'constexpr unsigned registry_game_pages\[\]\{([^}]*)\}',contract);need(m,'Existing game-page inventory');gamepages=sorted(set(map(int,m[1].split(',')))|set(rec['new_pages']));contract=contract[:m.start(1)]+','.join(map(str,gamepages))+contract[m.end(1):];(out/'registry_contract.inc').write_text(contract)
 s=(out/'session_impl.inc').read_text();needle='binding->dump_container(sink,user);';need(s.count(needle)==1,'Actual observation sink');s=s.replace(needle,needle+'binding->dump_vtable(sink,user);');(out/'session_impl.inc').write_text(s)
 objects=dict(base['entry_objects']);objects.update(lifts['entry_objects'])
 for p,h in objects.items():pin(p,h)
 for p,h in base['libraries'].items():pin(p,h)
 interface=dict(hooks={110:'before genuine cell/vptr source read',111:'after actual raw cell/vptr association',112:'genuine indirect CALL and admitted zero argument',113:'after literal target RET',114:'before explicit game object source MOV/OR',115:'after committed source MOV/OR'},indirect_inputs=gi['static_indirect_inputs'],record_words=['v','index','root','site','slot','raw','delivered','readPC','readAccessIndex','ECX','priorVptr','expectedVtable','publicationAccessIndex','vptrReadIndex','frame','returnPC','argument','cleanup','exitESP','exitEAX','RETpc','returned','sourceStart','sourceEnd','FSbefore','FSafter','APIbefore','APIafter','ownersBefore','ownersAfter','reserved','reserved'],store_words=['v','index','root','pc','address','width','value','sourceBefore','sourceAfter','FShead','activeCall','reserved','reserved','reserved','reserved','reserved'],read_probe_words=['v','root','pc','address','width','expectedValue','sourceBefore','isInstanceRead'],vptr_words=['v','root','pc','address','value','readIndex','publicationIndex','publicationPC'],normal_calls_per_sequence=6,new_allocations=0,new_strdups=0,new_FS_records=1,nonzero_pointer_path_admitted=False)
 (out/'vtable-interface.json').write_text(json.dumps(interface,indent=2)+'\n');(out/'vtable-physical-dispatch.json').write_text(json.dumps(dispatch,indent=2)+'\n')
 for p in out.iterdir():
  if p.is_file():pin(p)
 (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');files=dict(pins);files[str((out/'pins.json').resolve())]=sha(out/'pins.json')
 report=dict(passed=True,scope='Static additive checked source indirect dispatch; actual120 capture/review pending',parent_acceptance_sha256=sha(parent),parent_native_preparation_sha256=sha(BASE/'report.json'),entry_objects=objects,libraries=base['libraries'],source_pages=pages,game_pages=gamepages,native_library=str((out/'registry_library.cpp').resolve()),native_include=str(out.resolve()),new_roots=[r['entry']for r in gi['roots']],all_selected_roots=[r['entry']for r in gi['selected_order']],new_game_bodies=len(dispatch),provider_bodies_added=0,normal_new_allocations=0,normal_total_live_owners=70,normal_indirect_calls=6,normal_new_FS_records=1,native_executed=False,roots_admitted=0,accepted116_files_modified=False,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),objects=len(objects),new_game_bodies=len(dispatch))))
if __name__=='__main__':main(sys.argv[1])

