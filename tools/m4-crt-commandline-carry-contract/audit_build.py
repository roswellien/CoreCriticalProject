"""Read-only current carry source/build/IR/COFF association audit.

No original/provider/game or native worker is executed. Only LLVM metadata
inspection is run. Historical acceptance receipts are bound without expanding
superseded current-source manifests.
"""
import argparse
import ctypes as C
import difflib
import hashlib
import json
import ntpath
import re
import struct
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage


def need(ok,why):
    if not ok:raise ValueError(why)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def key(path):return ntpath.normcase(ntpath.normpath(str(Path(path).absolute())))


def one(text,after,before):
    need(text.count(after)==1,'Unique literal inverse seam '+after[:90])
    return text.replace(after,before)


def inverse_composition(text):
    text=one(text,'#include "filename.hpp"\n#include "carry.hpp"','#include "filename.hpp"')
    text=one(text,'namespace fn=mw34::m4_crt_filename;\nnamespace cm=mw34::m4_crt_commandline_carry;',
                  'namespace fn=mw34::m4_crt_filename;')
    text=one(text,'#include "carry_binding.inc"\n#include "filename_binding.inc"','#include "filename_binding.inc"')
    prefix='if(cm::producer_owner){auto*c=cm::current_producer(p,a);'
    for suffix in ['return c->read(a);}','c->write(a,v);return p;}','c->invoke(s,a,p);return p;}']:
        text=one(text,prefix+suffix,'')
    text=one(text,'return f->consume(a,p);','f->stop(a,p);')
    text=one(text,'if(cm::binding||cm::admitted_binding)return cm::current(*mg::owner)->read8(a,p);','')
    text=one(text,'if((cm::binding||cm::admitted_binding)&&mg::owner->state.gpr.rip.dword>=fn::stop_pc){cm::current(*mg::owner)->consumer_write(a,v,p);return p;}','')
    text=one(text,'if(p!=mg::owner)mg::owner->deny("Exact current parser opaque token",a,cm::parser_site);if(cm::binding||cm::admitted_binding)cm::current(*mg::owner)->parser_stop(s,a,p);','')
    text=text.replace('require(!cm::producer_owner&&!mg::owner,"Other bridge cannot use active mainargs owner");',
                      'require(!mg::owner,"Other bridge cannot use active mainargs owner");')
    guard='if(cm::producer_owner)cm::current_producer(cm::producer_owner,0)->deny("Other bridge cannot use active command-line producer");'
    need(text.count(guard)==9,'Nine explicit old-bridge exclusive producer guards')
    text=text.replace(guard,'')
    owner='namespace mw34::m4_crt_commandline_carry {void outer_owner_guard(mg::Context&c){if(!::owner||&::owner->state()!=&c.state)c.deny("Exact active outer CRT entry scheduling owner required",writer,writer);::owner->guard();if(c.runtime.cpu().eip!=mg::slot||c.runtime.cpu().esp!=0x20001860)c.deny("Exact outer mainargs service CPU frame required",writer,writer);}}\n'
    text=one(text,owner,'')
    end='extern "C" void*mw34_carry_source_end(State*s,unsigned a,void*p)noexcept(false){if(!cm::producer_owner)throw std::runtime_error("Command-line producer end owner absent");cm::current_producer(p,a)->finish(s,a,p);return p;}\n'
    return one(text,end,'')


