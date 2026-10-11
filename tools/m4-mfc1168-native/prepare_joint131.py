"""Full131 candidate from accepted130 and the executed strong connected prefix.

Only one fullsix schedule is generated. Existing410 literalobjects are reused.
Fresh genuine six-sequence ownership/paired evidence remains a required gate.
"""
from pathlib import Path
import hashlib,json,re,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(t,a,b):assert t.count(a)==1,(a,t.count(a));return t.replace(a,b)
def main(name):
 out=R/'reports/m4-joint-startup131'/name;assert not out.exists();out.mkdir(parents=True);pins={};generated={};parent={};selected=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;(str(p)not in pins or pins[str(p)]==v)or(_ for _ in()).throw(ValueError('Stable input'));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def write(p,b):p.write_bytes(b if isinstance(b,bytes)else b.encode());generated[str(p.resolve())]=sha(p)
 try:
  pp=pin(R/'reports/m4-mfc1168-native/connected-fixture-preparation-r5/report.json','a7985e57a3a437fe6b19a600507ebeac33dac79ea0bae825b35133095f3f8924');parent=read(pp)
  oldpp=pin(R/'reports/m4-joint-startup130/preparation-r2/report.json','060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c');old=read(oldpp)
  for p,h in parent['files'].items():pin(p,h)
  for key,digest in [('connected-source-r4','a22b94ca3a5ccf6f1fb57bbe40b03ee97ac8d7770f991a2cb80b3cecf354d30d'),('connected-resources-r1','abd7b109aa55654766e0a77ae0f2ffda8118c0a8f5388c9a88792dd49b714885')]:assert read(R/'reports/m4-mfc1168-native'/key/'report.json',digest)['passed']
  assert parent['passed']and old['passed'];selected=sorted(old['selected_order']+[dict(entry=0x5ae3e4,slot=0x5e0040)],key=lambda x:x['slot']);assert len(selected)==131 and selected[13]==dict(entry=0x5ae3e4,slot=0x5e0040)and [r for r in selected if r['entry']!=0x5ae3e4]==old['selected_order']
  for p in pp.parent.rglob('*'):
   if p.is_file()and p.name!='report.json':q=out/p.relative_to(pp.parent);q.parent.mkdir(parents=True,exist_ok=True);write(q,pin(p).read_bytes().replace(pp.parent.as_posix().encode(),out.as_posix().encode()))
  protocol=(out/'joint_protocol.hpp').read_text();protocol,n=re.subn(r'constexpr std::array<std::uint32_t,14> entries\{[^\n]+\};','constexpr std::array<std::uint32_t,131> entries{'+','.join(hex(x['entry'])for x in selected)+'};',protocol);assert n==1;write(out/'joint_protocol.hpp',protocol)
  text=(out/'native_main.cpp').read_text();text=one(text,'phase==14&&r_.calls().size()==14&&r_.translation_count()==132','phase==131&&r_.calls().size()==134&&r_.translation_count()==132')
  text=text.replace('records.reserve(14)','records.reserve(131)').replace('records.size()==14','records.size()==131').replace('total==14','total==786').replace('seq==1','seq==6').replace('1,1,14,14,17,sizeof(Native)','1,6,131,786,17,sizeof(Native)').replace('1,1,sizeof(SequenceRecord),17','1,6,sizeof(SequenceRecord),17')
  text=one(text,'const std::array<std::array<unsigned,3>,1>cases{{{0,0x7f,0}}};','const std::array<std::array<unsigned,3>,6>cases{{{0,0x7f,0},{0,0x37f,7},{0,0xf7f,0},{1,0x47f,7},{1,0xa7f,0},{1,0xe7f,7}}};')
  original=pin(oldpp.parent/'native_main.cpp').read_text();start=original.index('  // Genuine source root replay is a separate growth experiment, outside selected-table credit.');end=original.index('DirectPhaseWriter::current=nullptr;total+=records.size();++seq;',start)
  current='  context.registry().finish();direct.prefix=prefix+"registry-cleaned/";context.registry().dump(&DirectPhaseWriter::sink,&direct);need(!context.registry().live_handle(),"Current registry owner cleanup");';text=one(text,current,original[start:end])
  text=text.replace('One genuine-domain persistent14-root native prefix and owned cleanup complete; fullM4 incomplete','Six persistent131-root sequences and source growth/owned cleanup complete; fullM4 incomplete').replace('14native phases in1persistent connected MFC prefix','786native phases in6persistent131-root sequences');write(out/'native_main.cpp',text)
  cmake=(out/'CMakeLists.txt').read_text().replace('mw34_mfc1168_connected','mw34_joint_startup131');write(out/'CMakeLists.txt',cmake)
  write(out/'selected-order.json',json.dumps(selected,indent=2)+'\n')
  contracts=dict(root=0x5ae3e4,slot=0x5e0040,phase=13,registration_callback=None,registration_callbacks=101,literal_objects=410,Runtime_translations=132,Runtime_calls_per_selected_sequence=134,selected_roots=131,sequences=6,phases_per_level=786,Native_bytes=159716,Sequence_bytes=147400,source_pages_fixed=17,source_pages_external=29,source_page_union=46,MFC_extra_regions=12,normal_MFC_named_API_pairs_per_sequence=4,normal_MFC_native_service_calls_per_sequence=13,guest_CS24=0x33007000,component_host_CS_bytes=40,component_host_resources_released_after_root=True,prior130_provider_resource_CS_count=5,new_component_CS_count=1,loader_graph_from_genuine_original='CW007f/TOP0 first13→MFC cached1252 BEFORE only',pending_domains=['Fresh genuine original131 six-sequence carried graph/CRT/TIB and fullpaired proof','Fresh full131 source/actual provider lifecycle including later CP25 target use','Current12 connected causal denials/retries','Complete actual linked full6 caller/source/refusal proof'],initializer_credit=0)
  write(out/'integration-contracts.json',json.dumps(contracts,indent=2)+'\n');[pin(p,h)for p,h in generated.items()];pin(__file__);pin(sys.executable)
  for p,h in pins.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(parent);report.update(passed=passed,scope='Unexecuted full131 connected native candidate, exact130 order plus nonregistering5AE3E4; current410objects/current130Context, wholeBEFORE typed additions and one6sequence schedule',selected_order=selected,source_roots=131,source_sequences=6,current_registration_callbacks=101,Runtime_translations=132,Runtime_calls_per_selected_sequence=134,literal_objects_per_level=410,parent_joint130_preparation=str(R/'reports/m4-joint-startup130/preparation-r2/report.json'),parent_positive_preparation=str(R/'reports/m4-mfc1168-native/connected-fixture-preparation-r5/report.json'),generated_sources=generated,files=pins,worker_executed=False,execution_admitted=False,initializer_credit=0,current131_acceptance=False,pending_genuine_full131_scope=True)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
