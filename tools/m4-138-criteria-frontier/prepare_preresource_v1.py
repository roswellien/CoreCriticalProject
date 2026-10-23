"""Exact legacy12 causal faults on the current138 Context, build-only recipe."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out=R/'reports/m4-138-preresource-controls/preparation-r1';assert not out.exists();out.mkdir(parents=True)
pins={}
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
pp=pin(R/'reports/m4-joint-startup138/preparation-r4/report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a');pr=json.loads(pp.read_bytes())
bp=pin(R/'reports/m4-joint-startup138/build-r5/build.json','7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47');b=json.loads(bp.read_bytes());assert pr['passed'] and b['passed'] and b['preparation_sha256']==sha(pp)
old=R/'reports/m4-mfc1168-native/connected-controls-preparation-r6';pin(old/'report.json','0a45415c36b76ae10669f9ecbb8289fac4878b9e564f33212128a5c22ac12136');legacy=pin(old/'connected_controls.inc').read_text();parent=pin(pp.parent/'native_main.cpp').read_text();s=parent;changes=[]
def one(a,z):
 global s
 assert s.count(a)==1;s=s.replace(a,z);changes.append(dict(before=a,after=z))
one('namespace mc=mw34::m4_mfc1168_connected;','namespace mc=mw34::m4_mfc1168_connected;\nstatic void mfc_control_entry(mw34::m4_runtime::Runtime&,State&);')
one('snapshot(r,c->s_,true);c->mfc_component_=', 'snapshot(r,c->s_,true);mfc_control_entry(r,c->s_);c->mfc_component_=')
one(' unsigned completed{};', ''' bool has_component()const noexcept{return bool(mfc_component_);}
 void control_checkpoint(std::string_view name){if(mfc_component_)mfc_component_->checkpoint(name);}
 void control_cleanup(){if(mfc_component_)mfc_component_->cleanup_failed();}
 void control_widget_snapshot(std::string_view name){require(widget_component_&&registry_->live_handle(),"Current pre-resource widget context exists before any selected root");widget_component_->checkpoint(name);widget_whole_checkpoint(r_,name);}
 unsigned completed{};''')
one('std::vector<mw34::m4_mixed::Native>*records;bool completed;','std::vector<mw34::m4_mixed::Native>*records;bool completed,retry;')
one('p->completed=p->context->invoke_selected_table(p->sequence,p->repeat,p->top,*p->records);','if(p->retry){try{p->context->runtime().call_direct({mc::root},{mw34::m4_mixed::broker});p->completed=false;}catch(const mw34::m4_runtime::Fault&e){p->completed=e.reason()==mw34::m4_runtime::FaultReason::poisoned;}}else p->completed=p->context->invoke_selected_table(p->sequence,p->repeat,p->top,*p->records);')
inverse=s
for x in reversed(changes):inverse=inverse.replace(x['after'],x['before'])
assert inverse==parent;(out/'native_main.cpp').write_text(s)
writer='''// Fresh ordinary outputs only. No canonical writer is invoked by this main.
#define main unused_current138_positive_main
#include "native_main.cpp"
#undef main
#include "connected_literals.hpp"
struct PreResourceWriter {
 std::filesystem::path out;
 explicit PreResourceWriter(const char*p):out(p){need(!std::filesystem::exists(out),"Fresh immutable pre-resource directory");std::filesystem::create_directories(out);}
 void append(const std::string&name,const void*p,std::size_t n){need(name.find("..") ==std::string::npos&&!std::filesystem::path(name).is_absolute(),"Relative sealed output");auto q=out/name;need(!std::filesystem::exists(q),"Unique pre-resource output");std::filesystem::create_directories(q.parent_path());std::ofstream f(q,std::ios::binary);need(bool(f),"Open ordinary pre-resource output");f.write(static_cast<const char*>(p),n);need(bool(f),"Whole ordinary output");}
 void finish(){}
};
'''
c=legacy;cc=[]
def change(a,z):
 global c
 assert c.count(a)==1;c=c.replace(a,z);cc.append(dict(before=a,after=z))
change(' if(phase!=13)return;using namespace mw34;', ' if(phase>=14)throw std::runtime_error("Expected pre-resource refusal did not occur; prefix bound reached");if(phase!=13)return;using namespace mw34;')
change('mw34::capture_direct::Writer&w','PreResourceWriter&w')
change('need(argc==6,"Connected causal control exact inputs/fresh output");','need(argc==8,"Current138 pre-resource control exact4images/fresh-output ROOT-admission mode1..12");const unsigned requested=unsigned(std::stoul(argv[7]));need(requested>=1&&requested<=12&&std::strlen(argv[6])==64,"Exact single authored legacy mode and ROOT admission");')
change('capture_direct::Options options;options.reports_root=std::filesystem::current_path()/"reports";capture_direct::Writer writer(argv[5],options);const unsigned header[]{1,12,14,17,sizeof(Native)};', 'PreResourceWriter writer(argv[5]);writer.append("admission.txt",argv[6],64);const unsigned header[]{2,12,14,17,sizeof(Native),requested};')
change('for(unsigned mode=1;mode<=12;++mode){','for(unsigned mode=requested;mode<=requested;++mode){')
change('mfc_control_mode=mode;mfc_output.clear();Context context', 'mfc_control_mode=mode;mfc_output.clear();widget_output.clear();Context context')
change('context.control_cleanup();context.control_checkpoint("cleaned");','context.control_cleanup();context.control_checkpoint("cleaned");context.cleanup_widgets();for(const auto&row:widget_output)writer.append(prefix+"Widget/"+row.name,row.bytes.data(),row.bytes.size());')
change('12 actual connected MFC denials, unchanged poisoned retries and owned cleanup; no initializer credit','One actual current138 legacy MFC denial, unchanged poisoned retry, current widget and MFC/registry cleanup; no initializer credit')
change('put("Native.bin",mw34::m4_mixed::observation,sizeof(mw34::m4_mixed::Native));','put("Native.bin",mw34::m4_mixed::observation,sizeof(mw34::m4_mixed::Native));std::array<std::byte,64>frame{};need(r.cpu().eip==mc::root&&r.cpu().esp==mw34::m4_mixed::frame,"Actual committed MFC CALL frame");r.memory().read({r.cpu().esp},frame);put("entry-frame64.bin",frame.data(),frame.size());')
change('w.append(p+"FX.bin",c.runtime().fx().data(),512);','w.append(p+"FX.bin",c.runtime().fx().data(),512);c.control_widget_snapshot(p.ends_with("retry-before/")?"pre-resource-retry-before":"pre-resource-retry-after");')
ci=c
for x in reversed(cc):ci=ci.replace(x['after'],x['before'])
assert ci==legacy;(out/'controls_main.cpp').write_text(writer+c)
for p in out.iterdir():pin(p)
pin(__file__);pin(sys.executable)
report=dict(passed=True,scope='Unexecuted single-mode current138 Context legacy12 pre-resource counterfactual recipe; no historical control transfer assumed',parent_preparation=str(pp),parent_preparation_sha256=sha(pp),parent_build=str(bp),parent_build_sha256=sha(bp),parent_main_changes=changes,legacy_controls_changes=cc,whole_parent_main_inverse=True,whole_legacy_controls_inverse=True,source_images=[dict(path=str(R/'MW3/Mech3.exe'),bytes=2384384),dict(path=str(R/'MW3/MSVCP60.dll'),bytes=565760),dict(path=str(R/'MW3/MSVCRT.dll'),bytes=266293),dict(path=str(R/'MW3/MFC42.dll'),bytes=954128)],cases=dict(modes=list(range(1,13)),repeat=0,CW=127,TOP=0,prefix_completed=13,failed_phase=13,target=0x5ae3e4,mode11_real_entry_frame_bytes=64),required_prelaunch=['whole Context source inverse','same all provider/literal object inputs perlevel','whole revised main/component CALL and initialized TLS attribution','whole85B hardware CALL to exact revised guarded function plus unwind','source_frame64 actual CALL ESP and root before Component construction','current widget_fault marking and actual both-domain cleanup','all12 faults refuse before APIs/resources; this remains unproven until actual controlled run'],worker_executed=False,execution_admitted=False,initializer_credit=0,files=pins)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(sha(out/'report.json'))
