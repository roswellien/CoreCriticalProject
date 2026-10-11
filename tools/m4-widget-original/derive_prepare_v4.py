"""Add true GDI-boundary selectors/descriptor observations without widening ABI."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-widget-original';P=R/'reports/m4-widget-original/preparation-r4/report.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('Exact unique derivation '+a[:90])
 return s.replace(a,b,1)
parent=json.loads(P.read_text());p=T/'prepare_v3.py';header=T/'widget_observer.hpp'
if sha(P)!='877c05e96e45d2d926bd9c2438bb2b07c1d52f010d47f8bcb7c79e3f50a22821' or sha(p)!=parent['files'][str(p.resolve())]or sha(header)!=parent['files'][str(header.resolve())]:raise ValueError('Immutable preparation source')
h=header.read_text()
h=one(h,'Cpu widget_cpu{};','unsigned short widget_ds{},widget_es{},widget_ss{};\nstruct WidgetSegments {unsigned index,DS,ES,SS;unsigned char descriptors[24];};\nstatic_assert(sizeof(WidgetSegments)==40);WidgetSegments widget_segments[384]{};\nCpu widget_cpu{};')
h=one(h,' const auto api=widget_kind/2;', ''' auto&segments=widget_segments[widget_count];segments={};segments.index=widget_count;segments.DS=widget_ds;segments.ES=widget_es;segments.SS=widget_ss;
 const unsigned selectors[3]{widget_ds,widget_es,widget_ss};
 for(unsigned i=0;i<3;++i){LDT_ENTRY descriptor{};if(!GetThreadSelectorEntry(GetCurrentThread(),selectors[i],&descriptor)){widget_error=1;continue;}std::memcpy(segments.descriptors+i*8,&descriptor,8);const unsigned base=descriptor.BaseLow|(static_cast<unsigned>(descriptor.HighWord.Bytes.BaseMid)<<16)|(static_cast<unsigned>(descriptor.HighWord.Bytes.BaseHi)<<24);if(base!=0||!descriptor.HighWord.Bits.Pres||!descriptor.HighWord.Bits.Default_Big)widget_error=1;}
 if(widget_cpu.flags&0x400)widget_error=1;
 const auto api=widget_kind/2;''')
q=T/'widget_observer_v2.hpp'
if q.exists():raise ValueError('Fresh header')
q.write_text(h)
s=p.read_text()
s=one(s,"' mov widget_head,eax',' fxsave widget_fx'", "' mov widget_head,eax',' mov ax,ds',' mov widget_ds,ax',' mov ax,es',' mov widget_es,ax',' mov ax,ss',' mov widget_ss,ax',' fxsave widget_fx'")
s=one(s,"('widget_head','DWORD'),('widget_cpu','BYTE')", "('widget_head','DWORD'),('widget_ds','WORD'),('widget_es','WORD'),('widget_ss','WORD'),('widget_cpu','BYTE')")
s=one(s,"text(R/'tools/m4-widget-original/widget_observer.hpp')", "text(R/'tools/m4-widget-original/widget_observer_v2.hpp')")
s=one(s,'out.append(wstem+"-snapshots.bin",widget_snapshots,widget_count*sizeof(WidgetSnapshot));', 'out.append(wstem+"-snapshots.bin",widget_snapshots,widget_count*sizeof(WidgetSnapshot));out.append(wstem+"-segments.bin",widget_segments,widget_count*sizeof(WidgetSegments));')
s=one(s," pin(__file__);pin(R/'tools/m4-widget-original/derive_prepare_v3.py');", " pin(__file__);pin(R/'tools/m4-widget-original/derive_prepare_v4.py');pin(R/'tools/m4-widget-original/widget_observer.hpp');pin(R/'tools/m4-widget-original/prepare_v3.py');pin(R/'reports/m4-widget-original/preparation-r4/report.json','877c05e96e45d2d926bd9c2438bb2b07c1d52f010d47f8bcb7c79e3f50a22821');pin(R/'tools/m4-widget-original/derive_prepare_v3.py');")
s=one(s,"snapshot_count_bound=384,whole_CRT_phase_endpoint_pages", "snapshot_count_bound=384,actual_GDI_selector_descriptor_bytes_per_boundary=40,actual_DS_ES_SS_flatness_observed=True,whole_CRT_phase_endpoint_pages")
q=T/'prepare_v4.py'
if q.exists():raise ValueError('Fresh additive source')
q.write_text(s)
print(json.dumps(dict(passed=True,source=str(q),sha256=sha(q))))
