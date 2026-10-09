"""Measured binary FPATAN repair with original operands; no extra division."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    source,out,report=map(lambda p:Path(p).resolve(),sys.argv[1:4]);assert not out.exists() and not report.exists() and out.is_relative_to(ROOT/'reports/m4-fp-trigonometric')
    text=source.read_text();assert text.splitlines()[0].startswith('; ModuleID = ')
    canonical=hashlib.sha256('\n'.join(text.splitlines()[1:]).encode()).hexdigest();assert canonical=='a47832f2739cb5ef2db9cc9d9ad5e124846bd7a530453f17b5fddba91216ab34'
    old='  %168 = call x86_fp80 @llvm.experimental.constrained.fdiv.f80(x86_fp80 %147, x86_fp80 %145, metadata !"round.dynamic", metadata !"fpexcept.strict")';assert text.count(old)==1
    text=text.replace(old,'  %mw.fpatan.y = alloca x86_fp80, align 16\n  %mw.fpatan.x = alloca x86_fp80, align 16\n  %mw.fpatan.output = alloca x86_fp80, align 16\n  store x86_fp80 %147, ptr %mw.fpatan.y, align 16\n  store x86_fp80 %145, ptr %mw.fpatan.x, align 16\n  call void @mw34_actual_fpatan_raw80(ptr %state, ptr %mw.fpatan.y, ptr %mw.fpatan.x, ptr %mw.fpatan.output)\n  %168 = load x86_fp80, ptr %mw.fpatan.output, align 16')
    old='  %mw.atan.input = alloca x86_fp80, align 16\n  %mw.atan.output = alloca x86_fp80, align 16\n  store x86_fp80 %168, ptr %mw.atan.input, align 16\n  call void @mw34_actual_fatan_raw80(ptr %mw.atan.input, ptr %mw.atan.output)\n  %240 = load x86_fp80, ptr %mw.atan.output, align 16';assert text.count(old)==1
    text=text.replace(old,'  %240 = select i1 true, x86_fp80 %168, x86_fp80 %168')
    text=text.replace('declare void @mw34_actual_fatan_raw80(ptr, ptr)','declare void @mw34_actual_fpatan_raw80(ptr, ptr, ptr, ptr)')
    old='  call void @mw34_actual_fcos_raw80(ptr %mw.cos.input, ptr %mw.cos.output)';assert text.count(old)==1;text=text.replace(old,'  call void @mw34_actual_fcos_status_raw80(ptr %state, ptr %mw.cos.input, ptr %mw.cos.output)')
    text=text.replace('declare void @mw34_actual_fcos_raw80(ptr, ptr)','declare void @mw34_actual_fcos_status_raw80(ptr, ptr, ptr)')
    calls=list(re.finditer(r'^(  %\d+ = call i32 )@__remill_fpu_exception_test\(i32 noundef 127\)( #\d+)$',text,re.M));assert len(calls)==5
    for call in reversed([calls[2],calls[4]]):
        assert '@llvm.experimental.constrained.fptrunc.f32.f80' in text[max(0,call.start()-340):call.start()]
        text=text[:call.start()]+call.group(1)+'@mw34_fp_store_exception_test(ptr %state, i32 127)'+call.group(2)+text[call.end():]
    text+='\ndeclare i32 @mw34_fp_store_exception_test(ptr, i32)\n'
    aliases=set(re.findall(r'(%\d+) = getelementptr inbounds nuw i8, ptr %state, i32 2753',text));phis=set(re.findall(r'(%\d+) = phi i8',text));de=[]
    for value,pointer in re.findall(r'^  store i8 (%\d+), ptr (%\d+), align 1$',text,re.M):
        if pointer not in aliases or (value not in phis and value!='%166'):continue
        old=f'  store i8 {value}, ptr {pointer}, align 1\n';n=len(de);new=f'  %mw_atan_prior_de_{n} = load i8, ptr {pointer}, align 1\n  %mw_atan_sticky_de_{n} = or i8 {value}, %mw_atan_prior_de_{n}\n  store i8 %mw_atan_sticky_de_{n}, ptr {pointer}, align 1\n'
        assert text.count(old)==1;text=text.replace(old,new);de.append({'value':value,'pointer':pointer})
    assert len(de)==6
    old='  store i8 %239, ptr %194, align 1\n';assert text.count(old)==1
    # The actual FPATAN exception test already accumulated PE. The stock
    # quotient-payload heuristic invents PE for quiet NaNs, so remove its
    # overwrite entirely rather than interpreting NaN payload as precision.
    text=text.replace(old,'')
    out.write_text(text);report.write_text(json.dumps({'candidate_only':True,'entry':'4b7020','canonical_baseline_sha256':canonical,'input_sha256':sha(source),'output_sha256':sha(out),'repair_source_sha256':sha(__file__),'numerical_repair':'First divide plus unary atan replaced by actual binary FPATAN on exact ST1 Y/ST0 X; later actual FDIV retained','removed_extra_division_sites':1,'remaining_actual_FDIV_sites':1,'typed_actual_store_C1_bridges':2,'typed_actual_FCOS_C2_bridges':1,'DE_accumulation_replacements':de,'retain_tested_FPATAN_PE':True,'guest_memory_event_changes':0,'baseline_failure_report':str(ROOT/'reports/m4-fp-trigonometric/atan-baseline-r1/directed-report.json')},indent=2)+'\n')
    print(json.dumps({'binary_FPATAN':1,'removed_extra_FDIV':1,'remaining_actual_FDIV':1,'typed_store_C1':2,'sticky_DE':6}))
if __name__=='__main__':main()
