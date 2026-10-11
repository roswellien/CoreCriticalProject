"""Add private witness conservation and exact live formatter lifetime guard."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_v3.py');source=p.read_text();anchor="exec(compile(s,str(p),'exec'),globals())";assert source.count(anchor)==1
extra=r'''
s=s.replace('pin(__file__);pin(R/\'tools/m4-formatting-native/prepare.py\')','pin(__file__);pin(R/\'tools/m4-formatting-native/prepare.py\');pin(R/\'tools/m4-formatting-native/prepare_v3.py\')')
s=s.replace("'void formatting_enter();std::uint64_t formatting_read", "'void formatting_enter();std::uint64_t formatting_read") if False else s
s=s.replace('void formatting_enter();std::uint64_t formatting_read','void formatting_enter();void formatting_guard();std::uint64_t formatting_read')
needle="p.write_text(s+'\\n#include \"formatting_operations.inc\"\\n')"
assert s.count(needle)==1
s=s.replace(needle,"s=one(s,'live_allocations()>85','live_allocations()>88');s=one(s,'void Binding::batch_guard(){lockit_guard();','void Binding::batch_guard(){formatting_guard();lockit_guard();');"+needle)
needle="p=out/'session_impl.inc';"
assert s.count(needle)==1
insertion="""p=out/'locale_batch_binding.inc';s=p.read_text();s=one(s,'void Binding::stable_hook(unsigned point,bool terminal,bool cleaning){','void Binding::stable_hook(unsigned point,bool terminal,bool cleaning){const auto formatting_calls=formatting_calls_;const auto formatting_owned=formatting_owned_;const auto formatting_publications=formatting_publication_records_;const auto formatting_dispatches=formatting_dispatches_;const std::array<unsigned,8>formatting_status{unsigned(formatting_active_),formatting_completed_,formatting_base_,formatting_owner_,formatting_generation_,formatting_owned_cursor_,formatting_dispatch_cursor_,formatting_publications_};');s=one(s,'hook(point);admit_current();','hook(point);admit_current();if(formatting_calls!=formatting_calls_||formatting_owned!=formatting_owned_||formatting_publications!=formatting_publication_records_||formatting_dispatches!=formatting_dispatches_||formatting_status!=std::array<unsigned,8>{unsigned(formatting_active_),formatting_completed_,formatting_base_,formatting_owner_,formatting_generation_,formatting_owned_cursor_,formatting_dispatch_cursor_,formatting_publications_})deny("Formatter observer changed private invocation or source owner witnesses",state.gpr.rip.dword);');p.write_text(s)
    p=out/'formatting_operations.inc';s=p.read_text();s+='\\nnamespace {void Binding::formatting_guard(){if(!formatting_active_)return;const auto*r=formatting_root(registry_root_);if(!r||state.addr.es_base.dword||formatting_owned_cursor_>r->owned_count||formatting_dispatch_cursor_>4||formatting_publications_>1||formatting_completed_>=3)deny("Exact finite active formatter private lifetime",state.gpr.rip.dword);if(formatting_owner_){auto*a=allocation_for(formatting_owner_,1);if(!a||a->guest!=formatting_owner_||a->generation!=formatting_generation_||a->requested!=r->request||a->extent!=16||a->kind!=2)deny("Formatter active lifetime retains its real allocation generation",formatting_owner_);}}}\\n';p.write_text(s)
    """
s=s.replace(needle,insertion+needle)
'''
source=source.replace(anchor,extra+'\n'+anchor)
exec(compile(source,str(p),'exec'),globals())
