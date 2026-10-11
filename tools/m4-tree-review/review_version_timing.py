"""Independent actual physical CALL/LLVM pre-store timing correction."""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir();files={};counts=collections.Counter();passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or v==h;files[str(p)]=v;return p
 def read(p,h):
  d=json.loads(pin(p,h).read_bytes());assert d['passed']
  for p,h in d['files'].items():pin(p,h)
  return d
 def once(t,a,b):assert t.count(a)==1,(a,t.count(a));return t.replace(a,b)
 try:
  old=R/'reports/m4-version-source/component-preparation-r2';new=R/'reports/m4-version-source/component-preparation-r3'
  read(R/'reports/m4-tree-review/version-prelaunch-r3/report.json','25a2ebefd990be496e761d4dd9d03f1e7fbc0fe54c866a5d19fd3a8e8be6146a')
  p=read(new/'report.json','e47cc5974bc3da9ea51ce56e90090568f0451d9fad065a9fef22428e6a926217');assert p['compiled_CALL_pre_store_timing_rows']==14
  timing=json.loads(pin(new/'call-store-timing-relations.json').read_bytes());assert len(timing)==14 and len({x['pc']for x in timing})==14
  for row in p['namespace_relations']:
   assert pin(new/Path(row['component_IR']).name).read_bytes()==pin(old/Path(row['component_IR']).name).read_bytes();counts['whole_retained_IRs']+=1
  expected=pin(old/'component.cpp').read_text();current=pin(new/'component.cpp').read_text()
  expected=once(expected,'std::vector<Access>accesses;','std::vector<Access>accesses;std::vector<std::array<unsigned,8>>call_store_timing;')
  expected=once(expected,'need(n==4&&a==s.gpr.rsp.dword&&v==pc+row.size&&frames.size()<32,"Actual source CALL committed exact return/frame");','const auto pre=s.gpr.rsp.dword;need(literal::call_pre_store(pc)&&n==4&&!s.addr.ss_base.dword&&pre>=4&&a==pre-4&&a>=r.stack_low().value&&std::uint64_t(a)+4<=r.stack_top().value&&v==pc+row.size&&frames.size()<32,"Exact compiled CALL pre-ESP-store return/frame timing");call_store_timing.push_back({pc,pre,a,unsigned(v),s.addr.ss_base.dword,row.size,unsigned(accesses.size()-1),0});')
  expected=once(expected,'need(!f.target&&f.frame==s.gpr.rsp.dword,"Actual committed source CALL before routing");','need(!f.target&&f.frame==s.gpr.rsp.dword&&!call_store_timing.empty()&&call_store_timing.back()[0]==f.site&&call_store_timing.back()[2]==f.frame&&call_store_timing.back()[3]==f.ret,"Same exact CALL store then committed source ESP before routing");')
  expected=once(expected,'dump(p+"/frames.bin",frames.data(),frames.size()*sizeof(Frame));','dump(p+"/frames.bin",frames.data(),frames.size()*sizeof(Frame));dump(p+"/call-store-timing.bin",call_store_timing.data(),call_store_timing.size()*sizeof(call_store_timing[0]));')
  assert expected==current,'Whole complete component delta is only the exact measured timing contract/observation'
  oldh=pin(old/'literals.hpp').read_text();newh=pin(new/'literals.hpp').read_text();assert newh.startswith(oldh)
  extra=newh[len(oldh):];pcs=re.search(r'call_pre_store\(unsigned pc\).*?\{([^}]+)\}',extra,re.S);assert pcs
  # The source header is also checked as a complete finite switch/set, below.
  numbers={int(x)for x in re.findall(r'\b\d+\b',extra)};assert {x['pc']for x in timing}<=numbers and numbers<={x['pc']for x in timing}|{0,1}
  s=importlib.util.spec_from_file_location('timing_pe',pin(R/'tools/analysis/pe.py'));PE=importlib.util.module_from_spec(s);s.loader.exec_module(PE);game=PE.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  for row in timing:
   text=pin(new/('f_%x-host.ll'%row['body'])).read_text();template=row['whole_template'];assert hashlib.sha256(template.encode()).hexdigest()==row['template_sha256']and text.count(template)==1
   lines=text.splitlines();call=lines[row['IR_line']-1];store=lines[row['ESP_commit_IR_line']-1];assert row['ESP_commit_IR_line']==row['IR_line']+1 and '@mw34_version_game_write32'in call
   a=re.search(r'(%\d+) = getelementptr[^\n]*ptr %state, i32 2312',template);assert a
   oldesp=re.search(r'(%\d+) = load i32, ptr '+re.escape(a[1])+r',',template);assert oldesp
   decremented=re.search(r'(%\d+) = add i32 '+re.escape(oldesp[1])+r', -4',template);assert decremented
   ss=re.search(r'(%\d+) = getelementptr[^\n]*ptr %state, i32 2120',template);assert ss
   ssvalue=re.search(r'(%\d+) = load i32, ptr '+re.escape(ss[1])+r',',template);assert ssvalue
   effective=re.search(r'(%\d+) = add i32 (?:'+re.escape(decremented[1])+r', '+re.escape(ssvalue[1])+r'|'+re.escape(ssvalue[1])+r', '+re.escape(decremented[1])+r')',template);assert effective
   assert re.search(r'@mw34_version_game_write32\([^\n]*i32 noundef '+re.escape(effective[1])+r',',call)
   assert re.search(r'store i32 '+re.escape(decremented[1])+r', ptr '+re.escape(a[1])+r',',store)
   raw=game.read(game.rva_range(row['pc']-game.image_base,row['size'])[0],row['size']);assert raw.hex()==row['physical_bytes']and(raw[0]==0xe8 and len(raw)==5 or raw[:2]==b'\xff\x15'and len(raw)==6)
   counts['whole_physical_CALL_SSA_templates']+=1
  pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  d=dict(passed=passed,scope='Exact same-instruction physical CALL preESP-minus4/SS/effective address/return store and following committed ESP publication across14 immutable LLVM templates; whole source correction retains strict post-dispatch frame/return guards; current worker execution remains separate',counts=dict(counts),component_preparation_sha256='e47cc5974bc3da9ea51ce56e90090568f0451d9fad065a9fef22428e6a926217',worker_launched=False,archive_reader_opened=False,initializer_credit=0,files=files);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=hashlib.sha256(q.read_bytes()).hexdigest(),counts=dict(counts),files=len(files))))
if __name__=='__main__':main(sys.argv[1])
