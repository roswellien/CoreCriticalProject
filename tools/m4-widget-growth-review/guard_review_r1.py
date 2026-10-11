"""Independent finite ordinary-file review of the additive borrowed growth guards."""
from pathlib import Path
import difflib,hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
A=R/'reports/m4-fps-native/service-preparation-r2'
B=R/'reports/m4-fps-native/service-preparation-r3'
J=R/'reports/m4-joint-startup138/preparation-r3'
PINS={}
def raw(p):
 p=Path(p);b=p.read_bytes();PINS[str(p.resolve())]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
def need(v,m):
 if not v:raise ValueError(m)
def main(out):
 out=Path(out).resolve();need(not out.exists(),'Immutable additive review output');out.mkdir(parents=True)
 prepbytes=raw(B/'report.json');need(hashlib.sha256(prepbytes).hexdigest()=='cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9','Exact candidate preparation');prep=json.loads(prepbytes)
 rows=prep['copied_source_relations'];need(len(rows)==72,'Complete inherited copy extent');changed=[]
 for row in rows:
  p=Path(row['prior_path']);q=Path(row['current_path']);need(p.parent==A and q.parent==B and p.name==q.name==row['name'],'Exact ordinary service file association');a=raw(p);b=raw(q)
  need(hashlib.sha256(a).hexdigest()==row['prior_sha256'] and hashlib.sha256(b).hexdigest()==row['current_sha256'],'Actual complete copied file hashes');need((a==b)==row['byte_identical'],'Complete byte equality association')
  if a!=b:changed.append(p.name)
 need(changed==['session_impl.inc'],'Only SessionImpl guard extension changed')
 a=raw(A/'session_impl.inc').decode();b=raw(B/'session_impl.inc').decode();ops=[o for o in difflib.SequenceMatcher(a=a.splitlines(),b=b.splitlines()).get_opcodes() if o[0]!='equal'];need(len(ops)==2 and [o[0] for o in ops]==['replace','replace'],'Exactly two finite guard hunks')
 s=b.index(' void borrow_widget_onexit(');e=b.index('\n void finish(){',s);s0=a.index(' void borrow_widget_onexit(');e0=a.index('\n void finish(){',s0);need(a[:s0]==b[:s] and a[e0:]==b[e:],'All other SessionImpl behavior remains byte-identical');method=b[s:e]
 tokens=['allocation->kind==1','!allocation->source_freed&&!allocation->cleanup_freed','((next-begin)&3U)==0','std::uint64_t(next)<=std::uint64_t(begin)+allocation->extent','auto oldbytes=binding->guest_bytes(begin,oldextent)','lb::dispatch_body(0x78004a36,&s,binding.get())','current==allocation','published_next==std::uint64_t(published)+used+4','growth_after==growth_before||growth_after==growth_before+1','a[14]==1&&a[15]==1','a[22]==begin&&a[16]==oldacquired&&a[12]==a[17]','size_calls==(grew?2U:1U)&&realloc_calls==unsigned(grew)','current->generation==oldgeneration','current->extent==binding->native_apis_[last_size].words[17]','auto expected=binding->native_apis_[last_size].outputs[0]','g[2]==0x78011c27','g[7]>=oldextent&&g[7]==g[8]','binding->native_apis_[first_size].words[17]<std::uint64_t(used)+4','g[8]==binding->native_apis_[last_size].words[17]','g[9]==g[8]+16','g[10]==((g[9]+15)&~15ULL)','g[15]==current->generation&&g[15]>oldgeneration','g[19]==1&&g[20]==g[10]&&g[21]==0&&g[22]==1&&g[23]==0','for(unsigned i=24;i<32;++i)require(g[i]==0','current->capacity==0','current->pending_native.empty()&&current->retired_guest==0','inputs[0]==binding->native_apis_[last_size].outputs[0]','outputs[0]==current->initial','published==(g[18]?oldcursor:begin)','auto expected=current->initial','binding->guest_bytes(published,oldextent)==oldbytes']
 for t in tokens:need(t in method,'Complete finite guard semantic relation: '+t)
 need(method.count('std::memcpy(expected.data()+used,&callback,4)')==2,'Exactly callback DWORD overlays for measured-size and grown raw outputs')
 names=re.findall(r'std::string_view\(spec->name\)=="([^"]+)"',method);need(names==['HeapSize','HeapReAlloc','EnterCriticalSection','LeaveCriticalSection'],'Exact finite positive API allowlist')
 source=R/'reports/m4-widget-growth-review/source-review-r1/report.json';sr=raw(source);need(hashlib.sha256(sr).hexdigest()=='d6f76cacd9cdeb9644b67091a5be0d884c3abce732ec6b0c9f08bd624068243c','Independent 62 whole-PC source proof');sj=json.loads(sr);need(sj['passed'] and sj['whole_physical_instructions']==62 and not sj['archive_reader_opened'],'Closed ordinary physical source proof')
 for p,v in sj['files'].items():need(hashlib.sha256(raw(p)).hexdigest()==v['sha256'],'Recomputed successful physical source dependency chain')
 proto=raw(J/'joint_protocol.hpp').decode();m=re.search(r'entries\{([^}]*)\}',proto);need(m,'Current selected table');entries=[int(x,16) for x in re.findall(r'0x[0-9a-f]+',m[1])]
 game=raw(R/'MW3/Mech3.exe');need(hashlib.sha256(game).hexdigest()=='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf','Physical admitted game image');pe=struct.unpack_from('<I',game,0x3c)[0];opt=pe+24;os=struct.unpack_from('<H',game,pe+20)[0];base=struct.unpack_from('<I',game,opt+28)[0]
 def physical(a,n):
  r=a-base;found=[]
  for i in range(struct.unpack_from('<H',game,pe+6)[0]):
   q=opt+os+i*40;va,rs,rp=struct.unpack_from('<III',game,q+12)
   if va<=r and r+n<=va+rs:found.append(game[rp+r-va:rp+r-va+n])
  need(len(found)==1 and len(found[0])==n,'Unique whole physical game source interval');return found[0]
 table=struct.unpack('<145I',physical(0x5e0000,145*4));selected=[x for x in table if x in entries];need(selected==entries and len(entries)==138 and entries[14:16]==[0x4040f0,0x40e250],'Source-owned selected phase14 warm registry before first borrowed phase15')
 rc=raw(J/'registration_contract.hpp').decode();need('0x4040f0' in rc,'Earlier ordinary initializer is an actual admitted callback registration root');native=raw(J/'native_main.cpp').decode();need('c->registry_->enter(r.cpu().eip)' in native and 'r_.call_direct(item.target,{broker})' in native,'Same registry source-call route in selected physical chronology')
 need(physical(0x404110,14)==bytes.fromhex('6820414000e826801a0083c404c3'),'Whole physical earlier registration tail calls actual onexit wrapper')
 diff=out/'guard-diff.txt';diff.write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='service-preparation-r2/session_impl.inc',tofile='service-preparation-r3/session_impl.inc')));raw(diff);raw(__file__);raw(sys.executable)
 report={'passed':True,'scope':'Unexecuted additive borrowed onexit guards for current connected138 physical chronology; complete literal provider and native allocator retained','service_preparation_sha256':hashlib.sha256(prepbytes).hexdigest(),'physical_source_review_sha256':hashlib.sha256(sr).hexdigest(),'copied_source_files':72,'byte_identical_source_files':71,'changed_files':changed,'finite_guard_hunks':2,'finite_semantic_guard_relations':len(tokens),'whole_physical_provider_instructions':62,'selected_source_table_targets':138,'earlier_source_registration_phase':14,'first_borrowed_widget_phase':15,'positive_API_allowlist':names,'normal_complete_capacity_output_plus_callback':True,'growth_complete_native_output_plus_callback':True,'old_complete_extent_carry':True,'first_and_second_size_measurements_separately_joined':True,'actual_generation_and_alias_transport_joined':True,'fresh_standalone_lazy_lock_admitted':False,'standalone_scope_limit':'A fresh registry with lock13 not yet source-initialized can invoke genuine HeapAlloc and InitializeCriticalSection; those cold APIs are outside this connected-positive allowlist. Current physical chronology source-registers through 4040F0 before phase15.','native_worker_executed':False,'archive_reader_opened':False,'capture_opened':False,'source_output_equivalence_claimed':False,'initializer_credit':0,'files':PINS}
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'passed':True,'reader_opened':False}))
if __name__=='__main__':main(sys.argv[1])
