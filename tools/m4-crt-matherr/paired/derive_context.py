"""Mechanical NEW host fault-transport derivative; frozen root source untouched."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3]
source=ROOT/'tools/m4-crt-matherr/context.hpp'
target=ROOT/'tools/m4-crt-matherr/paired/paired_context.hpp'
out=ROOT/'reports/m4-crt-matherr/paired-context-derivation-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(source)=='769450aa4b996ebd205b89195c48094e3ecc24f99d1934e19cebf6b1abcb4feb'
assert not target.exists() and not out.exists()
text=source.read_text();changes=[]
def exact(before,after,count=1):
 global text
 assert text.count(before)==count,(before,text.count(before))
 text=text.replace(before,after);changes.append({'before':before,'after':after,'occurrences':count})
exact('#include <csetjmp>\n','')
exact('m4_crt_matherr','m4_crt_matherr_paired_native',4)
exact('struct Context {','// Tiny C++ exception crosses only non-noexcept bridges and unwind-capable IR.\nstruct BridgeAbort {};\nstruct Context {')
exact('    std::jmp_buf escape;','    // Authored unit fault observer only; null in every paired replay.\n    void (*test_after_event)(Context &, unsigned){};')
exact('        if(active && thread==std::this_thread::get_id()) std::longjmp(escape,1);\n        throw std::runtime_error(reason);','        throw BridgeAbort{};')
exact('        events[step++]={address,value,4,0};return value;','        events[step++]={address,value,4,0};\n        if(test_after_event)test_after_event(*this,step);\n        return value;')
exact('        events[step++]={address,value,4,1};','        events[step++]={address,value,4,1};\n        if(test_after_event)test_after_event(*this,step);')
exact('        if(setjmp(escape)==0)token=sub_7800b38f(&state,entry,this);','        try { token=sub_7800b38f(&state,entry,this); }\n        catch(const BridgeAbort &) { /* First POD error was retained by deny. */ }\n        catch(...) { active=false; throw; }')
assert 'setjmp' not in text and 'longjmp' not in text and 'noexcept' not in text.replace('non-noexcept','')
target.write_text(text);out.mkdir(parents=True)
(out/'derive-source.py').write_bytes(Path(__file__).read_bytes());(out/'root-context.hpp').write_bytes(source.read_bytes());(out/'paired-context.hpp').write_bytes(target.read_bytes())
report={'passed':True,'scope':'New host C++ exception transport and unit-only event observer derivative; guest IR unchanged, no execution acceptance','frozen_root_source':str(source),'frozen_root_sha256':sha(source),'new_source':str(target),'new_sha256':sha(target),'mechanical_changes':changes,'test_observer':'Null in all positive corpus/paired replay rows; fault controls alone can mutate owned maps/state after counted source accesses. Guest callback DWORD is never invoked.'}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins={str(p):sha(p) for p in [source,target,Path(__file__)]};pins.update({str(p.resolve()):sha(p) for p in out.iterdir() if p.is_file()});(out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n')
print(json.dumps({'passed':True,'new_context_sha256':sha(target),'report_sha256':sha(out/'report.json')}))
