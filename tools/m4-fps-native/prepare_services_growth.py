"""Admit source-owned callback-vector growth in the borrowed widget service.

Only Session's finite pre/postconditions change. The accepted literal provider,
actual allocator, generation/alias transport and all callback bodies stay frozen.
No worker, archive, numerical response, or AFTER input is consumed here.
"""
from pathlib import Path
import hashlib,json,shutil,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def one(t,a,b):need(t.count(a)==1,'Exact growth-guard hunk '+a[:100]);return t.replace(a,b)
def main(name):
 prior=R/'reports/m4-fps-native/service-preparation-r2';pp=prior/'report.json';out=prior.parent/name;need(not out.exists(),'Fresh service growth revision');out.mkdir();pins={};relations=[];passed=False;d={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Ordinary source only');v=sha(p);need(h is None or h==v,'Exact input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable input');pins[str(p)]=v;return p
 try:
  pin(pp,'d3afbd1f20d9a286a0ae8565554845f897c4d7a051d60110bb64912fa15d77c2');d=json.loads(pp.read_bytes());need(d['passed'],'Frozen seven-root borrowed source service')
  for p,h in d['files'].items():pin(p,h)
  for p in prior.iterdir():
   if p.is_file()and p.name!='report.json':
    q=out/p.name;shutil.copyfile(p,q);pin(p);relations.append(dict(name=p.name,prior_path=str(p.resolve()),prior_sha256=sha(p),current_path=str(q.resolve())))
  p=out/'session_impl.inc';s=p.read_text()
  a='  const auto begin=r.memory().load<unsigned>({0x7803788c}),next=r.memory().load<unsigned>({0x78037888});auto*allocation=binding->allocation_for(begin);require(allocation&&allocation->guest==begin&&allocation->native&&allocation->mapped&&!allocation->pending&&next>=begin&&std::uint64_t(next)+4<=std::uint64_t(begin)+allocation->extent,"Current live producer full-byte extent before literal msize");'
  b='''  const auto begin=r.memory().load<unsigned>({0x7803788c}),next=r.memory().load<unsigned>({0x78037888});auto*allocation=binding->allocation_for(begin);
  require(allocation&&allocation->guest==begin&&allocation->kind==1&&allocation->native&&allocation->mapped&&!allocation->pending&&!allocation->source_freed&&!allocation->cleanup_freed&&allocation->generation&&allocation->extent&&allocation->extent<=1024*1024&&next>=begin&&((next-begin)&3U)==0&&std::uint64_t(next)<=std::uint64_t(begin)+allocation->extent,"Current live producer full-byte cursor before literal msize, including a full vector");
  const auto used=next-begin,oldextent=allocation->extent,oldrequest=allocation->requested,oldgeneration=allocation->generation,oldmapped=allocation->mapped_bytes,oldcursor=binding->allocation_cursor_;const auto oldacquired=allocation->acquired;
  const auto growth_before=binding->registry_growth_.size(),api_before=binding->native_apis_.size();auto oldbytes=binding->guest_bytes(begin,oldextent);'''
  s=one(s,a,b)
  a='   require(binding->allocation_for(begin)==allocation&&allocation->native&&allocation->mapped&&!allocation->pending&&allocation->capacity&&allocation->extent==allocation->capacity&&std::uint64_t(next)+4<=std::uint64_t(begin)+allocation->capacity&&r.memory().load<unsigned>({0x7803788c})==begin&&r.memory().load<unsigned>({0x78037888})==next+4&&r.memory().load<unsigned>({next})==callback,"Actual literal msize capacity and source-owned registry publication");'
  b='''   const auto published=r.memory().load<unsigned>({0x7803788c}),published_next=r.memory().load<unsigned>({0x78037888});auto*current=binding->allocation_for(published);
   require(current==allocation&&current->guest==published&&current->kind==1&&current->native&&current->mapped&&!current->pending&&!current->source_freed&&!current->cleanup_freed&&current->extent>=std::uint64_t(used)+4&&published_next==std::uint64_t(published)+used+4&&r.memory().load<unsigned>({published+used})==callback,"Actual live source-published registry owner and one appended callback");
   const auto growth_after=binding->registry_growth_.size();require(growth_after==growth_before||growth_after==growth_before+1,"One bounded literal registry growth per widget registration");const bool grew=growth_after!=growth_before;
   unsigned size_calls{},realloc_calls{};std::size_t first_size{},last_size{};for(std::size_t i=api_before;i<binding->native_apis_.size();++i){const auto&a=binding->native_apis_[i].words;const auto specs=lb::source_api_contracts();const auto spec=std::find_if(specs.begin(),specs.end(),[&](const auto&x){return x.site==a[2]&&x.slot==a[3]&&x.raw==a[4]&&x.argc==a[7];});require(spec!=specs.end()&&a[14]==1&&a[15]==1,"Completed exact source API rows during borrowed registry service");if(std::string_view(spec->name)=="HeapSize"){if(!size_calls)first_size=i;last_size=i;++size_calls;require(a[22]==begin&&a[16]==oldacquired&&a[12]==a[17]&&binding->native_apis_[i].outputs.size()==1&&binding->native_apis_[i].outputs[0].size()==a[17],"Actual named HeapSize measures the same preceding native owner and entire capacity");}else if(std::string_view(spec->name)=="HeapReAlloc"){++realloc_calls;require(a[22]==begin&&a[16]==oldacquired,"Actual named HeapReAlloc grows the same preceding owner");}else require(std::string_view(spec->name)=="EnterCriticalSection"||std::string_view(spec->name)=="LeaveCriticalSection","Only literal lock and size/growth services inside borrowed onexit");}
   require(size_calls==(grew?2U:1U)&&realloc_calls==unsigned(grew),"Literal one-size normal path or two-size single-growth path");
   if(!grew){require(published==begin&&current->acquired==oldacquired&&current->generation==oldgeneration&&current->requested==oldrequest&&current->capacity&&current->extent==current->capacity&&current->extent>=oldextent&&current->extent==binding->native_apis_[last_size].words[17]&&current->mapped_bytes==oldmapped&&binding->allocation_cursor_==oldcursor,"Unchanged owner generation with actual measured msize capacity");auto expected=binding->native_apis_[last_size].outputs[0];std::memcpy(expected.data()+used,&callback,4);require(binding->guest_bytes(published,current->extent)==expected,"Whole actual HeapSize capacity with only the literal callback append");}
   else{
    const auto&g=binding->registry_growth_.back();require(g[0]==1&&g[1]>=api_before&&g[1]<binding->native_apis_.size()&&g[2]==0x78011c27&&g[3]==begin&&g[4]==oldacquired&&g[5]==oldgeneration&&g[6]==oldrequest&&g[7]>=oldextent&&g[7]==g[8]&&binding->native_apis_[first_size].words[17]<std::uint64_t(used)+4&&g[8]==binding->native_apis_[last_size].words[17]&&g[9]==g[8]+16&&g[9]<=1024*1024&&g[10]==((g[9]+15)&~15ULL)&&g[11]&&g[11]==g[14]&&g[13]==published&&g[15]==current->generation&&g[15]>oldgeneration&&g[16]==g[10]&&g[17]==0&&g[18]==unsigned(g[14]!=oldacquired)&&g[19]==1&&g[20]==g[10]&&g[21]==0&&g[22]==1&&g[23]==0,"Complete successful literal capacity+16 growth witness, generation and alias transport");
    for(unsigned i=24;i<32;++i)require(g[i]==0,"Complete zero reserved growth witness words");const auto&api=binding->native_apis_[g[1]].words;require(api[2]==g[2]&&api[8]==g[11]&&api[12]==published&&api[13]==g[10]&&api[23]==g[10]&&current->acquired==g[14]&&current->acquired==reinterpret_cast<std::uintptr_t>(current->native)&&current->requested==g[9]&&current->extent==g[10]&&current->capacity==0&&current->initial.size()==current->extent&&current->pending_native.empty()&&current->retired_guest==0,"Actual realloc API return and complete current source-owned extent");require(binding->native_apis_[g[1]].inputs.size()==1&&binding->native_apis_[g[1]].inputs[0]==binding->native_apis_[last_size].outputs[0]&&binding->native_apis_[g[1]].outputs.size()==1&&binding->native_apis_[g[1]].outputs[0]==current->initial,"Whole measured old capacity and actual new realloc input/output joins");require(published==(g[18]?oldcursor:begin)&&current->mapped_bytes==(g[18]?((current->extent+4095)&~4095U):oldmapped)&&binding->allocation_cursor_==oldcursor+(g[18]?current->mapped_bytes:0),"Exact in-place or moved source alias and allocation cursor");
    auto expected=current->initial;std::memcpy(expected.data()+used,&callback,4);require(binding->guest_bytes(published,current->extent)==expected,"Whole actual realloc initial extent with only the literal callback append");
   }
   if(used<oldextent){require(std::uint64_t(used)+4<=oldextent,"Aligned complete callback DWORD inside preceding extent");std::memcpy(oldbytes.data()+used,&callback,4);}
   require(binding->guest_bytes(published,oldextent)==oldbytes,"Every preceding producer byte carried, except the one source callback append");'''
  s=one(s,a,b);p.write_text(s)
  for row in relations:row.update(current_sha256=sha(row['current_path']),byte_identical=sha(row['current_path'])==row['prior_sha256']);pin(row['current_path'])
  need([x['name']for x in relations if not x['byte_identical']]==['session_impl.inc'],'Only finite borrowed service guard changed')
  pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  d.update(passed=passed,scope='Unexecuted source-owned registry growth extension of exact borrowed widget/FPS onexit service; source provider and native allocator unchanged',native_library=str(out/'registry_library.cpp'),native_include=str(out),prior_service_preparation=str(pp.resolve()),prior_service_preparation_sha256=sha(pp),copied_source_relations=relations,changed_files=['session_impl.inc'],growth_request_increment=16,source_grows_vector=True,host_onexit=False,source_output_seed=False,native_executed=False,initializer_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),source_files=len(relations))))
if __name__=='__main__':main(sys.argv[1])
