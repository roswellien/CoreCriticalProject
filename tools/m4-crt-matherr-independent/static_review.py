"""Independent matherr whole ABI/source audit; frozen root layout model only."""
import hashlib, importlib.util, json, re, subprocess, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-matherr';PINS={}

def need(ok,why):
    if not ok:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,want=None):
    p=Path(p).resolve();got=sha(p);need(want is None or got==want,'Static identity '+str(p));need(str(p) not in PINS or PINS[str(p)]==got,'Conflicting static identity');PINS[str(p)]=got;return p
def read(p):return json.loads(pin(p).read_text(encoding='utf-8-sig'))
def body(text,name):
    found=re.findall(r'^define [^\n]*@'+re.escape(name)+r'\([^\n]*\) [^\n]*\{\n(.*?)^}',text,re.M|re.S)
    need(len(found)==1,'Unique definition '+name);return found[0]
def audit(guest,host,layouts,m,upstream):
    need(body(guest,'sub_7800b38f')==body(host,'sub_7800b38f'),'Entire actual guest instruction/flag/access body unchanged')
    gt=dict(re.findall(r'^(%[\w.]+) = type (.+)$',guest,re.M));ht,hl=m.layout_model(host);_,gl=m.layout_model(guest)
    need(len(gt)==len(ht)==34 and gt==ht,'Every exact guest/host State type definition')
    need(gl==hl,'Every whole guest/host ABI size/alignment/offset')
    for name in ht:
        size,align,offsets=hl[name];need(layouts[name[1:]]==dict(size=size,alignment=align,offsets=list(offsets)),'Own recursive layout against recorded layout '+name)
    need(hl['%struct.State'][:2]==(3504,8),'CompleteState3504align8')
    defs=set(re.findall(r'^define [^\n]*@([^ (]+)',host,re.M))
    need(defs=={'sub_7800b38f','__remill_flag_computation_zero','__remill_flag_computation_sign'},'Only actual leaf plus two upstream annotation identities')
    for name in ('__remill_flag_computation_zero','__remill_flag_computation_sign'):
        need(re.fullmatch(r'identity:\n\s+ret i1 %0\n',body(host,name)) is not None,'Exact annotation identity '+name)
        need(re.search(r'bool '+name+r'\(bool result, \.\.\.\)\s*\{\s*return result;\s*}',upstream),'Exact upstream annotation definition '+name)
    need(not re.search(r'\b(?:undef|poison|inttoptr|ptrtoint|nounwind|willreturn|float|double|x86_fp80|volatile|atomic)\b',host),'No invented pointer/numerical/trap/EH attributes')
    calls=re.findall(r'\bcall [^\n]*@([^ (]+)',body(host,'sub_7800b38f'))
    need({name:calls.count(name) for name in calls}=={'__remill_read_memory_32':3,'__remill_write_memory_32':2,'__remill_flag_computation_zero':1,'__remill_flag_computation_sign':1,'__remill_function_return':1},'Exact complete typed calls/access extent')
    need(re.search(r'%29 = getelementptr inbounds nuw i8, ptr %state, i32 2069\n\s+store i8 0, ptr %29',host),'Actual fixed native AND-AF0 policy')
    return len(ht)

def context_audit(source,target):
    changes=[('#include <csetjmp>\n','',1),('m4_crt_matherr','m4_crt_matherr_paired_native',4),
      ('struct Context {','// Tiny C++ exception crosses only non-noexcept bridges and unwind-capable IR.\nstruct BridgeAbort {};\nstruct Context {',1),
      ('    std::jmp_buf escape;','    // Authored unit fault observer only; null in every paired replay.\n    void (*test_after_event)(Context &, unsigned){};',1),
      ('        if(active && thread==std::this_thread::get_id()) std::longjmp(escape,1);\n        throw std::runtime_error(reason);','        throw BridgeAbort{};',1),
      ('        events[step++]={address,value,4,0};return value;','        events[step++]={address,value,4,0};\n        if(test_after_event)test_after_event(*this,step);\n        return value;',1),
      ('        events[step++]={address,value,4,1};','        events[step++]={address,value,4,1};\n        if(test_after_event)test_after_event(*this,step);',1),
      ('        if(setjmp(escape)==0)token=sub_7800b38f(&state,entry,this);','        try { token=sub_7800b38f(&state,entry,this); }\n        catch(const BridgeAbort &) { /* First POD error was retained by deny. */ }\n        catch(...) { active=false; throw; }',1)]
    for old,new,count in changes:need(source.count(old)==count,'Exact independently allowed Context derivative');source=source.replace(old,new)
    need(source==target,'Entire Context only explicit namespace/fault transport/unit observer changes')
    need('noexcept' not in target.replace('non-noexcept','') and 'longjmp' not in target and 'setjmp' not in target,'Unwind-capable non-noexcept bridges')
    return len(changes)

