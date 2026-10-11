"""Integrate raw-decoded source operands and private same-instruction read epochs."""
from pathlib import Path
h=Path(__file__).resolve().parent;p=h/'prepare_service.py';s=p.read_text()
def change(a,b):
 global s
 if s.count(a)!=1:raise ValueError('Exact additive constructor service hunk '+a[:90])
 s=s.replace(a,b,1)
begin=s.index(' descriptors=[]\n for row in rows:');end=s.index(" impl=out/'session_impl.inc'",begin)
s=s[:begin]+''' operands=read(R/'reports/m4-constructor-native/store-operands-r1/report.json','56acaf9dffcf68355d6a68bcd28ef841e084208e9f10724a8a14d3d06ed63d33');timing=read(Path(sys.argv[2]),sys.argv[3]);need(operands['passed']and timing['passed']and timing['complete_compiled_store_IR_timing_claim']and timing['compiled_body_count']==33,'Complete compiled literal callback timing and independent raw operand contracts')
 guard=pin(operands['guard_path'],operands['guard_sha256']);shutil.copyfile(guard,out/'constructor_store_operands.hpp');(out/'constructor_store_contract.inc').write_text('#include "constructor_store_operands.hpp"\\n');descriptors=read(operands['contracts_path'],operands['contracts_sha256'])['stores'];need(len(descriptors)==418,'Exactly418 physical stores; three indirect JMPs are not stores')
''' +s[end:]
change("std::vector<std::array<std::uint64_t,12>>constructor_accesses_;","std::vector<std::array<std::uint64_t,12>>constructor_accesses_;\\n std::uint64_t constructor_access_epoch_{};unsigned constructor_active_root_{},constructor_prior_root_{};mw34::m4_constructor_store_source::PriorRead constructor_prior_read_{};")
change("R/'tools/m4-constructor-native/borrowed_constructor.inc'","R/'tools/m4-constructor-native/borrowed_constructor_v4.inc'")
change('void constructor_source_write(State&,unsigned root,unsigned pc,unsigned address,unsigned bytes,std::uint64_t value);','void constructor_source_write(State&,unsigned root,unsigned pc,unsigned address,unsigned bytes,std::uint64_t value);\\n void constructor_scope(State&,unsigned root,bool entering);')
a='void Session::constructor_source_write(State&s,unsigned root,unsigned pc,unsigned address,unsigned bytes,std::uint64_t value){impl_->constructor_source_write(s,root,pc,address,bytes,value);}'
change(a,a+'\\nvoid Session::constructor_scope(State&s,unsigned root,bool entering){impl_->constructor_scope(s,root,entering);}')
change('void constructor_scope(State&,unsigned root,bool entering);','void constructor_scope(State&,unsigned root,bool entering);\\n void abort_constructor(State&,unsigned root)noexcept;')
change('void Session::constructor_scope(State&s,unsigned root,bool entering){impl_->constructor_scope(s,root,entering);}','void Session::constructor_scope(State&s,unsigned root,bool entering){impl_->constructor_scope(s,root,entering);}\\nvoid Session::abort_constructor(State&s,unsigned root)noexcept{impl_->abort_constructor(s,root);}')
change("s=impl.read_text();","s=impl.read_text();need(s.count('failed=true;if(!binding->failed)')==1,'One private service poison seam');s=s.replace('failed=true;if(!binding->failed)','clear_constructor_scope();failed=true;if(!binding->failed)',1);")
change('std::span(i.constructor_accesses_)','std::span(constructor_accesses_)')
change('pin(__file__);report=dict(',"pin(__file__);pin(R/'tools/m4-constructor-native/prepare_service.py');pin(R/'tools/m4-constructor-native/prepare_service_v2.py');report=dict(store_operand_report_sha256=sha(R/'reports/m4-constructor-native/store-operands-r1/report.json'),store_timing_report_sha256=sys.argv[3],source_store_operand_value_guard_pending=False,private_same_instruction_read_epoch=True,balanced_active_constructor_scope=True,")
exec(compile(s,str(p),'exec'),globals())