def inverse_driver(text):
    text=one(text,'namespace mw34::m4_crt_commandline_carry {void checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}}\n','')
    lines=text.splitlines(True)
    packed=[line for line in lines if line.startswith('namespace {Api commandline_api(')]
    evidence=[line for line in lines if line.startswith('  std::array<unsigned,28>commandline_job')]
    need(len(packed)==len(evidence)==1,'Unique additive packed identity/POD ledger output lines')
    need('a.address=h.target;' in packed[0] and 'a.owner_named=h.owner_named_target;' in packed[0] and
         'std::memcpy(a.sha,h.module_sha.data(),64);' in packed[0] and 'std::copy(h.module_path.begin(),h.module_path.end(),a.path);' in packed[0],
         'Actual packed API witness source association')
    for name in ('commandline-job.bin','commandline-accesses.bin','commandline-consumer-accesses.bin','commandline-events.bin',
                 'commandline-api-before.bin','commandline-api-after.bin','commandline-api-bytes.bin',
                 'commandline-host-pointer.bin','commandline-host-regions.bin','commandline-api-identity.json','commandline-reason.txt'):
        need(name in evidence[0],'Complete new POD/actual identity output '+name)
    text=one(text,packed[0],'');text=one(text,evidence[0],'')
    changes=[('MW34_CRT_COMMANDLINE_CARRY_NO_MAIN','MW34_CRT_FILENAME_NO_MAIN'),('scenario+49','scenario+37'),
             ('cm::Binding commandline(mainargs.context,provider,mode);',''),
             ('cm::binding=&commandline;cm::admitted_binding=&commandline;',''),('cm::producer_owner=nullptr;',''),
             ('entry_job.fault_pc==cm::parser_site&&entry_job.fault_target==cm::parser','entry_job.fault_pc==fn::stop_pc&&entry_job.fault_target==fn::commandline'),
             ('entry_job.fault_pc!=cm::parser_site||entry_job.fault_target!=cm::parser','entry_job.fault_pc!=fn::stop_pc||entry_job.fault_target!=fn::commandline'),
             ('"Literal builder consumes actual owned command line then stops before parser body"','"Literal builder resumes after native filename stdcall return and stops before command-line producer read"'),
             ('snapshot(r,row,"retry-after");cm::binding=nullptr;cm::admitted_binding=nullptr;','snapshot(r,row,"retry-after");')]
    for after,before in changes:text=one(text,after,before)
    return text


def layouts(guest_path,host_path,llvm):
    sys.path.insert(0,str(ROOT/'tools/lifting'))
    from host_adapter import LLVM,HOST_LAYOUT
    api=LLVM(llvm/'LLVM-C.dll')
    answer=[]
    for path in (guest_path,host_path):
        ctx=api.ContextCreate();module,buffer,error=C.c_void_p(),C.c_void_p(),C.c_void_p();data=None
        try:
            api.check(api.CreateMemoryBufferWithContentsOfFile(str(path).encode(),C.byref(buffer),C.byref(error)),error)
            api.check(api.ParseIRInContext(ctx,buffer,C.byref(module),C.byref(error)),error)
            api.check(api.VerifyModule(module,2,C.byref(error)),error)
            data=api.CreateTargetData(api.GetDataLayoutStr(module))
            table={}
            for name in re.findall(r'^%([^ =]+) = type',path.read_text(),re.M):
                ty=api.GetTypeByName2(ctx,name.encode());need(ty and not api.IsOpaqueStruct(ty),'Complete actual named State type')
                table[name]=dict(size=api.ABISizeOfType(data,ty),align=api.ABIAlignmentOfType(data,ty),
                    offsets=[api.OffsetOfElement(data,ty,i) for i in range(api.CountStructElementTypes(ty))])
            need(api.signature(api.GetNamedFunction(module,b'sub_7800188c'))==('ptr',['ptr','i32','ptr']),'Actual State/GuestPC/token ABI')
            answer.append(dict(pointer_bytes=api.PointerSize(data),types=table))
        finally:
            if data:api.DisposeTargetData(data)
            if module.value:api.DisposeModule(module)
            api.ContextDispose(ctx)
    need(answer[0]['pointer_bytes']==4 and answer[1]['pointer_bytes']==8,'Actual guest32/host64 pointer sizes')
    need(answer[0]['types']==answer[1]['types'] and answer[1]['types']['struct.State']['size']==3504,
         'All named actual guest/host State layouts preserved')
    need(f'target datalayout = "{HOST_LAYOUT}"' in host_path.read_text(),'Actual AMD64 ABI data layout')
    return answer


