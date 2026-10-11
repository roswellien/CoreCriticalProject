"""Add measured ES/DS/SS descriptor admission to the frozen CRT trace preparation."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-formatting-original'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(s,a,b):
 assert s.count(a)==1,a[:70];return s.replace(a,b,1)
def main(name):
 parent=BASE/'trace-preparation-r1';out=BASE/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix!='.mwb';v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 old=json.loads(pin(parent/'report.json','e8edc96a9c0e22403940bfb76e5b11a49dc82eab37df668e155ac95009b5bb52').read_bytes())
 for p,h in old['files'].items():pin(p,h)
 out.mkdir(parents=True)
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(pin(p).read_bytes())
 kernel=(out/'tree_trace.hpp').read_text();kernel=one(kernel,'static unsigned tree_trace_count{},tree_trace_active{},tree_trace_owner{};','''static unsigned tree_trace_count{},tree_trace_active{},tree_trace_owner{};
struct TreeTraceSelector {unsigned selector,base,limit;LDT_ENTRY descriptor;};
static_assert(sizeof(TreeTraceSelector)==20);
static TreeTraceSelector tree_trace_selectors[3]{};static unsigned tree_trace_selectors_ready{};''')
 kernel=one(kernel,'tree_trace_count=0;tree_trace_owner=GetCurrentThreadId();','tree_trace_count=0;tree_trace_owner=GetCurrentThreadId();tree_trace_selectors_ready=0;std::memset(tree_trace_selectors,0,sizeof(tree_trace_selectors));')
 marker=' static unsigned pending=~0U;static TreeTraceEvent measured{};'
 code=''' unsigned selectors_ready{};get(&tree_trace_selectors_ready,&selectors_ready,4);
 if(!selectors_ready){TreeTraceSelector observations[3]{};const unsigned selectors[3]{context.SegDs,context.SegEs,context.SegSs};
  for(unsigned i=0;i<3;++i){auto&o=observations[i];o.selector=selectors[i];require(GetThreadSelectorEntry(thread.value,o.selector,&o.descriptor),"Actual stopped original data/extra/stack segment descriptor");const auto&b=o.descriptor.HighWord.Bits;o.base=o.descriptor.BaseLow|(b.BaseMid<<16)|(b.BaseHi<<24);o.limit=o.descriptor.LimitLow|(b.LimitHi<<16);if(b.Granularity)o.limit=(o.limit<<12)|0xfff;require(o.base==0&&o.limit==0xffffffff,"Actual original flat32 ES/DS/SS admission for string and explicit source accesses");}
  put(tree_trace_selectors,observations,sizeof(observations));selectors_ready=1;put(&tree_trace_selectors_ready,&selectors_ready,4);
 }
'''
 kernel=one(kernel,marker,code+marker);(out/'tree_trace.hpp').write_text(kernel)
 ref=(out/'reference.cpp').read_text();marker='out.append(trace_stem+"events.bin",tree_trace_events,tree_trace_count*sizeof(TreeTraceEvent));';ref=one(ref,marker,marker+'out.append(trace_stem+"segments.bin",tree_trace_selectors,sizeof(tree_trace_selectors));out.append(trace_stem+"segments-ready.bin",&tree_trace_selectors_ready,4);');(out/'reference.cpp').write_text(ref)
 pin(__file__)
 for p in out.iterdir():pin(p)
 report={**old,'scope':old['scope']+'; actual stopped ES/DS/SS descriptors prove flat32 source string/stack address bases','parent_trace_preparation_sha256':sha(parent/'report.json'),'segment_evidence_bytes':60,'segment_evidence':{'selectors':['DS','ES','SS'],'source':'GetThreadSelectorEntry on actual stopped original owner thread before first traced instruction','required_base':0,'required_limit':0xffffffff},'files':pins}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
