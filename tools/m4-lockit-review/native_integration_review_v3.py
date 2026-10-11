"""Bounded current source review plus exact two-PC early-FS attribution correction."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
p=HERE/'native_integration_review.py';s=p.read_text(encoding='utf-8')
s=s.replace("reports/m4-lockit-native/preparation-r3","reports/m4-lockit-native/preparation-r4").replace("reports/m4-joint-startup124/preparation-r3","reports/m4-joint-startup124/preparation-r4")
old="    for p,h in n['files'].items():pin(p,h)"
new="    for p,h in n['files'].items():\n        if Path(p).resolve().parent==np.resolve():pin(p,h)\n    pin(HERE/'native_integration_review.py')"
assert s.count(old)==1;s=s.replace(old,new)
anchor="    counts['reviewed_resource_admission_invariants']=len(clauses)"
extra='''    old_fs=text(ROOT/'reports/m4-lockit-native/preparation-r3/fs_operations.inc');new_fs=text(np/'fs_operations.inc')
    old_delta=""" const auto&call=calls_.back();const auto frame=state.gpr.rsp.dword+8;
 if(frame!=call.frame||runtime.memory().load<unsigned>({frame})!=call.return_pc||
    runtime.memory().load<unsigned>({frame-8})!=spec->handler||runtime.memory().load<unsigned>({frame-4})!=UINT32_MAX)"""
    new_delta=""" const auto&call=calls_.back();
 // These two exact prologs read FS before committing their two literal pushes.
 // Their complete handler/scope/predecessor bytes are checked at installation.
 const bool early=(spec->read==0x4125a0U||spec->read==0x500cd0U)&&spec->entry==spec->read;
 const auto frame=state.gpr.rsp.dword+(early?0:8);
 if(frame!=call.frame||runtime.memory().load<unsigned>({frame})!=call.return_pc||
    (!early&&(runtime.memory().load<unsigned>({frame-8})!=spec->handler||runtime.memory().load<unsigned>({frame-4})!=UINT32_MAX)))"""
    need(old_fs.count(old_delta)==1 and old_fs.replace(old_delta,new_delta)==new_fs,'Only exact reviewed two-PC early-FS code delta')
    need('fs_expected_,frame-12,spec->handler,UINT32_MAX' in new_fs,'Same complete future record geometry')
    diagnostic=read(ROOT/'reports/m4-lockit-review/fs-variant-r2/report.json');need(diagnostic['passed'] and len(diagnostic['observations'])==2,'Independent original physical and candidate observed diagnosis')
    counts['physical_early_FS_variant_contracts']=2
'''
assert s.count(anchor)==1;s=s.replace(anchor,anchor+'\n'+extra)
exec(compile(s,str(p),'exec'),globals())