def main(prep_name,build_name,build_sha,prep_pins_sha):
    base=ROOT/'reports/m4-crt-commandline-carry';prep=base/prep_name;build=base/build_name
    out=base/'source-contract-r2'
    need(not out.exists(),'Fresh owned final source contract report')
    need(sha(build/'build.json')==build_sha and sha(prep/'pins.json')==prep_pins_sha,'Exact frozen final source/build identities')
    pins={}
    def bind(path,expected=None):
        path=Path(path).absolute();actual=sha(path);k=key(path)
        need(expected is None or actual==expected,'Physical association changed '+str(path))
        need(k not in pins or pins[k]['sha256']==actual,'Same physical path association conflict')
        pins[k]=dict(path=str(path),sha256=actual)
        return actual
    manifest=read(build/'build.json');previous=read(ROOT/'reports/m4-crt-filename/build-r7/build.json')
    need(manifest['passed'] and previous['passed'],'Actual passed final and predecessor builds')
    bind(build/'build.json',build_sha);bind(prep/'pins.json',prep_pins_sha)
    bind(ROOT/'reports/m4-crt-filename/build-r7/build.json','1868574163cdbce4491afe2217688ef549189f184e20549e31f68e44930fb1d5')
    bind(ROOT/'reports/m4-crt-filename/root-acceptance-r1/report.json')
    bind(base/'source-contract-r1/report.json','7d06d03bfbd3a7e419622d002a7a2701af6cba80c17ba3f5ab062572600bc59c')
    for category in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
        for path,digest in manifest[category].items():bind(path,digest)
    for path,digest in read(prep/'pins.json')['files'].items():bind(path,digest)
    bind(prep/'report.json',manifest['preparation_sha256'])
    need(key(manifest['preparation_path'])==key(prep/'report.json'),'Final preparation/build association')
    for path,digest in manifest['sources'].items():bind(build/'sources'/Path(path).relative_to(ROOT),digest)
    need(manifest['libraries']==previous['libraries'] and len(manifest['libraries'])==2,'Two unchanged FDIV libraries')
    need(len(previous['entry_objects'])==12 and all(manifest['entry_objects'].get(path)==digest
          for path,digest in previous['entry_objects'].items()),'Twelve frozen guest COFF objects preserved')
    new={path:digest for path,digest in manifest['entry_objects'].items() if path not in previous['entry_objects']}
    need(set(map(key,new))=={key(prep/f'producer-{level}.obj') for level in ('O0','O2')},'Exactly two new literal writer COFF objects')
    old=ROOT/'reports/m4-crt-filename/preparation-r8'
    unchanged=[];diffs={}
    changed={'composition.cpp','main_v2.inc','observations.hpp','mainargs_binding.inc','filename.hpp','filename_binding.inc'}
    names=sorted(p.name for p in old.iterdir() if p.suffix in('.cpp','.hpp','.inc'))
    need(len(names)==16,'Exact accepted filename source component inventory')
    for name in names:
        bind(old/name);bind(prep/(name+'.ancestor'))
        need((old/name).read_bytes()==(prep/(name+'.ancestor')).read_bytes(),'Exact frozen predecessor copy')
        if name not in changed:
            need((old/name).read_bytes()==(prep/name).read_bytes(),'Frozen source component changed '+name)
            unchanged.append(name)
        else:diffs[name]=''.join(difflib.unified_diff((old/name).read_text().splitlines(True),(prep/name).read_text().splitlines(True),name+'.ancestor',name))
    need(inverse_composition((prep/'composition.cpp').read_text())==(old/'composition.cpp').read_text(),'Exact additive composition inverse')
    need(inverse_driver((prep/'main_v2.inc').read_text())==(old/'main_v2.inc').read_text(),'Exact driver inverse; all old source/map/registry/seed logic retained')
    text=(prep/'mainargs_binding.inc').read_text()
    text=one(text,'mainargs_checkpoint(r,"mainargs-before");if(cm::binding||cm::admitted_binding)cm::current(c)->initialize();project(c.state,r.cpu());',
                  'mainargs_checkpoint(r,"mainargs-before");project(c.state,r.cpu());')
    need(text==(old/'mainargs_binding.inc').read_text(),'Exactly one late scheduling seam in unchanged mainargs binding')
    text=one((prep/'filename.hpp').read_text(),'unsigned consume(unsigned,void*);','[[noreturn]]void stop(unsigned,void*);')
    need(text==(old/'filename.hpp').read_text(),'Filename declaration-only continuation seam')
    text=one((prep/'filename_binding.inc').read_text(),'unsigned Binding::consume(unsigned address,void*p)','[[noreturn]]void Binding::stop(unsigned address,void*p)')
    text=one(text,'stopped=true;return cm::current(context)->consume(address,p);',
                  'stopped=true;context.event(6,stop_pc,commandline,0);context.first("Required initialized CRT command-line producer remains unresolved",commandline,stop_pc);\n throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{stop_pc},{commandline},context.reason);')
    need(text==(old/'filename_binding.inc').read_text(),'Filename retains actual API/frame/witness/source guards and changes only prior stop continuation')
    lines=(prep/'observations.hpp').read_text().splitlines(True)
    extras=[line for line in lines if line.startswith(' {std::array<std::byte,11>a{};')]
    need(len(extras)==1 and 'fresh_output(phase/"commandline-source.bin",a)' in extras[0] and
         'fresh_output(phase/"commandline-owned.bin",b)' in extras[0],'Additive exact source/owned byte observations')
    need(one(''.join(lines),extras[0],'')==(old/'observations.hpp').read_text(),'Exact observation inverse')
    provider=bind(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    bind(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    pe=PEImage((ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
    def literal(va,n):offset,_=pe.rva_range(va-pe.image_base,n);return pe.data[offset:offset+n]
    need(literal(0x7800188c,11)==(prep/'writer-original.bin').read_bytes()==bytes.fromhex('ff1534e00278a374710378'),'Eleven actual unchanged writer bytes')
    need(struct.unpack('<I',literal(0x7802e034,4))[0]==0x3442e,'Exact raw commandline IAT word')
    need(literal(0x7800bbd6,38)==(base/'source-contract-r1/consumer-source.bin').read_bytes(),'Actual38B downstream consumer source')
    guest=(prep/'guest.ll').read_text();candidate=(prep/'candidate.ll').read_text();host=(prep/'host.ll').read_text()
    need(candidate==guest.replace('@__remill_missing_block(','@mw34_carry_source_end('),'Exactly one symbol retarget; no authored capture jump/guest RET')
    pattern=r'(?ms)^define ptr @sub_7800188c\(.*?^}\n'
    need(re.search(pattern,candidate).group()==re.search(pattern,host).group(),'Actual host writer instruction body exactly unchanged')
    types=lambda text:re.findall(r'^%[^\n]+',text,re.M)
    need(types(guest)==types(host),'All exact software guestState types preserved')
    need(not re.search(r'\b(?:nounwind|inttoptr|ptrtoint|poison|undef)\b',host),'Typed guest-address bridge and real C++ unwind admission')
    need(host.index('%15 = call noundef ptr @__remill_write_memory_32')<host.index('store i32 %10, ptr %8')<host.index('store i32 %11, ptr %16')<host.index('%19 = call ptr @__remill_function_call'),
         'Real CALL checked-return-store before ESP and targetPC publication')
    need(host.count('@mw34_carry_source_end(')==2 and 'ret ptr %34' in host and 'jmp' not in host,
         'Real missing-block fragment end1897; no guest RET/fake return transport')
    body=(prep/'carry_binding.inc').read_text();header=(prep/'carry.hpp').read_text()
    need(header.count('admitted_frame_{}')==1 and 'private:' in header[:header.index('admitted_frame_{}')], 'Private actual admitted scheduling frame')
    need(body.count('admitted_frame_=')==1 and body.count('admitted_pc_=')==1,'Immutable once-captured frame and continuation')
    init=body[body.index('void Binding::initialize'):body.index('void Binding::consumer_guard')]
    ordered=['checkpoint(context.runtime,"commandline-producer-before")','admitted_frame_=frame','context.state.gpr.rip.dword=writer',
             'mw34_carry_cmd_writer_body','checkpoint(context.runtime,"commandline-producer-after")',
             'expected.gpr.rax.dword=buffer;expected.gpr.rip.dword=end;',
             'producer_owner=nullptr;context.state.gpr.rip.dword=saved_pc;context.runtime.cpu().eax=buffer;',
             'checkpoint(context.runtime,"commandline-carry-after")']
    pos=[init.index(t) for t in ordered];need(pos==sorted(pos),'Actual native writer plus explicit PC/EAX continuation; no State seed')
    invoke=body[body.index('void Binding::invoke'):body.index('void Binding::finish')]
    ordered=['call_closure(s,target,p);','caller_error=errors.saved','host=old::own_host_input()',
             'actual_host_=host;actual_bytes_=host.bytes;','checkpoint(context.runtime,"commandline-api-after")',
             'memory().map({buffer},size','memory().write({buffer},actual_bytes_)','memory().protect({buffer},Permissions::read)',
             'checkpoint(context.runtime,"commandline-buffer-after")','context.state.gpr.rax.dword=buffer;',
             'context.state.gpr.rsp.dword=admitted_frame_;','context.state.gpr.rip.dword=ret;']
    pos=[invoke.index(t) for t in ordered];need(pos==sorted(pos),'Current owner before stale effects; actual owned API witness/full checked copy before service return publication')
    need('memory().map(' not in init and body.count('memory().map(')==1 and body.count('memory().unmap(')==0 and
         'memory().unmap({buffer})' in header,'Only new owned buffer; borrow all16oldmappedpages')
    need('stable_hook(6);consumer_guard(p);' in body and 'stable_hook(8);consumer_guard(p);' in body and
         'source_identity();context.source_identity();if(!ready())' in body,'Current private frame/source/owned-input and State/FX closure before consumer and parser stop')
    need('throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{parser_site},{parser},reason);' in body and
         'context.state.gpr.rsp.dword!=f||consumer_access_count!=9' in body,'Required parser stop after actual real CALL/checked frame')
    need('active=false;depth=0;producer_owner=nullptr;' in init and 'catch(const mg::BridgeAbort&)' in init,
         'Typed producer activity/depth/current owner cleared through catch')
    llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    bind(ROOT/'tools/lifting/host_adapter.py','97b101725526866a2a2fa4788be3a850f11da49fbf7cb563cefa1eed44c5b5ed')
    actual_layouts=layouts(prep/'guest.ll',prep/'host.ll',llvm)
    need(actual_layouts[1]['types']==read(prep/'layout.json')['layouts'],'Preparation layout record agrees with independent actual LLVM layout inspection')
    inspect=llvm/'llvm-readobj.exe';bind(inspect)
    static=[];out.mkdir()
    for level in ('O0','O2'):
        cc=build/level/'compile_commands.json';bind(cc)
        rows=read(cc);compiled=[r for r in rows if Path(r['file']).name=='composition.cpp']
        need(len(compiled)==1 and key(compiled[0]['file'])==key(prep/'composition.cpp'),'Exact actual compiled current composition')
        command=compiled[0]['command']
        need('/EHs' in command and '/EHsc' not in command and ('/Od' if level=='O0' else '/O2') in command and
             'ADDRESS_SIZE_BITS=32' in command and str(prep).lower() in command.lower(),'Actual level/exception/guest-State header recipe')
        composition=next(Path(p) for p in manifest['artifacts'] if p.endswith('composition.cpp.obj') and '/'+level+'/' in p.replace('\\','/'))
        for label,obj in [('composition',composition),('producer',prep/f'producer-{level}.obj')]:
            args=[str(inspect),'--file-headers','--unwind','--symbols','--relocations',str(obj)]
            run=subprocess.run(args,capture_output=True,timeout=30)
            need(run.returncode==0,'Read-only COFF inspection')
            target=out/f'{label}-{level}-coff.txt';target.write_bytes(run.stdout)
            err=out/f'{label}-{level}-coff.stderr';err.write_bytes(run.stderr)
            content=run.stdout.decode()
            need('IMAGE_FILE_MACHINE_AMD64' in content and 'RuntimeFunction {' in content,'Actual AMD64 unwind records')
            if label=='composition':need('__CxxFrameHandler3' in content and 'Binding@m4_crt_commandline_carry' in content,'Actual C++ typed carry/language exception closure')
            else:
                need('mw34_carry_cmd_writer_body' in content and 'sub_7800188c' in content and
                     '__remill_function_call' in content and 'mw34_carry_source_end' in content,'Actual literal producer symbol/bridge association')
            static.append(dict(arguments=args,exit_code=run.returncode,output_sha256=bind(target),stderr_sha256=bind(err)))
        worker=Path(manifest['workers'][level]);data=worker.read_bytes();offset=struct.unpack_from('<I',data,0x3c)[0]
        need(data[offset:offset+4]==b'PE\0\0' and struct.unpack_from('<H',data,offset+4)[0]==0x8664,'Actual linked AMD64 worker')
        need(any('llc.exe' in c['arguments'][0] and '-'+level in c['arguments'] and str(prep/'host.ll') in c['arguments']
                 for c in read(prep/'report.json')['commands']),'Current producer IR/level compile association')
    for name,diff in diffs.items():(out/(name+'.diff')).write_text(diff);bind(out/(name+'.diff'))
    for path in [Path(__file__),ROOT/'tools/analysis/pe.py',base/'source-contract-r1/consumer-source.bin',base/'source-contract-r1/pins.json',
                 ROOT/'reports/m4-crt-mainargs/recovery-r3/normal_argv-host.ll',ROOT/'tools/m4-crt-commandline-native/host_input.hpp',
                 ROOT/'runtime/memory/guest_memory.cpp',ROOT/'tools/m4-crt-fdiv/host_services.hpp']:bind(path)
    report=dict(passed=True,scope='Independent read-only actual-source/API/scheduling/derivative/ABI/build/COFF association; no worker or original code execution',
                build_sha256=build_sha,preparation_pins_sha256=prep_pins_sha,
                unchanged_ancestor_components=unchanged,exact_additive_inverse_components=sorted(changed),
                unchanged_guest_COFF_objects=12,unchanged_FDIV_libraries=2,new_literal_producer_COFF_objects=2,
                whole_guest_State_type_layouts_checked=len(actual_layouts[1]['types']),software_State_size=3504,
                compiled_State_header_sha256=manifest['compiler_read_headers'][str(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h')],
                borrowed_provider_and_stack_pages=16,new_owned_buffer=0x33000000,source_IAT_rewritten=False,State_or_FX_reseed=False,
                scheduling_seam=dict(point='After unchanged mainargs-before, before existing native provider projection',
                    producer_entry=0x7800188c,producer_frame=0x20001860,entry_effect='Only State PC overlay',
                    real_CALL_IAT=0x7802e034,raw=0x3442e,real_return_word=0x78001892,
                    original_bytes=11,compiled_MOV_global=0x78037174,end_missing_block=0x78001897,
                    continuation='Explicit savedStatePC restore; actual produced guest EAX transported into RuntimeCPU.EAX before unchanged original projection',
                    guest_RET=False,authored_capture_JMP=False,DllMain_process_attach_order_proved=False),
                consumer=dict(source_bytes=38,executed_source_instructions=14,actual_source_accesses=9,
                    admitted_actual_OS_witness_branch='Nonempty ANSI command line',
                    pgmptr_store=0x7803b3e0,first_byte_CMP=0x7800bbe3,
                    real_CALL=0x7800bbf7,actual_target=0x7800bc48,actual_return_word=0x7800bbfc,
                    parser_entry_ESP=0x2000182c,args=[0x33000000,0,0,0x20001850,0x2000184c],
                    parser_body_executed=False,allocator_locale_or_outputs_implemented=False,
                    partial_order='Checked IAT read then checkedCALL store precedesESP/PC; consumer MOV/CMP checkedreads precederesults; everyPUSH/CALL checkedstore precedesESP; pgmptrstore beforefirstbyteCMP'),
                actual_API_contract='Measured GetCommandLineA bounded borrowed ANSI string is copied includingNUL into owned readonly GuestAddress; full hostpointer+APIidentity/regions remain metadata. Explicit service preserves other State/FX; originalx86 volatile equality unclaimed.',
                typed_internal_provider_context_not_generic_Runtime_frame=True,public_fault_Runtime_poison_and_cleanup=True,
                static_metadata_commands=static,original_executed=False,native_worker_executed=False,game_launched=False,
                limitations=['Independent compiled hostile fixtures and root BEFORE-only source/State/FX/pages proof remain separate acceptance gates.',
                    'Actual API witness selects nonempty branch; empty commandline fallback source is recovered but carries no native execution credit.',
                    'No original DLL attach scheduling or x86 API volatile-register equality is inferred from the authored late seam.',
                    'No parser body/argc/argv/env, full CRT/MFC/window/menu or wholeM4 completion credit.',
                    'SDK search environment is recorded rather than a library-file-open attestation.'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json')
    for info in pins.values():need(sha(info['path'])==info['sha256'],'Final unique physical source/artifact rehash')
    (out/'pins.json').write_text(json.dumps(dict(files={i['path']:i['sha256'] for i in sorted(pins.values(),key=lambda i:i['path'].lower())}),indent=2)+'\n')
    print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),physical_associations=len(pins))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('preparation');p.add_argument('build');p.add_argument('build_sha256');p.add_argument('preparation_pins_sha256')
    a=p.parse_args();main(a.preparation,a.build,a.build_sha256,a.preparation_pins_sha256)
