"""Repair only measured DE accumulation and actual hardware store C1 capture."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    source,out,report=map(lambda p:Path(p).resolve(),sys.argv[1:4])
    assert not out.exists() and not report.exists() and out.is_relative_to(ROOT/'reports/m4-fp-simple-batch')
    text=source.read_text();entry='4b5af0' if '@sub_4b5af0(' in text else '4c79d0'
    expected={'4b5af0':'77258f0b4cd0fcc7344986e70a56fd56c0e7687f3483d256d8397571dc175f4e','4c79d0':'b5391c23c6b4e5b21e2cb6a9f454d0344fd4d4c2e4a9304535edd42a95f1d5b4'}
    # LLVM's first comment records the fresh input filename. No instruction,
    # type, attribute, declaration, or remaining line is normalized away.
    assert text.splitlines()[0].startswith('; ModuleID = ')
    canonical=hashlib.sha256('\n'.join(text.splitlines()[1:]).encode()).hexdigest()
    assert canonical==expected[entry],'Exact preserved strict baseline body required'
    calls=list(re.finditer(r'^(  %\d+ = call i32 )@__remill_fpu_exception_test\(i32 noundef 127\)( #\d+)$',text,re.M))
    assert len(calls)==(2 if entry=='4b5af0' else 1)
    last=calls[-1];assert text[max(0,last.start()-330):last.start()].count('@llvm.experimental.constrained.fptrunc.f32.f80')==1
    replace=last.group(1)+'@mw34_fp_store_exception_test(ptr %state, i32 127)'+last.group(2)
    text=text[:last.start()]+replace+text[last.end():]+'\ndeclare i32 @mw34_fp_store_exception_test(ptr, i32)\n'
    aliases=set(re.findall(r'(%\d+) = getelementptr inbounds nuw i8, ptr %state, i32 2753',text))
    values=set(re.findall(r'(%\d+) = phi i8',text));changed=[]
    for value,pointer in re.findall(r'^  store i8 (%\d+), ptr (%\d+), align 1$',text,re.M):
        if pointer not in aliases or value not in values:continue
        n=len(changed);old=f'  store i8 {value}, ptr {pointer}, align 1\n'
        new=f'  %m4_simple_prior_de_{n} = load i8, ptr {pointer}, align 1\n  %m4_simple_sticky_de_{n} = or i8 {value}, %m4_simple_prior_de_{n}\n  store i8 %m4_simple_sticky_de_{n}, ptr {pointer}, align 1\n'
        assert text.count(old)==1;text=text.replace(old,new);changed.append({'phi':value,'State_DE_pointer':pointer})
    assert len(changed)==(2 if entry=='4b5af0' else 1)
    out.write_text(text);report.write_text(json.dumps({'candidate_only':True,'entry':entry,'input_sha256':sha(source),'output_sha256':sha(out),'repair_source_sha256':sha(__file__),
        'numeric_changes':0,'canonical_baseline_sha256':canonical,'canonical_scope':'Only first ModuleID comment omitted; all other source lines bound','typed_store_boundary':'i32(State*,i32 mask127)','store_status_source':'Actual fnstsw after strict FSTP; no expected-value synthesis',
        'DE_accumulation_replacements':changed,'baseline_failure_report':str(ROOT/'reports/m4-fp-simple-batch/baseline-r1/directed-report.json')},indent=2)+'\n')
    print(json.dumps({'entry':entry,'DE_repairs':len(changed),'C1_actual_typed_bridges':1,'numeric_changes':0}))
if __name__=='__main__':main()
