"""Add the missing observed FSTP C1 status capture to one exact host candidate.

All arithmetic, exception accumulation, register/memory operations and return
remain the static lift. The new typed bridge receives the same State pointer.
"""
from pathlib import Path
import hashlib
import json
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(ok,why):
    if not ok:raise ValueError(why)
def main():
    source,output,report=map(lambda p:Path(p).resolve(),sys.argv[1:4])
    require(sha(source)=='564f22610d368ce8ae6b40283cc93668f7394ac30674d9051e784a9ad1a723b5','Exact reviewed strict host candidate required')
    require(not output.exists() and not report.exists() and output.is_relative_to(ROOT/'reports/m4-fp-store-repair'),'Fresh private repaired candidate required')
    text=source.read_text();calls=list(re.finditer(r'^(  %\d+ = call i32 )@__remill_fpu_exception_test\(i32 noundef 127\)( #\d+)$',text,re.M))
    require(len(calls)==2,'Exact multiplication/store exception tests required')
    call=calls[1];require(text[max(0,call.start()-330):call.start()].count('@llvm.experimental.constrained.fptrunc.f32.f80')==1,'Exact strict FSTP predecessor required')
    replaced=call.group(1)+'@mw34_fp_store_exception_test(ptr %state, i32 127)'+call.group(2)
    transformed=text[:call.start()]+replaced+text[call.end():]+'\ndeclare i32 @mw34_fp_store_exception_test(ptr, i32)\n'
    require(transformed.count('@mw34_fp_store_exception_test(')==2,'Exact new store bridge definition/use count differs')
    output.write_text(transformed);report.write_text(json.dumps({'candidate_only':True,'original_host_sha':sha(source),'repaired_host_sha':sha(output),
        'repair_source_sha':sha(__file__),'exact_typed_boundary':'i32 (State*, i32 mask)',
        'numerical_changes':0,'replacement_calls':1,'status_capture':'Actual hardware C1 after strict dynamic FSTP; not expected values'},indent=2)+'\n')
    print(json.dumps({'candidate':str(output),'numeric_changes':0,'replaced_store_tests':1}))
if __name__=='__main__':main()
