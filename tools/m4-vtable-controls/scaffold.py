"""Authored additive control fixture generation; immutable accepted116 stays unchanged."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main():
 prior=ROOT/'tools/m4-container-controls'
 s=(prior/'fixture_v3.inc').read_text().replace('mw34_container_controls','mw34_vtable_controls').replace('container_roots','vtable_roots')
 s=one(s,'constexpr unsigned vtable_roots[]{0x47f5b0,0x47f6d0,0x48f210,0x4ada90,0x4b12d0,0x4d84a0,0x5a7dc0};','constexpr unsigned vtable_roots[]{0x40f0e0,0x4795f0,0x47f5f0,0x4b5220};')
 a='bool unmapped{};try{(void)t.c->runtime().memory().load<unsigned char>({0x5f4ce000});}catch(const MemoryFault&e){unmapped=e.reason()==MemoryFaultReason::unmapped;}check(unmapped,"Borrowed MFC pointee page remains genuinely unmapped");t.pointee_unmapped=unsigned(unmapped);'
 s=one(s,a,'')
 begin=s.index('void append_trigger(');end=s.index('#pragma pack(push,1)',begin)
 s=s[:begin]+'''void append_trigger(capture_direct::Writer&w,const std::string&p){
 using namespace mw34_vtable_controls;
 w.append(p+"calls.bin",trigger.calls.data(),trigger.calls.size()*256);w.append(p+"stores.bin",trigger.stores.data(),trigger.stores.size()*128);
 w.append(p+"read.bin",trigger.read.data(),sizeof(trigger.read));w.append(p+"vptr.bin",trigger.vptr.data(),sizeof(trigger.vptr));w.append(p+"store.bin",trigger.store.data(),sizeof(trigger.store));w.append(p+"active.bin",&trigger.active,4);
 w.append(p+"State.bin",trigger_state.data(),trigger_state.size());w.append(p+"FX.bin",trigger_fx.data(),trigger_fx.size());w.append(p+"CPU.bin",trigger_cpu.data(),trigger_cpu.size());w.append(p+"stack.bin",trigger_stack.data(),trigger_stack.size());w.append(p+"guest-ENV.bin",trigger_env.data(),trigger_env.size());
 w.append(p+"TIB.bin",trigger_tib.data(),sizeof(trigger_tib));w.append(p+"record.bin",trigger_record.data(),sizeof(trigger_record));w.append(p+"frame.bin",trigger_frame.data(),sizeof(trigger_frame));
 w.append(p+"private-before.bin",private_before.data(),private_before.size());w.append(p+"private-after.bin",private_after.data(),private_after.size());w.append(p+"private-name.bin",private_name.data(),private_name.size());w.append(p+"actual-intervention.bin",actual_intervention.data(),sizeof(actual_intervention));const unsigned id[]{trigger_point,trigger_PC,mutation_hits};w.append(p+"identity.bin",id,sizeof(id));
}
''' +s[end:]
 s=one(s,'result&&t.completed==7&&sample.tags[10]==7&&sample.tags[11]==5&&c.registry().container_nullfree_witnesses().size()==5&&c.registry().container_borrowed_witnesses().size()==3&&c.registry().string_witnesses().size()==3','result&&t.completed==4&&sample.tags[10]==1&&!sample.tags[11]&&mw34_vtable_controls::snapshot(c.registry()).calls.size()==6&&!c.registry().string_witnesses().size()')
 s=s.replace('Actual isolated seven-root normal extent','Actual isolated four-root six-indirect-call extent').replace('container/borrowed/null-free refusal','finite vtable source refusal')
 s=one(s,'header[]{1,34,68,sizeof(Sample),7,8}','header[]{1,27,54,sizeof(Sample),4,6}')
 s=s.replace('selected<34','selected<27').replace('Container scenario ','Vtable scenario ')
 begin=s.index('mw34_vtable_controls::trigger_null={};');end=s.index('mw34_onexit_review::owned_guest_aliases.clear();',begin)
 s=s[:begin]+'''mw34_vtable_controls::trigger={};mw34_vtable_controls::trigger_frame={};mw34_vtable_controls::trigger_record={};mw34_vtable_controls::private_before.clear();mw34_vtable_controls::private_after.clear();mw34_vtable_controls::private_name.clear();mw34_vtable_controls::actual_intervention={};mw34_vtable_controls::trigger_point=mw34_vtable_controls::trigger_PC=0;'''+s[end:]
 s=one(s,'checks,34,68','checks,27,54').replace('Bounded seven-root container/borrowed/null-free research controls passed; canonical116 is separate','Bounded four-root finite-vtable research controls passed; canonical120 is separate')
 s=s.replace('Isolated exact seven-root research controls','Isolated exact four-root finite-vtable research controls')
 (HERE/'fixture.inc').write_text(s)
 s=(prior/'build_v3.py').read_text().replace('connected116','connected120').replace('m4-container-controls','m4-vtable-controls').replace('fixture_v3.inc','fixture.inc').replace('hooks_v2.hpp','hooks.hpp').replace('mw34_container_controls','mw34_vtable_controls').replace('build_v3.ps1','build.ps1').replace('mw34_joint_startup116.exe','mw34_joint_startup120.exe')
 (HERE/'build.py').write_text(s)
 s=(prior/'build_v3.ps1').read_text().replace('build_v3.py','build.py');(HERE/'build.ps1').write_text(s)
 s=(prior/'capture.py').read_text().replace('m4-container-controls','m4-vtable-controls');(HERE/'capture.py').write_text(s)
if __name__=='__main__':main()
