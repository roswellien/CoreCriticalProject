"""Measured 4C78F0 status repair, numerical operations unchanged."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    source,out,report=map(lambda x:Path(x).resolve(),sys.argv[1:4]);assert not out.exists() and not report.exists() and out.is_relative_to(ROOT/'reports/m4-fp-trigonometric')
    text=source.read_text();assert text.splitlines()[0].startswith('; ModuleID = ')
    canonical=hashlib.sha256('\n'.join(text.splitlines()[1:]).encode()).hexdigest();assert canonical=='bfec3e217d24d19cdc778079553bbc38ef7b540955428153843b6936fdc8e489'
    for op in ('cos','sin'):
        old=f'  call void @mw34_actual_f{op}_raw80(ptr %mw.{op}.input, ptr %mw.{op}.output)';assert text.count(old)==1
        text=text.replace(old,f'  call void @mw34_actual_f{op}_status_raw80(ptr %state, ptr %mw.{op}.input, ptr %mw.{op}.output)')
        text=text.replace(f'declare void @mw34_actual_f{op}_raw80(ptr, ptr)',f'declare void @mw34_actual_f{op}_status_raw80(ptr, ptr, ptr)')
    calls=list(re.finditer(r'^(  %\d+ = call i32 )@__remill_fpu_exception_test\(i32 noundef 127\)( #\d+)$',text,re.M));assert len(calls)==6
    for call in reversed(calls[-3:]):
        assert '@llvm.experimental.constrained.fptrunc.f32.f80' in text[max(0,call.start()-340):call.start()]
        text=text[:call.start()]+call.group(1)+'@mw34_fp_store_exception_test(ptr %state, i32 127)'+call.group(2)+text[call.end():]
    text+='\ndeclare i32 @mw34_fp_store_exception_test(ptr, i32)\n'
    aliases={off:set(re.findall(r'(%\d+) = getelementptr inbounds nuw i8, ptr %state, i32 '+str(off),text)) for off in (2753,2755)};phis=set(re.findall(r'(%\d+) = phi i8',text));de=[];clears=[]
    for value,pointer in re.findall(r'^  store i8 (0|%\d+), ptr (%\d+), align 1$',text,re.M):
        if value=='0' and any(pointer in a for a in aliases.values()):
            old=f'  store i8 0, ptr {pointer}, align 1\n';assert text.count(old)==1;text=text.replace(old,'');clears.append(pointer)
        elif pointer in aliases[2753] and value in phis:
            old=f'  store i8 {value}, ptr {pointer}, align 1\n';n=len(de);new=f'  %mw_sc_prior_de_{n} = load i8, ptr {pointer}, align 1\n  %mw_sc_sticky_de_{n} = or i8 {value}, %mw_sc_prior_de_{n}\n  store i8 %mw_sc_sticky_de_{n}, ptr {pointer}, align 1\n'
            assert text.count(old)==1;text=text.replace(old,new);de.append({'phi':value,'pointer':pointer})
    assert len(clears)==2 and len(de)==6
    old='  store i8 %419, ptr %404, align 1\n';assert text.count(old)==1
    text=text.replace(old,'  %mw_sc_prior_pe = load i8, ptr %404, align 1\n  %mw_sc_sticky_pe = or i8 %419, %mw_sc_prior_pe\n  store i8 %mw_sc_sticky_pe, ptr %404, align 1\n')
    out.write_text(text);report.write_text(json.dumps({'candidate_only':True,'entry':'4c78f0','canonical_baseline_sha256':canonical,'input_sha256':sha(source),'output_sha256':sha(out),'repair_source_sha256':sha(__file__),'numeric_changes':0,'guest_event_changes':0,'typed_actual_trig_C2_bridges':2,'typed_actual_store_C1_bridges':3,'DE_accumulation_replacements':de,'removed_sticky_exception_clears':clears,'retain_tested_FSIN_PE':True,'baseline_failure_report':str(ROOT/'reports/m4-fp-trigonometric/sincos-baseline-r1/directed-report.json')},indent=2)+'\n')
    print(json.dumps({'typed_trig_C2':2,'typed_store_C1':3,'sticky_DE':6,'removed_exception_clears':2,'retain_tested_PE':1,'numeric_changes':0}))
if __name__=='__main__':main()
