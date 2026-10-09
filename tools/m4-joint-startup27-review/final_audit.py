"""Assemble independent narrow selected27 review and read-only COFF evidence."""
from pathlib import Path
import argparse, importlib.util, json, re, subprocess, traceback
import sys
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('joint27_final_readonly',Path(__file__).with_name('observe.py'))
J=importlib.util.module_from_spec(spec);spec.loader.exec_module(J)

def function(text,name):
    blocks=re.split(r'(?m)^([0-9a-f]{16} <[^\n]+>:)\n',text)
    matches=[blocks[i+1] for i in range(1,len(blocks),2) if name in blocks[i] and blocks[i].startswith('0000000000000000 ')]
    J.need(len(matches)==1,'Unique primary compiled function '+name)
    return matches[0]

def main(out):
    J.need(out.parent==J.BASE and out.name.startswith('independent-') and not out.exists(),'Fresh final independent source/COFF receipt');out.mkdir()
    (out/'review-source.py').write_bytes(Path(__file__).read_bytes());rows=[]
    try:
        receipts={}
        for name in ('independent-repaired-paired-r1','independent-controls-r3','independent-checkpoint-r1'):
            path=J.BASE/name;r=json.loads(J.pin(path/'report.json').read_text());J.need(r['passed'],'Independent required positive/failure/checkpoint receipt '+name);receipts[name]={'report_sha256':J.sha(path/'report.json'),'pins_sha256':J.sha(path/'pins.json')}
            for p,h in json.loads(J.pin(path/'pins.json').read_text())['files'].items():J.pin(p,h)
        tool=J.pin(J.ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
        for kind,build in (('controls','boundary-build-r1'),('native','native-boundary-build-r1')):
            for level in ('O0','O2'):
                root=J.BASE/build/f'build-{level}'
                candidates=[p for p in root.rglob('*.obj') if p.name==('fixture.cpp.obj' if kind=='controls' else 'native_main.cpp.obj')]
                J.need(len(candidates)==1,'Compiled boundary TU identified uniquely');obj=J.pin(candidates[0])
                args=[str(tool),'-dr','--demangle','--x86-asm-syntax=intel',str(obj)];result=subprocess.run(args,capture_output=True,timeout=30);J.need(result.returncode==0,'Read-only exact COFF disassembly')
                log=out/f'{kind}-{level}-coff.txt';log.write_bytes(result.stdout);J.pin(log);text=result.stdout.decode()
                wrapper=function(text,'Context::invoke_selected_table(');body=function(text,'Context::invoke_selected_body(')
                J.need('__chkstk' not in wrapper and '__chkstk' in body[:2500],'Large body probe is outside the small wrapper')
                if level=='O2':
                    J.need(wrapper.index('fxsave64')<wrapper.index('fnstenv')<wrapper.index('fninit')<wrapper.index('?invoke_selected_body@'),'Inlined raw capture before large private body')
                    J.need(wrapper.index('?invoke_selected_body@')<wrapper.index('fxrstor64')<wrapper.index('fldenv'),'Raw FX then complete legacy ENV restored after contained private body')
                    tail=wrapper[wrapper.index('fldenv'):];J.need('call' not in tail and '\tret' in tail,'Restoration followed only by ABI epilogue and status return')
                    match=re.search(r'sub\s+rsp, (0x[0-9a-f]+)',wrapper);frame=int(match[1],16);J.need(frame<4096,'Small direct allocation with no probe helper')
                else:
                    ctor='??0NumericHostBoundary@';dtor='??1NumericHostBoundary@';private='?invoke_selected_body@'
                    J.need(wrapper.index(ctor)<wrapper.index(private)<wrapper.index(dtor),'Out-of-line constructor/body/destructor ownership order')
                    construct=function(text,'NumericHostBoundary::NumericHostBoundary(');destroy=function(text,'NumericHostBoundary::~NumericHostBoundary(')
                    J.need(construct.index('fxsave64')<construct.index('fnstenv')<construct.index('fninit'),'O0 literal numerical/legacy capture order')
                    J.need(destroy.index('fxrstor64')<destroy.index('fldenv') and 'call' not in destroy[destroy.index('fldenv'):],'O0 final rawFX then legacyENV restoration with no later helper call')
                    frame=None
                rows.append(dict(kind=kind,level=level,object=str(obj),object_sha256=J.sha(obj),COFF_log=str(log),wrapper_frame_bytes_O2=frame,private_probe_after_wrapper_capture=True,return_unwind='private body noexcept with original internal catches; wrapper status returns after FP restoration'))
        old=J.pin(J.BASE/'controls-capture-r1/report.json');failure=json.loads(old.read_text());J.need(not failure['passed'],'Original failed O2 receipt retained, not overwritten')
        report=dict(passed=True,gate_judgment='Accept the bounded selected27 persistent original/native research gate',connected_count=27,table_slots_total=145,unaccepted_other_slots=118,receipts=receipts,binary_audits=rows,
                    actual_original_phases=1296,actual_native_phases=2592,actual_native_sequences=96,complete_State_bytes=3504,complete_pages=14,source_events_checked=35712,Runtime_root_routes_checked=2784,actual_provider_checkpoints=48,compiled_fault_scenarios=102,direct_fault_and_retry_records=204,observer_corruption_denials=1944+3468+1632,
                    acceptance_reason='Actual persistent original CPU/FX/ENV/full pages equal repaired native O0/O2 source-predicted whole State/events/routes; literal original provider-return checkpoint bridges both native builds; exact causal terminal faults, owner cleanup and immutable corrected retries close the bounded research failure contract.',
                    failure_semantics_limit='Entered failed State is captured coherently and retained on refusal. Entire causal page prefixes, route completed flags, first-fault POD and event extent are checked. Full entered partial-State semantic equivalence and literal partial per-access event values are not claimed.',
                    host_boundary='Actual complete outside-return numerical/raw80/MXCSR/full ENV28 pass on positive/fault/refusal calls. COFF proves large-body __chkstk is inside the already-owned small public boundary. Volatile SIMD and reservedFX bytes do not receive equality credit.',
                    old_O2_failure='Exact frozen O2 control loss remains preserved. Probe/code/stack-layout cause is an inference; exact old failing kind/path was not reproduced or localized.',
                    explicit_projections={'original_IAT':{'address':J.IAT,'original_provider_leaf':J.LEAF,'native_raw_file_DWORD':1963420,'bytes':4},'FX_metadata':'RawFX pointer metadata and supported-mask transport are declared; separateENV is complete in direct primary. Debugger metadata never used as legacyENV oracle.','breakpoint_EIP':'CC at4C1A09 observes4C1A0A; checkpoint source/nativePC4C1A09','AF':'Only source-undefined XOR AF excluded after first XOR; every defined flag retained'},
                    exclusions=['Original software State and access events are unobserved','Other118 initializer slots and whole init-term dispatcher unproved','FDIV→entry composition is a separate bounded gate; not connected into this selected27 table run','Full CRT, complete entry/startup, SEH exception dispatch, ordinary full-game launch and arbitrary FP domains remain open'],ordinary_game_launched=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');J.pin(__file__)
        for p in out.iterdir():
            if p.is_file():J.pin(p)
        (out/'pins.json').write_text(json.dumps(dict(files=J.PINS),indent=2)+'\n');print(json.dumps(dict(passed=True,connected_count=27,report=str(out/'report.json'),corruption_denials=7044)))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);a=p.parse_args();main(a.output.resolve())