def main(out):
    need(out.is_relative_to(BASE) and not out.exists(),'Fresh independent static report')
    out.mkdir(parents=True);(out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
    try:
        path=pin(ROOT/'tools/m4-fp-numeric-max-independent/native_review.py','6837acea5209e45ac6f2821b37f4d941bdd522c9ddbe320c9184378d609a5643');spec=importlib.util.spec_from_file_location('own_root_ABI_model',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        guest=pin(BASE/'preparation-r1/guest.ll','acc084182aae901a07401f2799dc38084c93f70c4ddd5693eaa4086551ef4d1f').read_text();host=pin(BASE/'abi-r1/host.ll','6afb5776644c82629221ad44799e2ea7c0ce821258fc0413eb04e2819ca60a4c').read_text()
        layouts=read(BASE/'abi-r1/report.json')['layouts'];up=pin(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp').read_text()
        count=audit(guest,host,layouts,m,up)
        original=pin(ROOT/'tools/m4-crt-matherr/context.hpp','769450aa4b996ebd205b89195c48094e3ecc24f99d1934e19cebf6b1abcb4feb').read_text();target=pin(ROOT/'tools/m4-crt-matherr/paired/paired_context.hpp','5eab85d9e012571fb7347f4f846c6f8d5b9d82c95601d0e97ba784a5d52dbb01').read_text();changes=context_audit(original,target)
        controls=[]
        for name,text in [('State-vector-count',host.replace('[32 x %union.VectorReg]','[31 x %union.VectorReg]')),('wrong-AND-global',host.replace('2013500088','2013500089')),('native-AF-choice',host.replace('store i8 0, ptr %29','store i8 1, ptr %29')),('wrong-annotation',host.replace('ret i1 %0','ret i1 true')),('bridge-nounwind',host+'\n; nounwind\n')]:
            try:audit(guest,text,layouts,m,up)
            except ValueError as ex:controls.append(dict(case=name,rejected=True,reason=str(ex)))
            else:raise ValueError('Static audit accepted corruption '+name)
        tool=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe');readobj=pin(tool.parent/'llvm-readobj.exe');objects=[]
        for level in ('O0','O2'):
            guestobj=pin(BASE/f'paired-native-build-r7/native-{level}.obj')
            for label,p in [('guest',guestobj),('root-controls',pin(BASE/f'independent-compiled-r1/{level}/controls.obj'))]:
                command=[str(tool),'--disassemble','--reloc','--x86-asm-syntax=intel',str(p)];r=subprocess.run(command,capture_output=True,text=True);need(r.returncode==0,'Fresh actual compiled decode')
                dest=out/f'{level}-{label}-decode.txt';dest.write_text(r.stdout);pin(dest)
                uw=subprocess.run([str(readobj),'--unwind',str(p)],capture_output=True,text=True);need(uw.returncode==0,'Fresh compiled unwind inspection');destu=out/f'{level}-{label}-unwind.txt';destu.write_text(uw.stdout);pin(destu)
                if label=='guest':need('sub_7800b38f' in r.stdout and '__remill_function_return' in r.stdout and 'UnwindInfo' in uw.stdout,'Actual guest bridge/Windows unwind body')
                else:
                    blocks=uw.stdout.split('  RuntimeFunction {')[1:]
                    actual=[b for b in blocks if re.search(r'StartAddress: \?execute@Context@',b)]
                    need(len(actual)==1 and re.search(r'Handler: __CxxFrameHandler[34]',actual[0]),'Actual Context::execute Windows C++ unwind handler')
                objects.append(dict(level=level,kind=label,path=str(p),decode=str(dest),unwind=str(destu)))
        for p,h in m.PINS.items():pin(p,h)
        report=dict(passed=True,complete_State_bytes=3504,alignment=8,complete_type_layouts=count,unchanged_actual_leaf_IR=True,upstream_identity_helpers=2,exact_Context_derivative_changes=changes,independent_static_corruptions=controls,fresh_compiled_objects=objects,independent_acceptance_requires_final_physical_closure=True,full_M4_complete=False)
        rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp);pin(Path(__file__));(out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,types=count,controls=len(controls),objects=len(objects),report_sha256=sha(rp),pins_sha256=sha(out/'pins.json'))))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
