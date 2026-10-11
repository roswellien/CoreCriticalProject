"""Extend the successful52-body component with literal fps formatting only."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'tools/m4-fps-native'
prior=R/'reports/m4-widget-native/preparation-r6/component.cpp';s=prior.read_text();relations=[]
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);relations.append(dict(before=a,after=b))
change('constexpr std::array<unsigned,6> import_PCs{0x5a013c,0x5a063f,0x5a074b,0x517287,0x5ac11e,0x5ac580};','constexpr std::array<unsigned,7> import_PCs{0x5a013c,0x5a063f,0x5a074b,0x517287,0x5ac11e,0x5ac580,0x5a2f68};')
change('constexpr std::array<unsigned,6> import_slots{0x5bb070,0x5bb074,0x5bb068,0x5bb064,0x5bb52c,0x5bb530};','constexpr std::array<unsigned,7> import_slots{0x5bb070,0x5bb074,0x5bb068,0x5bb064,0x5bb52c,0x5bb530,0x5bb53c};')
change('for(unsigned k=0;k<6;++k){const auto&v=input.imports[k];','for(unsigned k=0;k<7;++k){const auto&v=input.imports[k];')
change('else require(v.projected==v.raw,"Unused cold import stays raw and is never admitted");','else if(k==6)require(v.projected==0x780230dd,"Exact literal finite vsprintf route; no host formatter");else require(v.projected==v.raw,"Unused cold import stays raw and is never admitted");')
change('for(unsigned k=0;k<6;++k){const auto&i=input.imports[k];','for(unsigned k=0;k<7;++k){const auto&i=input.imports[k];')
change('struct Invoke {Component::Impl *owner;unsigned root;bool cleanup;std::exception_ptr exception;};','''struct FormatRecord {
 std::array<std::uint64_t,16> metadata{};
 m4_runtime::Cpu32 before{},after{};
 std::array<std::byte,512> FX_before{},FX_after{},destination_before{},destination_after{};
 std::array<std::byte,64> frame_before{},frame_after{},va_before{},va_after{};
 std::array<std::byte,16> format{};
};
static_assert(sizeof(FormatRecord)==2528);
struct Invoke {Component::Impl *owner;unsigned root;bool cleanup;std::exception_ptr exception;};''')
change('std::vector<Font>fonts;std::vector<ApiRecord>APIs;','std::vector<Font>fonts;std::vector<ApiRecord>APIs;std::vector<FormatRecord>formats;std::vector<std::array<unsigned,8>>format_dispatches;unsigned format_dispatch_cursor{},format_index{};bool format_live{};')
change('if(literal::instruction(pc)->ret)last_return_PC=pc;','''if(pc==0x7800fcef){
   require(root->root==0x40f000&&format_live&&format_dispatch_cursor<3&&!frames.empty(),"Current literal fps output dispatch lifetime");
   require(n==4&&a==0x780103fa&&v==0x7800fe25&&s.gpr.rax.dword==0&&frames.back().target==0x7800fc9b&&frames.back().site==0x78023105,"Exact current source index0 and whole readonly dispatch cell");
   format_dispatches.push_back({root->root,pc,a,unsigned(v),format_dispatch_cursor,frames.back().frame,unsigned(accesses.size()-1),s.gpr.rax.dword});++format_dispatch_cursor;
  }
  if(literal::instruction(pc)->ret)last_return_PC=pc;''')
change('void*dispatch(unsigned target,bool tail){','''void format_enter(const Frame&f){
  require(root->root==0x40f000&&!format_live&&formats.empty()&&f.site==0x5a2f68&&f.frame==s.gpr.rsp.dword&&f.ret==0x5a2f6e&&std::int64_t(f.frame)-root_frame==-140,"Actual current finite formatter CALL source frame");
  require(!imports.empty()&&imports.back()[1]==f.site&&imports.back()[4]==0x780230dd&&word(f.frame)==f.ret,"Actual formatter import operand and committed return");
  const auto destination=word(f.frame+4),fmt=word(f.frame+8),va=word(f.frame+12);
  require(s.gpr.rsi.dword==root->object&&destination==root->object+0x34&&fmt==0x5e1590&&va==root_frame-108,"Literal LEA source destination/current format/current va_list");
  FormatRecord record;record.before=cpu(s);record.metadata={1,root->root,f.site,0x780230dd,f.frame,f.ret,destination,fmt,va,512,16,64,0,thread,0,0};
  r.memory().read({f.frame},record.frame_before);r.memory().read({destination},record.destination_before);r.memory().read({fmt},record.format);r.memory().read({va},record.va_before);std::copy(r.fx().begin(),r.fx().end(),record.FX_before.begin());
  for(unsigned k=0;k<16;++k)require(std::to_integer<unsigned>(record.format[k])==literal::fps_format[k],"Complete physical narrow fps input; other format domains denied");
  format_index=unsigned(formats.size());formats.push_back(record);format_live=true;checkpoint("formatter-entry");
 }
 void format_return(const Frame&f){
  require(root->root==0x40f000&&format_live&&format_index<formats.size()&&last_return_PC==0x7802311e&&s.gpr.rip.dword==f.ret&&s.gpr.rsp.dword==f.frame+4&&format_dispatch_cursor==3,"Complete literal finite formatter RET and three source dispatches");
  auto&record=formats[format_index];require(record.metadata[4]==f.frame&&record.metadata[5]==f.ret,"Same current formatter lifetime generation");record.after=cpu(s);record.metadata[12]=s.gpr.rax.dword;record.metadata[14]=format_dispatch_cursor;record.metadata[15]=1;
  r.memory().read({f.frame},record.frame_after);r.memory().read({unsigned(record.metadata[6])},record.destination_after);r.memory().read({unsigned(record.metadata[8])},record.va_after);std::copy(r.fx().begin(),r.fx().end(),record.FX_after.begin());format_live=false;checkpoint("formatter-return");
 }
 void*dispatch(unsigned target,bool tail){''')
change('instruction(target);if(target==0x517680)require(!word(0x6384e8),"Current zero font registry source domain");if(target==0x5a2f40)require(!word(s.gpr.rsp.dword+8),"Current null format source domain");','''instruction(target);if(target==0x517680)require(!word(0x6384e8),"Current zero font registry source domain");
  if(target==0x5a2f40)require(word(s.gpr.rsp.dword+8)==(root->root==0x40f000?0x5e1590:0),"Current root literal null or exact fps format source domain");
  if(target==0x780230dd){require(!tail,"Actual formatter cdecl source CALL");format_enter(f);}
  if(target==0x7800fe25)require(tail&&format_live&&root->root==0x40f000&&!format_dispatches.empty()&&format_dispatches.back()[1]==0x7800fcef&&format_dispatches.back()[3]==target&&f.target==0x7800fc9b,"Retained actual source output dispatch tail and same frame");''')
change('frames.pop_back();last_return_PC=0;}','if(f.target==0x780230dd)format_return(f);frames.pop_back();last_return_PC=0;}')
change('selected<6,"Live serial finite widget selected-root invocation"','selected<7,"Live serial finite widget selected-root invocation"')
change('GDI_cursor=virtual_cursor=FS_cursor=operand_cursor=0;active=true;','GDI_cursor=virtual_cursor=FS_cursor=operand_cursor=format_dispatch_cursor=0;active=true;')
change('operand_cursor==root->operand_count,"Complete actual root CALL/virtual/vector/GDI/FS finite closure"','operand_cursor==root->operand_count&&!format_live&&format_dispatch_cursor==(root->root==0x40f000?3u:0u),"Complete actual root CALL/virtual/vector/GDI/FS/formatter finite closure"')
change('dump(p+"/APIs.bin",APIs.data(),APIs.size()*sizeof(ApiRecord));','dump(p+"/APIs.bin",APIs.data(),APIs.size()*sizeof(ApiRecord));dump(p+"/formats.bin",formats.data(),formats.size()*sizeof(FormatRecord));dump(p+"/format-dispatches.bin",format_dispatches.data(),format_dispatches.size()*sizeof(format_dispatches[0]));')
change('void Component::entry_479590(Runtime&r){entry(r,0x479590);}','void Component::entry_479590(Runtime&r){entry(r,0x479590);}void Component::entry_40f000(Runtime&r){entry(r,0x40f000);}')
q=P/'component_v1.cpp';assert not q.exists();q.write_text(s)
h=R/'reports/m4-widget-native/preparation-r6/component.hpp';raw=h.read_text();header=raw.replace('std::array<Import, 6>','std::array<Import, 7>').replace('// Six explicit callbacks;','// Seven explicit callbacks;').replace('static void entry_479590(Runtime &);','static void entry_479590(Runtime &);\n  static void entry_40f000(Runtime &);');q=P/'component_v1.hpp';assert not q.exists();q.write_text(header)
q=P/'component-source-relations.json';assert not q.exists();q.write_text(json.dumps(dict(prior_cpp=str(prior),prior_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),changes=relations,header_changes=[['std::array<Import, 6>','std::array<Import, 7>'],['Six explicit callbacks','Seven explicit callbacks'],['entry_479590 declaration','add entry_40f000 declaration']]),indent=2)+'\n')
print('Prepared exact source diffs',len(relations))
