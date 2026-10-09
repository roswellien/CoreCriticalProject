"""Disjoint source-only allocation lifts; no candidate/native/API execution.

The component definitions exactly match the author's requested prepare.py
contract. Each literal original span is lifted independently; five overlapping
entry objects reuse63 already recovered bytes, with no extra guard identity.
"""
from concurrent.futures import ThreadPoolExecutor
import ctypes as c
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from paths import publish_bytes,workspace_path
from manifests import normalized,unique_object,verify_manifest
REC=ROOT/'reports/m4-crt-allocation-recovery/recovery-r1'
REC_SHA='5ea56445e5367a421a28251f5e097b72f0d8370cf232a2fb4734b6698f14c2c6'
COMPONENTS=(('caller','caller-cleanup'),('malloc','malloc-wrapper'),('size','malloc-size'),
 ('worker','malloc-worker-hot'),('round','malloc-round-mode1'),('null','malloc-null-cold'),
 ('free','free-hot'),('freecold','free-mode1-cold'))
OVERLAPPING=(('alloc_tail','malloc-worker-hot',0x78001377,16),
 ('worker_epilogue','malloc-worker-hot',0x78001367,15),
 ('free_tail','free-hot',0x78001428,16),('free_epilogue','free-hot',0x78001416,15),
 ('size_ret','malloc-size',0x780012e2,1))
BRIDGES={'__remill_read_memory_32','__remill_write_memory_32','__remill_write_memory_8',
         '__remill_read_memory_8','__remill_function_call','__remill_function_return',
         '__remill_jump','__remill_missing_block'}


def need(ok,why):
    if not ok:raise ValueError(why)


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):return json.loads(Path(path).read_bytes(),object_pairs_hook=unique_object)


