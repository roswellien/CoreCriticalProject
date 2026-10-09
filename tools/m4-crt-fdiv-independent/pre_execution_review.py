"""Root read-only review of the concrete original FDIV observation scaffold.

This never invokes the reference worker or an author comparator. It checks
physical inputs, provider page transport, PE layout and fresh compiled capture
ordering before authorizing one separately brokered original-only capture.
"""
import hashlib,importlib.util,json,re,struct,subprocess,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p)
    assert str(p) not in PINS or PINS[str(p)]==v;PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def main(out):
    assert not out.exists() and out.is_relative_to(ROOT/'reports/m4-crt-fdiv-reference');out.mkdir(parents=True)
    (out/'review-source.py').write_bytes(Path(__file__).read_bytes())
    try:
        base=ROOT/'reports/m4-crt-fdiv-reference'
        review=read(base/'static-scaffold-review-r2/report.json','5a4636904248a43f1fd95a9f4c24cb9b268c507bdf811273e993c2ffa2aee315')
        pins=read(base/'static-scaffold-review-r2/pins.json','d102a95d3b7da367b8f9ce306d97504a985b44596269ad86dab506d40e9c6d9c')
        assert len(pins['files'])==551
        for p,h in pins['files'].items():pin(p,h)
        build=read(base/'build-r3/build.json','75aebc9be6f078be70f43f57269f1c28dfe4f20d014c0ac7236484d80d983fdc')
        assert review['passed'] and build['passed'] and not review['original_executed'] and not build['original_executed']
        for key in ('source_files','tool_files','compiler_read_headers','artifacts'):
            for p,h in build[key].items():pin(p,h)
        worker=pin(build['worker'],'9066d65db5865990b0a00f1c512d61add0c6b8bb096e8a18f13f9cd5e141a2d3');b=worker.read_bytes()
        pe=struct.unpack_from('<I',b,60)[0];assert b[pe:pe+4]==b'PE\0\0'
        machine,sections=struct.unpack_from('<HH',b,pe+4);opt=pe+24
        assert machine==0x14c and struct.unpack_from('<H',b,opt)[0]==0x10b
        assert struct.unpack_from('<I',b,opt+28)[0]==0x34000000
        assert struct.unpack_from('<2I',b,opt+72)==(1048576,65536)
        assert not struct.unpack_from('<H',b,opt+70)[0]&0x40
        assert struct.unpack_from('<2I',b,opt+96+5*8)==(0,0),'No relocatable worker layout'
        p=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        s=importlib.util.spec_from_file_location('root_fdiv_pe',p);PE=importlib.util.module_from_spec(s);s.loader.exec_module(PE)
        provider=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
        pack=pin(base/'preparation-r2/pack.bin','fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80').read_bytes()
        assert len(pack)==28740 and pack[:8]==b'MW4FDIP1' and struct.unpack_from('<I',pack,8)[0]==7
        addresses=(0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000)
        recovery=read(ROOT/'reports/m4-crt-fdiv/source-recovery-r1/report.json','c124fbfbf5bf64125b9e93c52b9b0e0500f2dd93df6d6ee440b89f5d90f895fd')
        pages={a:bytearray([0xcc]*4096) for a in addresses}
        def transport(a,n):
            return provider.read(provider.rva_range(a-provider.image_base,n)[0],n)
        for span in recovery['source_spans']:
            a=span['address'];v=transport(a,span['size_bytes']);assert hashlib.sha256(v).hexdigest()==span['sha256']
            pages[a&~4095][a&4095:(a&4095)+len(v)]=v
        for ins in recovery['callback_orchestrator']['instructions']:
            a=ins['address'];v=transport(a,ins['size']);assert v.hex()==ins['bytes_hex'];pages[a&~4095][a&4095:(a&4095)+len(v)]=v
        for constant in recovery['fallback_constants']:
            a=constant['address'];v=transport(a,8);assert hashlib.sha256(v).hexdigest()==constant['sha256'];pages[a&~4095][a&4095:(a&4095)+8]=v
        for a in (0x7802e000,0x78037000):pages[a]=bytearray(transport(a,4096))
        graph_PCs=set()
        for graph in recovery['complete_graphs']:
            for ins in graph['instructions']:
                a,n=ins['address'],ins['size'];assert transport(a,n).hex()==ins['bytes_hex'] and pages[a&~4095][a&4095:(a&4095)+n]==transport(a,n);graph_PCs.add(a)
        assert len(graph_PCs)==204
        for j,(a,perm) in enumerate(zip(addresses,(5,5,5,1,1,1,3))):
            assert struct.unpack_from('<2I',pack,12+j*4104)==(a,perm)
            assert pack[20+j*4104:20+j*4104+4096]==pages[a],'Exact bounded original source/constant transport with literal whole IAT/data pages'
        tool=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
        obj=pin(review['compiled_scaffold_object'],'842f3ab81cd1e029914b62c71366a356d4033ac261762b44ab810cbfd496ac5b')
        command=[str(tool),'-dr','--x86-asm-syntax=intel',str(obj)];cp=subprocess.run(command,capture_output=True)
        (out/'scaffold-coff.txt').write_bytes(cp.stdout);(out/'scaffold-coff.stderr').write_bytes(cp.stderr);assert cp.returncode==0
        text=cp.stdout.decode();capture=text.split('<_fd_capture>:',1)[1].split('<_fd_restore>:',1)[0]
        ops=re.findall(r'^\s*[0-9a-f]+:\s+(?:[0-9a-f]{2}\s+)+\s*([a-z]+)',capture,re.M)
        assert ops[:14]==['mov']*9+['pushfd','pop','mov','fxsave','fnstenv'],'Direct CPU/FP before any clobber/copy/cleanup'
        assert capture.index('_fd_fx_after')<capture.index('_fd_env_after')<capture.index('_fd_limit_after')<capture.index('_fd_saved_esp')<capture.index('_fd_host_fx')
        enter=text.split('<_fd_enter>:',1)[1].split('<_fd_capture>:',1)[0]
        assert enter.index('_fd_host_fx')<enter.index('_fd_host_env')<enter.index('_fd_writer_sp')<enter.index('push\t0x10000100')<enter.index('_fd_guest_fx')<enter.index('_fd_fx_before')<enter.index('_fd_stack_before')
        assert len(re.findall(r'\bcall\b',text))==0,'Scaffold capture has no incidental CALL'
        asm=pin(ROOT/'tools/m4-crt-fdiv-reference/reference_x86.asm').read_text()
        source=pin(ROOT/'tools/m4-crt-fdiv-reference/reference.cpp').read_text()
        broker=pin(ROOT/'tools/m4-crt-fdiv-reference/original_broker.hpp').read_text()
        assert source.count('probe::put32(pages[')==2 and 'probe::put32(pages[3]+0x98,' in source and 'probe::put32(pages[3]+0xd0,' in source
        assert 'CreateThread(nullptr,65536,thread_entry,nullptr,CREATE_SUSPENDED' in source
        assert 'NtCurrentTeb()' in source and 'top-limit<=maximum_stack' in source and 'PAGE_READWRITE' in source
        assert 'p->ContextRecord->EFlags|=0x10000U;' in source and 'p->ContextRecord->Dr6&=~15U;' in source
        assert 'JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE' in broker and 'CREATE_SUSPENDED|CREATE_NO_WINDOW|EXTENDED_STARTUPINFO_PRESENT' in broker
        assert broker.index('AssignProcessToJobObject')<broker.index('VirtualAllocEx')<broker.index('ResumeThread')
        assert 'deadline_ms=180000' in broker and 'requires pre-CRT broker reservations' in broker
        runner=pin(ROOT/'tools/m4-crt-fdiv-reference/run_reference.py','eea9508b69df53704fbc1d15b6d068c645653155ed7ac116b9b8a00e00bb03b6').read_text()
        assert 'timeout=200' in runner and 'subprocess.run(command' in runner and 'admit()==association' in runner
        recipe=read(base/'launch-recipe-r1/launch-recipe.json','59aa8532522f62e76a97075911b1830ddab37539a54baf862b25dea33f0f8c87')
        assert not recipe['execute_requested'] and not recipe['original_executed']
        pin(__file__);pin(sys.executable)
        for p in out.iterdir():
            if p.is_file():pin(p)
        for p in (base/'root-pre-execution-review-r1').iterdir():
            if p.is_file():pin(p)
        report=dict(passed=True,scope='Root concrete pre-execution source/ABI/page-transport and compiled scaffold review; original execution still absent',original_executed=False,worker_PE32_base=0x34000000,worker_stack_reserve_commit=[1048576,65536],rehash_author_static_bindings=551,own_fresh_compiled_decode=True,private_provider_pages=7,whole_literal_IAT_and_data_pages=2,bounded_literal_source_dependency_PCs=204,unused_private_bytes_CC=True,source_IAT_transport_cells=2,natural_thread_stack_and_authored_outer_return=True,debug_off_direct_primary=True,debug_on_raw_OS_context_and_RF_DR6_intervention_separate=True,physical_bindings=len(PINS),reviewed_invocation=['C:/Python314/python.exe','-B','tools/m4-crt-fdiv-reference/run_reference.py','--execute','--output','reports/m4-crt-fdiv-reference/run-normal-r1'],authorization_scope='One bounded normal-Windows original-only isolated FDIV corpus; no admin/elevation, no whole DLL or game UI launch, no native equivalence/full-startup credit',limitations=['Current disk bindings and compiled source associations are not execution-time dependency attestation','Actual loaded base, reservation outcomes, stack/API identity and initialized data await the observed worker records','Successful broker NOACCESS checks are executed admission checks, not serialized region samples','The authored outer capture and separate debug instrumentation are not original provider instructions'],whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json')
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,physical_bindings=len(PINS),report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
