"""Author static admission of the compiled real-stack scaffold; no execution.

This is preparatory author evidence, not an independent reviewer or oracle.
"""
import argparse,hashlib,json,pathlib,re,struct,subprocess,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-fdiv-reference'
def sha(p):
    with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def need(v,m):
    if not v:raise ValueError(m)
def main(out):
    out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh private static review required');out.mkdir()
    files={};history=[];commands=[]
    def bind(p,h=None):
        p=pathlib.Path(p).resolve();value=sha(p);need(h is None or value==h,'Exact physical binding '+str(p));files[str(p)]=value;return value
    build=BASE/'build-r3/build.json';m=read(build);bind(build)
    need(m['passed']and m['original_executed']is False and m['native_executed']is False,'Actual successful build-only report required')
    for group in('source_files','tool_files','compiler_read_headers','artifacts'):
        for p,h in m[group].items():bind(p,h)
    prep=BASE/'preparation-r2/pins.json';bind(prep)
    for p,h in read(prep)['files'].items():bind(p,h)
    for previous in('build-r1','build-r2'):
        p=BASE/previous/'build.json';old=read(p);bind(p);copies={v['original_path']:v for v in old['literal_source_copies']};resolved_copies={str(pathlib.Path(k).resolve()):v for k,v in copies.items()}
        for original,h in old['source_files'].items():
            copy=copies[original];need(copy['sha256']==h,'Exact historical literal source association');bind(copy['preserved_path'],h)
            if sha(original)!=h:history.append({'historical_map':str(p),'original_path':original,'literal_path':copy['preserved_path'],'sha256':h})
            else:bind(original,h)
        for group in('tool_files','compiler_read_headers','artifacts'):
            for original,h in old[group].items():
                if sha(original)!=h:
                    copy=resolved_copies.get(str(pathlib.Path(original).resolve()));need(copy is not None and copy['sha256']==h,'Changed historical dependency has an explicit literal source copy');bind(copy['preserved_path'],h)
                else:bind(original,h)
    for p in(BASE/'preparation-attempt-r1').rglob('*'):
        if p.is_file():bind(p)
    for p in(BASE/'static-scaffold-review-r1').rglob('*'):
        if p.is_file():bind(p)
    worker=pathlib.Path(m['worker']);binary=worker.read_bytes();pe=struct.unpack_from('<I',binary,0x3c)[0];optional=pe+24
    need(struct.unpack_from('<H',binary,pe+4)[0]==0x14c and struct.unpack_from('<H',binary,optional)[0]==0x10b,'Actual compiled x86 PE32 worker')
    base=struct.unpack_from('<I',binary,optional+28)[0];need(base==0x34000000,'Actual PE fixed declared disjoint base')
    need(not(struct.unpack_from('<H',binary,optional+70)[0]&0x40),'Actual worker DYNAMIC_BASE excluded')
    reserve,commit=struct.unpack_from('<2I',binary,optional+72);need((reserve,commit)==(1048576,65536),'Actual PE stack policy')
    original=(ROOT/'tools/m4-crt-control-integration/original_broker.hpp').read_text()
    derivative=(ROOT/'tools/m4-crt-fdiv-reference/original_broker.hpp').read_text()
    need(derivative==original.replace('std::array<std::uint32_t,6> bases{0x5a0000,0x5b0000,0x78000000,0x78010000,0x20000000,0x10000000}','std::array<std::uint32_t,5> bases{0x78000000,0x78010000,0x78020000,0x78030000,0x10000000}'),'Exact reviewed broker derivation changes only five reservations')
    bind(ROOT/'tools/m4-crt-control-integration/original_broker.hpp')
    llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    def tool(name,args,log):
        program=llvm/name;h=bind(program);result=subprocess.run([str(program),*map(str,args)],capture_output=True);(out/log).write_bytes(result.stdout);(out/(log+'.stderr')).write_bytes(result.stderr);need(result.returncode==0,'Actual static tool completed');bind(program,h);bind(out/log);bind(out/(log+'.stderr'));commands.append({'program':str(program),'sha256_before_after':h,'arguments':list(map(str,args)),'exit_code':result.returncode,'stdout':str(out/log),'stderr':str(out/(log+'.stderr'))});return result.stdout.decode('utf-8')
    obj=ROOT/'build/m4-crt-fdiv-reference-build-r3/fdiv_reference.dir/Release/reference_x86.obj'
    asm=tool('llvm-objdump.exe',['-dr','--x86-asm-syntax=intel',obj],'scaffold-coff.txt')
    image=tool('llvm-readobj.exe',['--file-headers','--sections','--coff-imports',worker],'worker-pe.txt')
    capture=asm.split('<_fd_capture>:',1)[1].split('<_fd_restore>:',1)[0]
    # Exact compiled ordering: all result GPRs/flags are stored before direct
    # hardware FX/ENV, before any FS metadata read/copy/restore/C++ return.
    positions=[capture.index('IMAGE_REL_I386_DIR32\t_fd_after'),capture.index('pushfd'),capture.index('IMAGE_REL_I386_DIR32\t_fd_fx_after'),capture.index('IMAGE_REL_I386_DIR32\t_fd_env_after'),capture.index('fs:[0x8]'),capture.index('IMAGE_REL_I386_DIR32\t_fd_stack_after'),capture.index('IMAGE_REL_I386_DIR32\t_fd_host_fx'),capture.index('popal')]
    need(positions==sorted(positions)and'call\t'not in capture,'Actual direct capture order, without called cleanup')
    before=asm.split('<_fd_enter>:',1)[1].split('<_fd_capture>:',1)[0]
    need('push\t0x10000100'in before and'IMAGE_REL_I386_DIR32\t_fd_writer_sp'in before and'jmp\tdword ptr [0x24]'in before,'Actual natural outer-frame scaffold, restored natural source ESP')
    for name in('GetModuleHandleA','GetProcAddress','CreateThread','GetThreadContext','SetThreadContext','AddVectoredExceptionHandler','VirtualAllocEx','VirtualQueryEx','WriteFile','FlushFileBuffers'):
        need('Symbol: '+name+' ('in image,'Actual compiled Windows import '+name)
    source=(ROOT/'tools/m4-crt-fdiv-reference/reference.cpp').read_text();header=(ROOT/'tools/m4-crt-fdiv-reference/common.hpp').read_text()
    need('probe::put32(pages[3]+0x98,'in source and'probe::put32(pages[3]+0xd0,'in source and source.count('probe::put32(pages[')==2,'Exactly two declared original IAT fixups')
    need('p->ContextRecord->EFlags|=0x10000U;'in source and'p->ContextRecord->Dr6&=~15U;'in source and'CONTEXT_CONTROL|CONTEXT_INTEGER|CONTEXT_DEBUG_REGISTERS'in source,'Exact admitted debug context and continuation intervention')
    need('CreateThread(nullptr,65536,thread_entry,nullptr,CREATE_SUSPENDED' in source and source.index('GetThreadContext(thread.value')<source.index('ResumeThread(thread.value'),'Only suspended thread context setup')
    need('v.state==MEM_COMMIT&&v.type==MEM_PRIVATE&&v.protect==PAGE_READWRITE'in source and'maximum_stack'in source and'PAGE_GUARD'in source,'Actual bounds/protection/guard exclusion code required')
    need('CREATE_NEW'in header and'DeleteFile'not in header and'"COMPLETE"'in header,'Owned output retains failed observations and terminal success marker')
    need('sizeof(Record)==91348'in header and'sizeof(CONTEXT)==716'in header and'sizeof(DebugEvent)==1520'in header,'Actual compiled static layout assertions')
    for p in(ROOT/'tools/m4-crt-fdiv-reference').rglob('*'):
        if p.is_file():bind(p)
    report={'passed':True,'scope':'Author static source/ABI/ownership and actual compiled scaffold preparation; original execution remains pending root review','original_executed':False,'native_executed':False,'build_path':str(build),'build_sha256':sha(build),'worker':str(worker),'worker_sha256':sha(worker),'worker_PE32_base':base,'worker_PE_stack_reserve_commit':[reserve,commit],'compiled_scaffold_object':str(obj),'compiled_scaffold_sha256':sha(obj),'project_source_bindings':len(m['source_files']),'primary_tool_bindings':len(m['tool_files']),'actual_compiler_read_headers':len(m['compiler_read_headers']),'source_pack_sha256':'fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80','provider_sha256':'2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7','body_entry':0x78004254,'outer_authored_capture':0x10000100,'original_DLL_parent_return_not_executed':0x78004232,'debug_return_PCs':[0x780042ae,0x780042c2,0x780042ce],'literal_original_source_CALL_RETs_unchanged':True,'original_IAT_fixups':[0x7802e098,0x7802e0d0],'real_thread_stack':{'initial_commit':65536,'maximum_observed_bytes':1048576,'capture':'Every admitted committed ordinary RW page between actual NT_TIB StackLimit and StackBase; bounds/VirtualQuery/guard metadata retained before/after. Assembly records real W=H-4 and source uses it naturally. A temporary owned non-thread scratch ESP is used only for instrumented PUSHFD/POP stores outside source/API execution, avoiding mutation of original residual stack words.','extent_growth_policy':'Retain observation and fail initial comparison admission; no invented before bytes for new pages.','actual_loaded_base_or_reservation_proof':'Pending actual brokered worker execution. PE declaration is static, not an observed loaded image or successful reservation.'},'capture':{'direct_original':'MOV-only GPR store then PUSHFD image, FXSAVE512/FNSTENV28 and full admitted actual stack/source pages before restoration or C++ cleanup. PUSHFD is its architectural stored flag image and does not observe RF/VM bits as live CPU bits.','host_restore':'Full host FX/ENV assembly checkpoint only, not full volatile SIMD equality across surrounding C++ return.','debug':'Separate debug-off and debug-on corpus; raw EXCEPTION_RECORD and complete OS CONTEXT retained, context flags qualify FP fields. RF set and DR6 B0..B3 cleared explicitly, TF must already be clear. No source PC/GPR/stack/FARPROC change. Debug context FP is not direct FNSTENV; potential OS metadata effects are retained.'},'corpus_planned':{'CW_words':[0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f],'initial_state':'Masked IC0 CW, empty TOP0/SW0, MXCSR1F80, nonzero raw empty x87 storage/legacy metadata; actual source query result is observed.','fresh_repeats':2,'debug_off_rows':24,'debug_on_rows':24,'rows':48,'fallback':'Exact static fallback retained; NULL/changed service targets or unexpected events yield retained failed observations without native equivalence credit.'},'raw_schema':{'magic':'MW4FDOR1','version':1,'header_bytes':32,'record_prefix_bytes':91348,'tags_bytes':108,'CPU_bytes_each':40,'FX_bytes_each':512,'ENV_bytes_each':28,'source_pages_each':7,'debug_event_bytes':1520,'maximum_debug_events':8,'CONTEXT_bytes':716,'EXCEPTION_RECORD_bytes':80,'variable_row':'DWORD row_bytes, Record, before stack-page HostRegion40 rows, after stack-page HostRegion40 rows, direct stack-before bytes, direct stack-after bytes; terminal COMPLETE only on all actual accepted rows.','residual_unspecified_halves':['W-34..W-32','W-42..W-40'],'native_projection':'None performed by this original-only worker. Later stack addresses, outer capture PC, actual32/64bit API pointer identity and ABI-volatile residual bytes require explicit separately reviewed projection.'},'history':history,'commands':commands,'limitations':['No original code execution, initialized flag or actual API-result claim yet.','No full DllMain/CRT/game launch, SEH/unwind, menu or M4 completion.','Authored outer caller/capture and debug intervention are instrumentation, not provider source.','Initial serial fresh ordinary private directories and stable loaded module assumptions; no general concurrent publisher/thread API.'],'whole_M4_complete':False}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':files,'historical_source_associations':history},indent=2)+'\n');print(json.dumps({'passed':True,'original_executed':False,'bindings':len(files),'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');main(p.parse_args().output)
