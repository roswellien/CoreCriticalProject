"""Repair only measured sticky flags and typed actual FSTP C1 capture."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    source,out,report=map(lambda p:Path(p).resolve(),sys.argv[1:4]);assert not out.exists() and not report.exists() and out.is_relative_to(ROOT/'reports/m4-fp-sqrt')
    text=source.read_text();assert text.splitlines()[0].startswith('; ModuleID = ')
    canonical=hashlib.sha256('\n'.join(text.splitlines()[1:]).encode()).hexdigest();assert canonical=='5d50d6fd6be412b08142ab88b028f844237da2afe02bb030eda60fa61a1c9ae1','Exact preserved strict baseline required'
    calls=list(re.finditer(r'^(  %\d+ = call i32 )@__remill_fpu_exception_test\(i32 noundef 127\)( #\d+)$',text,re.M));assert len(calls)==6
    for call in reversed(calls[-3:]):
        assert '@llvm.experimental.constrained.fptrunc.f32.f80' in text[max(0,call.start()-340):call.start()]
        text=text[:call.start()]+call.group(1)+'@mw34_fp_store_exception_test(ptr %state, i32 127)'+call.group(2)+text[call.end():]
    text+='\ndeclare i32 @mw34_fp_store_exception_test(ptr, i32)\n'
    aliases={off:set(re.findall(r'(%\d+) = getelementptr inbounds nuw i8, ptr %state, i32 '+str(off),text)) for off in (2753,2755,2745)}
    phis=set(re.findall(r'(%\d+) = phi i8',text));de=[];clears=[]
    for value,pointer in re.findall(r'^  store i8 (0|%\d+), ptr (%\d+), align 1$',text,re.M):
        if value=='0' and any(pointer in a for a in aliases.values()):
            old=f'  store i8 0, ptr {pointer}, align 1\n';assert text.count(old)==1;text=text.replace(old,'');clears.append(pointer)
        elif pointer in aliases[2753] and value in phis:
            old=f'  store i8 {value}, ptr {pointer}, align 1\n';n=len(de)
            new=f'  %mw_sqrt_prior_de_{n} = load i8, ptr {pointer}, align 1\n  %mw_sqrt_sticky_de_{n} = or i8 {value}, %mw_sqrt_prior_de_{n}\n  store i8 %mw_sqrt_sticky_de_{n}, ptr {pointer}, align 1\n'
            assert text.count(old)==1;text=text.replace(old,new);de.append({'phi':value,'pointer':pointer})
    assert len(clears)==7 and len(de)==6
    old='  store i8 %159, ptr %144, align 1\n';assert text.count(old)==1 and '%144' in aliases[2745]
    text=text.replace(old,'  %mw_sqrt_prior_pe = load i8, ptr %144, align 1\n  %mw_sqrt_sticky_pe = or i8 %159, %mw_sqrt_prior_pe\n  store i8 %mw_sqrt_sticky_pe, ptr %144, align 1\n')
    # Negative quiet NaNs are not negative real operands. Gate only the lift's
    # sign-derived invalid bit; preserve signaling and prior invalid flags.
    old='  %101 = or i8 %100, %99\n';assert text.count(old)==1
    text=text.replace(old,'  %mw_sqrt_frac = and i64 %87, 9223372036854775807\n  %mw_sqrt_frac_nonzero = icmp ne i64 %mw_sqrt_frac, 0\n  %mw_sqrt_nan = and i1 %89, %mw_sqrt_frac_nonzero\n  %mw_sqrt_real = xor i1 %mw_sqrt_nan, true\n  %mw_sqrt_real_byte = zext i1 %mw_sqrt_real to i8\n  %mw_sqrt_real_negative = and i8 %99, %mw_sqrt_real_byte\n  %101 = or i8 %100, %mw_sqrt_real_negative\n')
    # An m64 subnormal or SNaN is consumed by FMUL even though its strict
    # conversion to extended precision normalizes/quietens it before FMUL.
    # Model those two architectural input classifications before conversion.
    memory_status=[]
    for n,(value,pc) in enumerate((('%205',0x4adb6a),('%279',0x4adb72))):
        matches=list(re.finditer(r'^  '+re.escape(value)+r' = call noundef double @__remill_read_memory_f64\([^\n]+\n',text,re.M));assert len(matches)==1
        i=matches[0].end();prefix=f'%mw_sqrt_m64_{n}_'
        block=(f'  {prefix}bits = bitcast double {value} to i64\n'
          f'  {prefix}exponent = and i64 {prefix}bits, 9218868437227405312\n'
          f'  {prefix}fraction = and i64 {prefix}bits, 4503599627370495\n'
          f'  {prefix}fraction_nonzero = icmp ne i64 {prefix}fraction, 0\n'
          f'  {prefix}exponent_zero = icmp eq i64 {prefix}exponent, 0\n'
          f'  {prefix}denormal = and i1 {prefix}exponent_zero, {prefix}fraction_nonzero\n'
          f'  {prefix}de = zext i1 {prefix}denormal to i8\n'
          f'  {prefix}deptr = getelementptr inbounds i8, ptr %state, i32 2753\n'
          f'  {prefix}oldde = load i8, ptr {prefix}deptr, align 1\n'
          f'  {prefix}stickyde = or i8 {prefix}de, {prefix}oldde\n'
          f'  store i8 {prefix}stickyde, ptr {prefix}deptr, align 1\n'
          f'  {prefix}exponent_all = icmp eq i64 {prefix}exponent, 9218868437227405312\n'
          f'  {prefix}quiet = and i64 {prefix}bits, 2251799813685248\n'
          f'  {prefix}quiet_zero = icmp eq i64 {prefix}quiet, 0\n'
          f'  {prefix}nan = and i1 {prefix}exponent_all, {prefix}fraction_nonzero\n'
          f'  {prefix}snan = and i1 {prefix}nan, {prefix}quiet_zero\n'
          f'  {prefix}ie = zext i1 {prefix}snan to i8\n'
          f'  {prefix}ieptr = getelementptr inbounds i8, ptr %state, i32 2755\n'
          f'  {prefix}oldie = load i8, ptr {prefix}ieptr, align 1\n'
          f'  {prefix}stickyie = or i8 {prefix}ie, {prefix}oldie\n'
          f'  store i8 {prefix}stickyie, ptr {prefix}ieptr, align 1\n')
        text=text[:i]+block+text[i:];memory_status.append({'memory_value':value,'guest_PC':pc,'classification':'IEEE754 m64 exponent/fraction/quiet bits; sticky DE and signaling-NaN IE only'})
    out.write_text(text);report.write_text(json.dumps({'candidate_only':True,'entry':'4adb50','input_sha256':sha(source),'output_sha256':sha(out),'repair_source_sha256':sha(__file__),'canonical_baseline_sha256':canonical,'canonical_scope':'Only first ModuleID filename comment omitted','numeric_changes':0,'guest_event_changes':0,
      'typed_actual_store_status_bridges':3,'DE_accumulation_replacements':de,'removed_sticky_flag_clears':clears,'preserve_tested_FSQRTPe':True,'negative_qNaN_sign_invalid_gated':True,'binary64_FMUL_memory_status':memory_status,'baseline_failure_report':str(ROOT/'reports/m4-fp-sqrt/baseline-r4/directed-report.json'),'remaining_measured_failure_report':str(ROOT/'reports/m4-fp-sqrt/repaired-r1/remaining-diagnosis.json')},indent=2)+'\n')
    print(json.dumps({'typed_store_C1':3,'sticky_DE':len(de),'removed_exception_clears':len(clears),'preserve_tested_PE':1,'numeric_changes':0}))
if __name__=='__main__':main()
