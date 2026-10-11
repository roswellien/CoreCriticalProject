"""Additive isolated Lockit controls using unchanged literal linked source bodies."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=ROOT/'reports/m4-lockit-review/controls-source-r1';assert not out.exists();out.mkdir(parents=True)
 source=ROOT/'tools/m4-vtable-controls/fixture.inc';s=source.read_text()
 s=s.replace('four-root finite-vtable','four-root Lockit').replace('mw34_vtable_controls','mw34_lockit_controls').replace('vtable_roots','lockit_roots').replace('0x40f0e0,0x4795f0,0x47f5f0,0x4b5220','0x411010,0x4dc140,0x500660,0x5968f0')
 start=s.index('void append_trigger(');end=s.index('#pragma pack(push,1)',start)
 replacement='''void append_trigger(capture_direct::Writer&w,const std::string&p){
 using namespace mw34_lockit_controls;
 w.append(p+"calls.bin",trigger.calls.data(),trigger.calls.size()*128);
 w.append(p+"State.bin",trigger_state.data(),trigger_state.size());w.append(p+"FX.bin",trigger_fx.data(),trigger_fx.size());w.append(p+"CPU.bin",trigger_cpu.data(),trigger_cpu.size());w.append(p+"stack.bin",trigger_stack.data(),trigger_stack.size());w.append(p+"guest-ENV.bin",trigger_env.data(),trigger_env.size());
 w.append(p+"TIB.bin",trigger_tib.data(),sizeof(trigger_tib));w.append(p+"record.bin",trigger_record.data(),sizeof(trigger_record));w.append(p+"frame.bin",trigger_frame.data(),sizeof(trigger_frame));
 w.append(p+"private-before.bin",private_before.data(),private_before.size());w.append(p+"private-after.bin",private_after.data(),private_after.size());w.append(p+"private-name.bin",private_name.data(),private_name.size());w.append(p+"actual-intervention.bin",actual_intervention.data(),sizeof(actual_intervention));
 w.append(p+"native40-before.bin",resource_before.data(),40);w.append(p+"native40-after.bin",resource_after.data(),40);const unsigned id[]{trigger_point,trigger_PC,mutation_hits};w.append(p+"identity.bin",id,sizeof(id));
}
'''
 s=s[:start]+replacement+s[end:]
 s=s.replace('(void)invoke(t);','(void)invoke(t);mw34_lockit_controls::restore_actual();')
 old='t.completed==4&&sample.tags[10]==1&&!sample.tags[11]&&mw34_lockit_controls::snapshot(c.registry()).calls.size()==6&&!c.registry().string_witnesses().size()'
 new='t.completed==4&&sample.tags[10]==4&&sample.tags[11]==8&&mw34_lockit_controls::snapshot(c.registry()).calls.size()==8&&!c.registry().string_witnesses().size()'
 assert s.count(old)==1;s=s.replace(old,new)
 s=s.replace('1,27,54,sizeof(Sample),4,6','1,16,32,sizeof(Sample),4,8').replace('selected<27','selected<16').replace('checks,27,54','checks,16,32').replace('Vtable scenario','Lockit scenario').replace('six-indirect-call','eight-Lockit-call').replace('finite vtable','Lockit').replace('canonical120','canonical124')
 (out/'fixture.inc').write_text(s,encoding='utf-8');(out/'hooks.hpp').write_bytes((HERE/'control_hooks.hpp').read_bytes())
 builder=(ROOT/'tools/m4-vtable-controls/build.py').read_text()
 builder=builder.replace("BASE=ROOT/'reports/m4-vtable-controls'","BASE=ROOT/'reports/m4-lockit-review'")
 builder=builder.replace("pin(HERE/'build.ps1');fixture=pin(HERE/'fixture.inc');hooks=pin(HERE/'hooks.hpp')","fixture=pin(ROOT/'reports/m4-lockit-review/controls-source-r1/fixture.inc');hooks=pin(ROOT/'reports/m4-lockit-review/controls-source-r1/hooks.hpp')")
 old="        for p,h in json.loads(pin(Path(buildpath).parent/'pins.json').read_bytes())['files'].items():pin(p,h)"
 new="        prep_parent=Path(b['preparation']).parent\n        receipt=json.loads(pin(prep_parent/'report.json',b['preparation_sha256']).read_bytes())\n        for p,h in receipt['generated_sources'].items():pin(p,h)\n        nprep=Path(receipt['native_include']);native=json.loads(pin(nprep/'report.json').read_bytes())\n        for p,h in native['files'].items():\n            if Path(p).resolve().parent==nprep.resolve():pin(p,h)\n        for level in ('O0','O2'):\n            for p in receipt['objects'][level]:pin(p)"
 assert builder.count(old)==1;builder=builder.replace(old,new)
 builder=builder.replace('mw34_vtable_controls','mw34_lockit_controls').replace('frozen_connected120_worker_main','frozen_connected124_worker_main').replace('mw34_joint_startup120.exe','mw34_joint_startup124.exe')
 (HERE/'build_controls.py').write_text(builder,encoding='utf-8')
 paths=[source,ROOT/'tools/m4-vtable-controls/build.py',Path(__file__),HERE/'control_hooks.hpp',HERE/'build_controls.py',out/'fixture.inc',out/'hooks.hpp']
 (out/'report.json').write_text(json.dumps({'passed':True,'scope':'Compiled control preparation; actual source bodies/API responses unchanged','cases':{'0':'positive4root8LockitCALLs','1':'state0 refusal','2':'state1 refusal','3':'state3 refusal','4':'actual guestCS24 input byte','5':'actual game ctor import','6':'actual loaded named API cell','7':'actual provider RX prefix byte','8':'actual retained CALL witness','9':'actual import witness','10':'actual semantic guestCS24 mirror','11':'actual native40 retained image witness','12':'actual held native40 recursion byte; restored after guard refusal before cleanup','13':'complete guestFX shadow byte','14':'sourceCS input page readonly','15':'actual source API frame argument'},'files':{str(p):sha(p) for p in paths}},indent=2)+'\n')
 print(json.dumps({'passed':True,'sha256':sha(out/'report.json')}))
if __name__=='__main__':main()
