"""Fresh exact static malloc/free recovery and independent affine ledgers."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
BASE=ROOT/'reports/m4-crt-allocation-recovery'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized,unique_object,verify_manifest
from paths import publish_bytes,workspace_path
import model

PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
TOOL_SHA='a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a'
ACCEPT_SHA='7a71e5de996f841010817182875a7e068eba0dee9f7e0645efaca9bfde60aeaf'
FINAL_SHA='b5387dd048813fe6a93101995e00b721d491b1fab9e8c6de69c0ac2da4f524e8'
PRIOR_SHA='c285ece7e08e2c152735629c48aae461d9f28d006895cf87e9f5157b23053684'
SPANS=(('caller-cleanup',0x78001843,0x7800184c),('malloc-wrapper',0x780012b3,0x780012c5),
       ('malloc-size',0x780012c5,0x780012e3),('malloc-worker-hot',0x780012e3,0x78001390),
       ('malloc-round-mode1',0x7800cc97,0x7800ccac),('malloc-null-cold',0x7800cc3f,0x7800cc62),
       ('free-hot',0x78001390,0x78001441),('free-mode1-cold',0x7800cc39,0x7800cc3f))


def need(v,why):
    if not v:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_bytes(),object_pairs_hook=unique_object)


def main(name):
    started=time.perf_counter_ns();out=workspace_path(BASE/name,reports=True)
    need(re.fullmatch('recovery-r[1-9][0-9]*',name) and out.parent==BASE and not out.exists(),'Fresh static receipt namespace')
    loader=ROOT/'tools/m4-crt/recover_provider.py';spec=importlib.util.spec_from_file_location('allocation_source_PE',loader)
    pe_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe_module)
    provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';pe=pe_module.PE(provider,PROVIDER_SHA)
    tool=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
    files={}
    def add(p,h=None):
        p=Path(p).absolute();value=sha(p);key=normalized(str(p))
        need(h is None or value==h,'Frozen physical identity '+str(p));need(key not in files or files[key]==value,'Unique input identity')
        files[key]=value;return p
    accepted=add(ROOT/'reports/m4-crt-heap-return-root/root-acceptance-r1/report.json',ACCEPT_SHA)
    final=add(ROOT/'reports/m4-crt-heap-return-root/final-check-r1/report.json',FINAL_SHA)
    prior=add(ROOT/'reports/m4-crt-heap-return-recovery/recovery-r1/report.json',PRIOR_SHA)
    need(read(accepted)['passed'] and read(final)['passed'] and read(prior)['passed'],'Accepted immutable previous source return gate')
    add(tool,TOOL_SHA)
    for p in (Path(__file__),Path(__file__).with_name('README.md'),Path(model.__file__),Path(sys.executable),
              loader,provider,ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):
        add(p)
    old_static=add(ROOT/'reports/m4-crt-locale-allocation-recovery/recovery-r2/report.json',
        '883ffaa436cf2376994fcbeb9807bb547fc3df54e3e220a87cf55cfa8c46388d')
    initial=verify_manifest(files);out.mkdir(parents=True);spans={};instructions={};commands=[]
    def section(a,n):
        hits=[s for s in pe.sections if s[0]<=a-pe.base and a-pe.base+n<=s[0]+s[2]]
        need(len(hits)==1,'One complete file-backed span');rva,virtual,raw,off,flags=hits[0]
        return dict(rva=rva,virtual_bytes=virtual,raw_bytes=raw,raw_offset=off,permissions=flags&0xe0000000,
                    readable=bool(flags&0x40000000),writable=bool(flags&0x80000000),executable=bool(flags&0x20000000))
    for label,start,end in SPANS:
        argv=[str(tool),'-d','--x86-asm-syntax=intel','--start-address='+hex(start),'--stop-address='+hex(end),str(provider)]
        cp=subprocess.run(argv,capture_output=True,timeout=30);need(cp.returncode==0,'Fresh original source decode')
        rows=[]
        for line in cp.stdout.decode().splitlines():
            match=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
            if not match:continue
            pc=int(match[1],16);raw=bytes.fromhex(match[2]);need(start<=pc<end and pc+len(raw)<=end and pe.read(pc-pe.base,len(raw))==raw,'Exact decoded instruction bytes')
            row=dict(pc=pc,bytes_hex=raw.hex(),width=len(raw),mnemonic=match[3],operands=match[4].split(' <')[0].replace('\t',' ').strip())
            need(pc not in instructions or instructions[pc]==row,'Exact overlapping decode');instructions[pc]=row;rows.append(row)
        raw=pe.read(start-pe.base,end-start);need(b''.join(bytes.fromhex(r['bytes_hex']) for r in rows)==raw,'Complete original function span')
        for suffix,content in (('.bin',raw),('-decode.stdout',cp.stdout),('-decode.stderr',cp.stderr)):
            p=out/(label+suffix);publish_bytes(p,content);add(p)
        spans[label]=dict(start=start,end_exclusive=end,bytes=end-start,sha256=sha(out/(label+'.bin')),section=section(start,end-start),instructions=rows)
        commands.append(dict(argv=argv,exit_code=0,original_body_executed=False))
    need(sum(v['bytes'] for v in spans.values())==469,'Eight complete exact source spans,469 bytes')
    for label in ('malloc-wrapper','malloc-worker-hot'):
        prior_label='malloc-wrapper' if label=='malloc-wrapper' else 'heap-worker-hot'
        need(spans[label]['sha256']==read(old_static)['spans'][prior_label]['sha256'],'Fresh old static body identity agrees')
    exports={name:pe.exports()[name] for name in ('malloc','free')}
    need(exports['malloc']['address']==0x780012b3 and exports['free']['address']==0x78001390,'Authentic named CRT exports')
    imports=[]
    for slot,name,hint in ((0x7802e094,'HeapAlloc',409),(0x7802e090,'HeapFree',415)):
        rows=[v for v in pe.imports() if v['iat']==slot];need(len(rows)==1 and rows[0]['library']=='KERNEL32.dll' and rows[0]['name']==name,'Exact unique named API import')
        raw=struct.unpack('<I',pe.read(slot-pe.base,4))[0];need(struct.unpack('<H',pe.read(raw,2))[0]==hint and pe.text(raw+2)==name,'Exact original import hint/name')
        imports.append(dict(**rows[0],raw_IAT=raw,hint=hint,section=section(slot,4),finite_stdcall_return_bytes=16))
    data={}
    for label,a,n in (('malloc-scope-table',0x7802e248,24),('free-scope-table',0x7802e260,24),('newmode-file-identity',0x78037150,4)):
        raw=pe.read(a-pe.base,n);p=out/(label+'.bin');publish_bytes(p,raw);add(p)
        data[label]=dict(address=a,bytes=n,sha256=sha(p),DWORDs=list(struct.unpack('<'+'I'*(n//4),raw)),section=section(a,n),file_identity_only=True)

    # Explicit authored arithmetic input solely validates the reusable source formulas.
    # It is neither an original capture nor a current/native expected machine seed.
    sample=bytearray(3504);FX=bytes(512);CPU=bytes(40);TIB=0x7ffde000;M=0x20001858;PREVIOUS=0x20001900
    regs=dict(eax=1,ecx=0x10203040,edx=0x20304050,ebx=0x31415926,esp=M,ebp=0x20001880,esi=0x42424242,edi=0x53535353)
    for k,v in regs.items():struct.pack_into('<I',sample,model.REG[k],v)
    struct.pack_into('<I',sample,model.FSBASE,TIB);sample[model.FLAGS['DF']]=1
    def memory(size,marker):
        result={0x20001000:bytearray(4096),TIB:bytearray(struct.pack('<I',PREVIOUS)),0x78035000:bytearray(4096),
                0x78037000:bytearray(4096),0x7802e000:bytearray(pe.read(0x2e000,4096))}
        struct.pack_into('<2I',result[0x78035000],0,0x48450001,1)
        struct.pack_into('<2I',result[0x20001000],0x858,marker,size)
        return result
    def summarize(value,label):
        PCs=value['PCs'];need(all(pc in instructions for pc in PCs),'Every predicted path PC belongs to fresh source spans')
        return dict(label=label,source_PCs=PCs,source_PC_count=len(PCs),executed_source_bytes=sum(instructions[pc]['width'] for pc in PCs),
            source_access_count=len(value['accesses']),source_accesses=[dict(ordinal=i+1,pc=pc,address=a,value=v,bytes=n,write=bool(w)) for i,(pc,a,v,n,w) in enumerate(value['accesses'])],
            separate_API_return_reads=value['API_return_reads'],actual_source_CALLs=value['routes'],genuine_source_RETs=value['returns'],
            undefined_AF_representatives=value['undefined'],terminal_EIP=struct.unpack_from('<I',value['state'],2472)[0],
            terminal_ESP=struct.unpack_from('<I',value['state'],model.REG['esp'])[0],terminal_EAX=struct.unpack_from('<I',value['state'],model.REG['eax'])[0],
            final_flags={k:value['state'][off] for k,off in model.FLAGS.items()},actual_API_or_original_executed=False,
            input_class='Authored static arithmetic formula check; never a native/original expected-state seed')
    controls=[]
    for size in (0,1,24,31,32,4096):
        state=bytearray(sample);struct.pack_into('<I',state,2472,0x780012b3)
        for result,label in ((0x30000000,'nonzero-hypothesis'),(0,'NULL-hypothesis')):
            predicted=model.malloc_mode1(state,FX,CPU,memory(size,0xffffffe0),size,result)
            row=summarize(predicted,'malloc-'+str(size)+'-'+label);row.update(requested=size,rounded=predicted['rounded_bytes'],guest_API_result=result)
            need(row['source_PC_count']==49+(2 if size==0 else 0)+(2 if result==0 else 0) and
                 row['source_access_count']==39+(2 if size==0 else 0)+(1 if result==0 else 0),'Independent complete success/zero/NULL path cardinality')
            controls.append(row)
    fs=bytearray(sample);struct.pack_into('<I',fs,2472,0x78001390)
    for BOOL in (1,0):
        value=model.free_mode1(fs,FX,CPU,memory(0x30000000,0xffffffd0),0x30000000,BOOL)
        row=summarize(value,'free-BOOL-'+str(BOOL));row.update(raw_BOOL=BOOL,release_success=BOOL!=0,public_CRT_return_type='void')
        need(row['source_PC_count']==33 and row['source_access_count']==25,'Complete free mode1 path')
        controls.append(row)
    cs=bytearray(sample);struct.pack_into('<I',cs,2472,0x78001843);struct.pack_into('<I',cs,model.REG['esp'],0x2000185c)
    cm=memory(1,0x78001843);value=model.caller_cleanup(cs,FX,CPU,cm);caller=summarize(value,'source-caller-cleanup')
    need(caller['source_PC_count']==3 and caller['source_access_count']==1 and caller['executed_source_bytes']==9,'Exact original caller cleanup')
    for label,value in (('caller-cleanup-ledger',caller),('formula-path-ledgers',controls)):
        p=out/(label+'.json');publish_bytes(p,(json.dumps(value,indent=2)+'\n').encode());add(p)
    ordinary=next(v for v in controls if v['label']=='malloc-24-nonzero-hypothesis');free=next(v for v in controls if v['label']=='free-BOOL-1')
    def dynamic(value):
        value=dict(value)
        replacements={regs['ebp']:'entry.EBP',regs['ebx']:'entry.EBX',regs['esi']:'entry.ESI',regs['edi']:'entry.EDI',PREVIOUS:'carried.FS0',0x30000000:'validated.guest_pointer'}
        value['source_accesses']=[dict(v,value_expression=replacements.get(v['value'],hex(v['value']))) for v in value['source_accesses']]
        return value
    p=out/'malloc24-source-ledger.json';publish_bytes(p,(json.dumps(dynamic(ordinary),indent=2)+'\n').encode());add(p)
    p=out/'free-source-ledger.json';publish_bytes(p,(json.dumps(dynamic(free),indent=2)+'\n').encode());add(p)
    report=dict(schema='mw34-m4-allocation-static-recovery-v1',passed=True,
        scope='Complete mode1 malloc/free normal source semantics and meaningful reusable BEFORE prediction; no native execution',
        provider_sha256=PROVIDER_SHA,baseline_acceptance_sha256=ACCEPT_SHA,baseline_final_check_sha256=FINAL_SHA,
        spans=spans,exports=exports,API_owners=imports,data=data,source_commands=commands,
        source_bytes=469,source_spans=8,new_source_page_mappings_required=0,new_usable_allocation_mapping_required=True,
        caller_cleanup=dict(entry=0x78001843,terminal=0x7800184c,source_PCs=3,source_accesses=1,executed_bytes=9,
                            entry_ESP=0x2000185c,terminal_ESP=0x20001860,EAX=1,original_attach_continued=False),
        external_seams=dict(explicit_research_cdecl_only=True,original_source_CALL_claimed=False,
            malloc=dict(entry=0x780012b3,ESP=M,return_word=0xffffffe0,argument_address=M+4,argument=24),
            free=dict(entry=0x78001390,ESP=M,return_word=0xffffffd0,argument_address=M+4,argument=0x30000000),
            setup_each=dict(host_guest_stores=2,changes=['State.EIP.low32','State.ESP.low32','declared outer-return DWORD','declared cdecl argument DWORD']),
            after_malloc_caller_cleanup=dict(host_ESP_advance=4,original_source_cleanup_claimed=False),
            Runtime_CPU_and_call_records_carried=True,no_AFTER_machine_seed=True),
        malloc_contract=dict(entry=0x780012b3,source_PCs=49,source_accesses=39,source_CALLs=3,source_RETs=3,
            executed_bytes=ordinary['executed_source_bytes'],requested=24,rounded=32,frame='M',worker_EBP='M-24',
            SEH_record='M-40',HeapAlloc_frame='M-80',HeapAlloc_return_ESP='M-64',HeapAlloc_return=0x78001385,
            API_return_read_count=1,terminal_ESP='M+4',terminal_EAX='validated opaque guest pointer or genuineNULL',
            restored_nonvolatiles=['EBP','EBX','ESI','EDI'],terminal_ECX='actual carried _newmode0',
            newmode_file_identity_does_not_prove_original_DllMain=True,newmode_current_admitted_input=0),
        free_contract=dict(entry=0x78001390,source_PCs=33,source_accesses=25,source_CALLs=1,source_RETs=1,
            executed_bytes=free['executed_source_bytes'],frame='F',worker_EBP='F-4',SEH_record='F-20',
            HeapFree_frame='F-72',HeapFree_return_ESP='F-56',HeapFree_return=0x78001436,API_return_read_count=1,
            terminal_ESP='F+4',terminal_EAX='raw actual fullBOOL; CRT public return typevoid',
            terminal_ECX='carried previousFS0',mode1_cold_route=[0x7800cc39,0x7800cc3a,0x78001428],
            unreached_1425=True,restored_nonvolatiles=['EBP','EBX','ESI','EDI']),
        combined_delta=dict(source_PCs=85,source_accesses=65,source_CALLs=4,source_RETs=4,
            separate_API_return_reads=2,executed_source_bytes=9+ordinary['executed_source_bytes']+free['executed_source_bytes']),
        SEH_contract=dict(source_registers_previous_chain=True,normal_restores_exact_previous_chain=True,
            malloc_scope=0x7802e248,free_scope=0x7802e260,handler_address=0x7800ef03,
            scope_table_or_handler_dereferenced_on_normal_path=False,handler_called=False,exception_dispatch_or_unwind_proved=False,
            FS0_permission='existing owned DWORD RW',other_TIB_and_Policy_fields_changed=False,
            source_fault_after_registration_requires_separate_host_cleanup_not_original_SEH_credit=True),
        API_contract=dict(HeapAlloc=dict(handle='same private actual full64 HeapCreate HANDLE via opaque guesttoken',flags=0,
            bytes='source-rounded SIZE_T',result='actual full64 LPVOID mapped to owned guest extent; never truncation',
            initial_contents='actual full rounded extent copied from measured native allocation; no zero assumption',
            NULL='actual API outcome only, then source newmode0 NULL return',last_error='HeapAlloc does not promise extended GetLastError'),
            HeapFree=dict(handle='same private owning heap',flags=0,pointer='exact full64 owned allocation via validated guest pointer',
                success='actual nonzero BOOL; revoke pointer ownership after real success',failure='actualBOOL0 is failure despite source void RET; retain ownership for honest cleanup',
                duplicate_or_foreign_pointer='reject before host call, never deliberately double-free OS memory'),
            declared_guest_stdcall_effects=['EAX.low32 finite guest result/rawBOOL','ESP.low32+16','EIP.low32 authentic returnword'],
            original_API_internals_or_volatile_register_flag_equivalence=False),
        source_flags=dict(caller_TEST_undefined_AF=[0x78001843],malloc_logic_undefined_AF=[0x7800cc9a,0x7800cca4,0x780012d9],
            free_logic_undefined_AF=[0x780013b6],representative=0,universal_original_AF_equivalence=False,
            malloc_final='TEST guest pointer at12D9; NULL/newmode0 finalCMP0-0 atCC3F',
            free_final='source CMP mode1-2 at13C8: CF1/PF1/AF1/ZF0/SF1/OF0,mask95; DFcarried'),
        access_order=dict(PUSH='checked source store before ESP publication',POP='current generated ESP+4 publication before checked read',
            LEAVE='ESP=EBP before checked savedEBP read',RET='checked return read before EIP then ESP publication',
            universal_original_fault_partial_order_equivalence=False),
        static_formula_controls=14,requested_size_controls=[0,1,24,31,32,4096],formula_controls_are_native_evidence=False,
        independent_affine_prediction_tool=str(Path(model.__file__).absolute()),independent_affine_prediction_sha256=sha(model.__file__),
        memory_semantic_aliases='Derive captured aliases from owned address storage; do not count aliases as new mappings',
        future_dependencies=['mode2/3 smallblock allocators and lock9','nonzero _newmode withNULL invokes _callnewh5910',
            'SEH handlerEF03 execution/dispatch/unwind','persistent application heap and multi-allocation lifetimes',
            'original attach globals and serviceCALL1870 beyond184C','localecritical-section allocation/use/free caller',
            'successful argument/parser/environment/fullCRT startup'],
        primary_sources=[dict(url='https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapalloc',
            supports='Nonzero uninitialized allocation pointer orNULL with flags0, at least requested bytes, matchingHeapFree, no extendedLastError'),
            dict(url='https://learn.microsoft.com/en-us/windows/win32/api/heapapi/nf-heapapi-heapfree',
            supports='Same heap/pointer, actual nonzero success orzero failure, no use-after-free/double-free')],
        original_executed=False,native_executed=False,API_executed=False,usable_native_allocation_proved=False,
        live_heap_ownership_proved_by_this_static_tool=False,original_attach_proved=False,locale_initialized=False,
        full_heap_allocator_initialized=False,full_CRT_complete=False,whole_M4_complete=False,
        initial_dependency_check=initial,final_dependency_check=verify_manifest(files),elapsed_seconds=(time.perf_counter_ns()-started)/1e9,files=files)
    path=out/'report.json';publish_bytes(path,(json.dumps(report,indent=2)+'\n').encode());add(path)
    publish_bytes(out/'pins.json',(json.dumps(dict(files=files),indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,schema=report['schema'],report_sha256=sha(path),pins_sha256=sha(out/'pins.json'),
        source_bytes=469,source_spans=8,malloc49=ordinary['source_PC_count'],malloc39=ordinary['source_access_count'],
        free33=free['source_PC_count'],free25=free['source_access_count'],combined=report['combined_delta'])))


if __name__=='__main__':main(sys.argv[1])
