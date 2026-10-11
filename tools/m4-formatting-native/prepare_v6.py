"""Self-contained additive private conservation adapter over frozen recipe."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare.py');s=p.read_text()
def one(a,b):
    global s
    assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
one("else:raise ValueError(symbol)","""elif symbol=='mw34_onexit_game_read16':s+='\\nextern "C" unsigned short mw34_onexit_game_read16(void*p,unsigned a){return static_cast<unsigned short>(mw34::m4_onexit::read(p,a,2));}\\n'
        elif symbol=='mw34_onexit_game_write16':s+='\\nextern "C" void*mw34_onexit_game_write16(void*p,unsigned a,unsigned short v){return mw34::m4_onexit::write(p,a,v,2);}\\n'
        else:raise ValueError(symbol)""")
one("sorted(set(parent['source_pages'])|{0x78022000,0x78026000})","parent['source_pages']|{str(0x78022000):5,str(0x78026000):5}")
one('void formatting_enter();std::uint64_t formatting_read','void formatting_enter();void formatting_guard();std::uint64_t formatting_read')
one("p.write_text(s+'\\n#include \"formatting_operations.inc\"\\n')","s=one(s,'live_allocations()>85','live_allocations()>88');s=one(s,'void Binding::batch_guard(){lockit_guard();','void Binding::batch_guard(){formatting_guard();lockit_guard();');p.write_text(s+'\\n#include \"formatting_operations.inc\"\\n')")
block='''p=out/'locale_batch_binding.inc';s=p.read_text();s=one(s,'void Binding::stable_hook(unsigned point,bool terminal,bool cleaning){','void Binding::stable_hook(unsigned point,bool terminal,bool cleaning){const auto formatting_calls=formatting_calls_;const auto formatting_owned=formatting_owned_;const auto formatting_publications=formatting_publication_records_;const auto formatting_dispatches=formatting_dispatches_;const std::array<unsigned,8>formatting_status{unsigned(formatting_active_),formatting_completed_,formatting_base_,formatting_owner_,formatting_generation_,formatting_owned_cursor_,formatting_dispatch_cursor_,formatting_publications_};');s=one(s,'hook(point);admit_current();','hook(point);admit_current();if(formatting_calls!=formatting_calls_||formatting_owned!=formatting_owned_||formatting_publications!=formatting_publication_records_||formatting_dispatches!=formatting_dispatches_||formatting_status!=std::array<unsigned,8>{unsigned(formatting_active_),formatting_completed_,formatting_base_,formatting_owner_,formatting_generation_,formatting_owned_cursor_,formatting_dispatch_cursor_,formatting_publications_})deny("Formatter observer changed private invocation or source owner witnesses",state.gpr.rip.dword);');p.write_text(s)
    p=out/'formatting_operations.inc';s=p.read_text();s+='\\nnamespace {void Binding::formatting_guard(){if(!formatting_active_)return;const auto*r=formatting_root(registry_root_);if(!r||state.addr.es_base.dword||formatting_owned_cursor_>r->owned_count||formatting_dispatch_cursor_>4||formatting_publications_>1||formatting_completed_>=3)deny("Exact finite active formatter private lifetime",state.gpr.rip.dword);if(formatting_owner_){auto*a=allocation_for(formatting_owner_,1);if(!a||a->guest!=formatting_owner_||a->generation!=formatting_generation_||a->requested!=r->request||a->extent!=16||a->kind!=2)deny("Formatter active lifetime retains its real allocation generation",formatting_owner_);}}}\\n';p.write_text(s)
    '''
one("p=out/'session_impl.inc';",block+"p=out/'session_impl.inc';")
one('pin(__file__)',"pin(__file__);pin(R/'tools/m4-formatting-native/prepare.py')")
exec(compile(s,str(p),'exec'),globals())
