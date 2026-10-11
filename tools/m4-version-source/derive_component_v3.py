"""Additive exact CALL pre-store timing correction after the admitted O0 failure."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
src=P/'component_v1.cpp';s=src.read_text()
s=once(s,'std::vector<Access>accesses;','std::vector<Access>accesses;std::vector<std::array<unsigned,8>>call_store_timing;')
s=once(s,'need(n==4&&a==s.gpr.rsp.dword&&v==pc+row.size&&frames.size()<32,"Actual source CALL committed exact return/frame");frames.push_back({0,a,unsigned(v),pc});','const auto pre=s.gpr.rsp.dword;need(literal::call_pre_store(pc)&&n==4&&!s.addr.ss_base.dword&&pre>=4&&a==pre-4&&a>=r.stack_low().value&&std::uint64_t(a)+4<=r.stack_top().value&&v==pc+row.size&&frames.size()<32,"Exact compiled CALL pre-ESP-store return/frame timing");call_store_timing.push_back({pc,pre,a,unsigned(v),s.addr.ss_base.dword,row.size,unsigned(accesses.size()-1),0});frames.push_back({0,a,unsigned(v),pc});')
s=once(s,'need(!f.target&&f.frame==s.gpr.rsp.dword,"Actual committed source CALL before routing");','need(!f.target&&f.frame==s.gpr.rsp.dword&&!call_store_timing.empty()&&call_store_timing.back()[0]==f.site&&call_store_timing.back()[2]==f.frame&&call_store_timing.back()[3]==f.ret,"Same exact CALL store then committed source ESP before routing");')
s=once(s,'dump(p+"/frames.bin",frames.data(),frames.size()*sizeof(Frame));','dump(p+"/frames.bin",frames.data(),frames.size()*sizeof(Frame));dump(p+"/call-store-timing.bin",call_store_timing.data(),call_store_timing.size()*sizeof(call_store_timing[0]));')
q=P/'component_v2.cpp';assert not q.exists();q.write_text(s)
p=P/'prepare_component_v2.py';s=p.read_text();s=once(s,"R/'tools/m4-version-source/component_v1.cpp'","R/'tools/m4-version-source/component_v2.cpp'")
insert='''  # The physical CALL rows and frozen LLVM determine the one accepted hook timing.
  vg=read(pp.parent/'game-new-graphs.json');cg={**vg,**{str(e):graphs[str(e)]for e in(0x5ac110,0x5ac140)}}
  timing=[]
  for rel in relations:
   lines=Path(rel['component_IR']).read_text().splitlines();templates=[]
   for j,line in enumerate(lines):
    if 'call noundef ptr @mw34_version_game_write32'not in line or j+3>=len(lines)or'i32 2472'not in lines[j+2]:continue
    block=lines[max(0,j-10):j+4];t='\\n'.join(block)
    m=re.search(r'(%[0-9]+) = getelementptr inbounds nuw i8, ptr %state, i32 2312\\n  (%[0-9]+) = load i32, ptr \\1, align 8\\n  (%[0-9]+) = add i32 \\2, -4',t);need(m,'Exact frozen CALL reads incoming State ESP then computes minus4')
    esp,old,new=m.groups();need(lines[j+1]=='  store i32 '+new+', ptr '+esp+', align 8','Exact frozen CALL return write precedes State ESP commit')
    m2=re.search(r'(%[0-9]+) = getelementptr inbounds nuw i8, ptr %state, i32 2120\\n  (%[0-9]+) = load i32, ptr \\1, align 8\\n  (%[0-9]+) = add i32 (%[0-9]+), (%[0-9]+)',t);need(m2 and set(m2.groups()[-2:])=={new,m2.group(2)},'Exact frozen CALL address is newESP plus SSbase')
    need('i32 noundef '+m2.group(3)+','in line,'Same exact CALL return store address operand');templates.append(dict(IR_line=j+1,whole_template=t,template_sha256=hashlib.sha256(t.encode()).hexdigest(),ESP_commit_IR_line=j+2))
   calls=[v for v in cg[str(rel['entry'])]['instructions']if v['mnemonic']=='call'];need(len(calls)==len(templates),'Every physical CALL has exactly one guarded frozen pre-store template')
   for v,t in zip(calls,templates):timing.append(dict(body=rel['entry'],pc=v['pc'],size=v['size'],physical_bytes=v['bytes'],**t))
  need(len(timing)==14 and len({v['pc']for v in timing})==14,'Exact fourteen complete physical CALLs, including denied cold branch')
  h+=['inline bool call_pre_store(unsigned pc){switch(pc){']+['case %d:return true;'%v['pc']for v in timing]+['default:return false;}}']
  (out/'call-store-timing-relations.json').write_text(json.dumps(timing,indent=2)+'\\n')
'''
s=once(s,"  h+=['};','inline const Instruction*instruction", "  h+=['};']\n"+insert+"  h+=['inline const Instruction*instruction")
s=once(s,"  pin(__file__)","  pin(__file__);pin(R/'tools/m4-version-source/derive_component_v3.py');pin(R/'tools/m4-version-source/component_v1.cpp','"+sha(src)+"');pin(R/'reports/m4-version-source/component-preparation-r2/report.json','1143e3cef914a5582e93231a810dfd32cc0eabd94534ccaa7025045b0964ed4d');pin(R/'reports/m4-version-source/fixture-execution-r1/report.json','b6d31a9706d9f9bcae16a0cf8ebdc2fe1930cad6a28e2f244651b28da3beb7b6')")
s=once(s,'native_executed=False,original_executed=False,initializer_credit=0','compiled_CALL_pre_store_timing_rows=len(timing),CALL_dispatch_committed_ESP_guard_retained=True,native_executed=False,original_executed=False,initializer_credit=0')
q=P/'prepare_component_v3.py';assert not q.exists();q.write_text(s)
print(json.dumps(dict(component_sha256=sha(P/'component_v2.cpp'),recipe=str(q),sha256=sha(q),native_executed=False)))