def main(name):
    started=time.perf_counter_ns();out=workspace_path(ROOT/'reports/m4-crt-allocation'/name,reports=True)
    need(re.fullmatch('lifts-r[1-9][0-9]*',name) and not out.exists(),'Fresh disjoint source-only lift output')
    files={}
    def add(path,digest=None):
        path=Path(path).absolute();value=sha(path);key=normalized(str(path))
        need(digest is None or digest==value,'Exact pinned source/build dependency '+str(path))
        need(key not in files or files[key]==value,'Unique physical lift dependency');files[key]=value;return path
    report_path=add(REC/'report.json',REC_SHA);recovery=read(report_path)
    need(recovery['passed'] and recovery['schema']=='mw34-m4-allocation-static-recovery-v1','Exact sealed original source recovery')
    add(REC/'pins.json','24224098e60ecb8dff2bd60526fe64766bad3cfad49db2914204d106cc941c03')
    for path,digest in read(REC/'pins.json')['files'].items():add(path,digest)
    llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    lifter=add(ROOT/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe')
    sem=add(ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc',
        '618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca')
    dll=add(llvm/'LLVM-C.dll','34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb')
    for path in (llvm/'clang.exe',llvm/'llvm-nm.exe',Path(__file__),Path(sys.executable),
                 ROOT/'tools/lifting/host_adapter.py',ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):
        add(path)
    lower_path=add(ROOT/'tools/m4-crt-mainargs-recovery/recover.py')
    upstream_path=add(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp')
    lower_source=lower_path.read_text();body=lower_source[lower_source.index('def lower('):lower_source.index("if __name__ == '__main__':")]
    body=body.replace('mw34_mainargs_','mw34_allocation_').replace("and '__remill_missing_block' not in text",'')
    need('def lower(' in body and "mw34_mainargs_" not in body,'Exact namespace-only lowering plus admitted missing-block bridge')
    sys.path.insert(0,str(ROOT/'tools/lifting'))
    from host_adapter import LLVM,HOST_LAYOUT,FUNCTION_INDEX,checked_state_offsets
    namespace=dict(c=c,re=re,sha=sha,LLVM=LLVM,HOST_LAYOUT=HOST_LAYOUT,FUNCTION_INDEX=FUNCTION_INDEX,
        checked_state_offsets=checked_state_offsets,need=need,BRIDGES=BRIDGES)
    exec(compile(body,str(lower_path),'exec'),namespace)
    upstream=upstream_path.read_text();inputs=[]
    for component,label in COMPONENTS:
        info=recovery['spans'][label];path=add(REC/(label+'.bin'),info['sha256'])
        inputs.append((component,label,info['start'],path.read_bytes(),False))
    for component,label,entry,n in OVERLAPPING:
        info=recovery['spans'][label];raw=(REC/(label+'.bin')).read_bytes();offset=entry-info['start']
        need(0<=offset and offset+n<=len(raw) and any(row['pc']==entry for row in info['instructions']) and
             any(row['pc']+row['width']==entry+n for row in info['instructions']),'Exact original overlapping whole-instruction extent')
        inputs.append((component,label,entry,raw[offset:offset+n],True))
    need(len(inputs)==13 and sum(len(code) for _,_,_,code,_ in inputs)==532,'Thirteen literal bodies/532 compiled bytes')
    initial=verify_manifest(files);out.mkdir(parents=True);commands=[]
    try:
        def component_lift(item):
            component,label,entry,code,overlap=item;local_commands=[]
            publish_bytes(out/(component+'-source.bin'),code)
            def run(program,args,command_label):
                argv=[str(program),*map(str,args)];t=time.perf_counter_ns()
                try:cp=subprocess.run(argv,capture_output=True,timeout=120,creationflags=0x08000000)
                except subprocess.TimeoutExpired as error:
                    publish_bytes(out/(command_label+'.stdout'),error.stdout or b'')
                    publish_bytes(out/(command_label+'.stderr'),error.stderr or b'')
                    local_commands.append(dict(label=command_label,argv=argv,exit_code=None,timed_out=True,timeout_seconds=120))
                    publish_bytes(out/(component+'-failed-commands.json'),(json.dumps(local_commands,indent=2)+'\n').encode());raise
                publish_bytes(out/(command_label+'.stdout'),cp.stdout);publish_bytes(out/(command_label+'.stderr'),cp.stderr)
                local_commands.append(dict(label=command_label,argv=argv,exit_code=cp.returncode,timed_out=False,
                    seconds=(time.perf_counter_ns()-t)/1e9))
                need(cp.returncode==0,'Exact source-only tool failed '+command_label);return cp.stdout
            run(lifter,['--arch=x86','--os=windows','--address='+str(entry),'--entry_address='+str(entry),
                '--bytes='+code.hex(),'--semantics_dir='+str(sem.parent),'--ir_out='+str(out/(component+'-guest.ll'))],component+'-lift')
            text=(out/(component+'-guest.ll')).read_text()
            calls=[dict(kind='direct',target=int(address,16)) for address in re.findall(r'^declare ptr @sub_([0-9a-f]+)',text,re.M)]
            native=namespace['lower'](out,component,dict(entry=entry,outgoing_calls=calls),dll,upstream,run,llvm)
            actual_undefined={}
            for level in ('O0','O2'):
                raw=(out/(component+'-undefined-'+level+'.stdout')).read_text()
                symbols=re.findall(r'^\s*U\s+(\S+)\s*$',raw,re.M)
                need(all(symbol in native['bridges'] for symbol in symbols),'Every compiled undefined symbol is an admitted source bridge')
                actual_undefined[level]=symbols
            native.update(entry=entry,source_label=label,source_bytes=len(code),source_sha256=sha(out/(component+'-source.bin')),
                original_guard_identity_reused=overlap,direct_source_targets=calls,actual_undefined_symbols=actual_undefined)
            print(json.dumps(dict(component=component,compiled_objects=2,source_bytes=len(code))),flush=True)
            return component,native,local_commands
        # Independent literal functions/LLVM contexts; each owns unique outputs.
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(component_lift,inputs))
        native={component:value for component,value,_ in results}
        for _,_,rows in results:commands.extend(rows)
        verify_manifest(files)
        objects={path:info['sha256'] for value in native.values() for info in value['objects'].values() for path in (info['path'],)}
        need(len(objects)==26,'All actual26COFF outputs')
        for path in out.iterdir():
            if path.is_file():add(path)
        physical=verify_manifest(files)
        report=dict(schema='mw34-m4-allocation-source-lifts-v1',passed=True,
            scope='Exact original source/ABI/COFF preparation only; no native candidate or API execution',
            source_bodies=native,new_guest_objects=26,new_compiled_source_bytes=532,new_unique_source_identity_bytes=469,
            overlapping_compiled_source_bytes=63,components=[dict(component=a,source_label=b) for a,b in COMPONENTS],
            overlapping_entries=[dict(component=a,source_label=b,entry=e,bytes=n) for a,b,e,n in OVERLAPPING],
            State_bytes=3504,State_alignment=8,FX_bytes=512,CPU_bytes=40,checked_layouts_per_body=34,
            exact_literal_lifts=13,lowering_namespace_change_only=True,missing_block_bridge_admitted=True,
            commands=commands,entry_objects=objects,files=files,recovery_sha256=REC_SHA,
            native_component_executed=False,original_executed=False,actual_API_executed=False,
            whole_M4_complete=False,independent_compiled_review_credit=False,
            physical_closure=physical,seconds=(time.perf_counter_ns()-started)/1e9)
        publish_bytes(out/'report.json',(json.dumps(report,sort_keys=True,indent=2)+'\n').encode());add(out/'report.json')
        publish_bytes(out/'pins.json',(json.dumps(dict(schema='mw34-m4-allocation-lift-pins-v1',files=files),sort_keys=True,indent=2)+'\n').encode())
        print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),objects=26)))
    except Exception:
        publish_bytes(out/'failure.txt',traceback.format_exc().encode());raise


if __name__=='__main__':main(sys.argv[1])
