"""Original-BEFORE source model with explicitly hypothetical API responses."""
import json
from pathlib import Path
import struct
import sys
import time
sys.dont_write_bytecode=True
from consumer import F,M
from before import expected,STACK_PAGE,COLD_PAGE
from prefix import predict,source_material,prior,QUERY_POINTER,QUERY_BYTES
ROOT=F.ROOT
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle
from manifests import verify_manifest
from paths import publish_bytes,workspace_path


def response_for(entry,program,bool_word=1,platform=2,major=6):
    query=prior.predict(entry,program,0x48450001)
    before=bytes(query['memory'][0x20001000][0x7b8:0x7b8+QUERY_BYTES])
    after=bytearray(before)
    struct.pack_into('<I',after,4,major);struct.pack_into('<I',after,16,platform)
    return dict(input=before,output=bytes(after),result=bool_word)


def main(directory):
    started=time.perf_counter_ns();out=workspace_path(directory,reports=True)
    if out.exists() or out.parent!=ROOT/'reports/m4-crt-heap-version-root':
        raise ValueError('Fresh draft output')
    out.mkdir()
    for name in ('consumer.py','before.py','prefix.py','draft.py'):
        F.pin(Path(__file__).with_name(name))
    accepted=F.pin(ROOT/'reports/m4-crt-heap-mode-root/root-acceptance-r1/report.json',
        'fccb8400f1c4a5b8ee3824684d763d1a6391d9322ad28c0a5b173ef8bf483154')
    admission=json.loads(accepted.read_bytes())
    previous=json.loads(F.pin(admission['receipts']['author_execution']['path'],
                            admission['receipts']['author_execution']['sha256']).read_bytes())
    program,providers,maths,ctrl,init,args,argv,source,commands=M.source_material(out)
    heap_program,pages,heap_commands=source_material(out);source.update(pages)
    wp,pp,gp=M.R.source_material()
    original=F.pin(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin',F.ORIGINAL_SHA)
    payloads=[M.R.project(v) for v in M.R.originals(original.read_bytes())[:24]]
    rows,controls,stack_controls=[],[],[]
    for level in ('O0','O2'):
        identity=previous['levels'][level]
        with CaptureBundle(F.pin(identity['bundle'],identity['bundle_sha256']),identity['bundle_sha256']) as reader:
            root=F.LogicalPath(reader,'root')
            for index,payload in enumerate(payloads):
                row=F.LogicalPath(reader,f'row-{index}',root.inventory)
                entry,earlier=expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,args,argv,source,level)
                derived=predict(entry,heap_program,0x48450001,response_for(entry,heap_program))
                F.require(len(earlier)==20 and len(derived['phases'])==18 and
                          len([n for n in derived['phases']['heap-create-before'] if n.startswith('page-')])==21,
                          '21 mappings,20 prior and18 heap/version model phases;40 anticipated terminal phases')
                F.require(derived['selector_returned'] and derived['terminal_EIP']==0x780039e8 and
                          derived['terminal_ESP']==0x20001858 and derived['selector_result']==1,
                          'Genuine selector RET before unadmitted caller publication')
                F.require(derived['query_return_access']==(0x78003a2b,0x20000618,0x78003a31,4,0)
                          and len(derived['query_output_accesses'])==37,'Separate original API-return read and37 declared DWORD transport stores')
                F.require(bytes(entry.mem[STACK_PAGE])==bytes(4096) and derived['memory'][COLD_PAGE]==entry.mem[COLD_PAGE],
                          'Declared owned lower input and immutable additional raw code page')
                rows.append(dict(level=level,index=index,source_PCs=len(derived['PCs']),
                    source_accesses=len(derived['accesses']),source_CALLs=len(derived['routes']),source_RETs=2,
                    API_return_reads=2,API_transport_DWORDs=37,terminal_EIP=derived['terminal_EIP'],
                    terminal_ESP=derived['terminal_ESP'],expected_source_accesses=derived['accesses'],
                    expected_API_output_accesses=derived['query_output_accesses'],AF_sites=derived['undefined']))
                if index==0:
                    for bool_word,platform,major in ((0,2,6),(1,1,6),(1,2,4),(1,2,5),(1,2,6),(0xffffffff,2,0xffffffff)):
                        value=predict(entry,heap_program,0x48450001,response_for(entry,heap_program,bool_word,platform,major))
                        good=bool_word!=0 and platform==2 and major>=5
                        F.require(value['selector_returned']==good and value['environment_reached']==(not good),
                                  'Source decisions follow finite declared response, never fabricated native witness')
                        controls.append(dict(level=level,hypothetical_BOOL=bool_word,hypothetical_platform=platform,
                            hypothetical_major=major,selector_returned=good,source_PCs=len(value['PCs']),
                            source_accesses=len(value['accesses']),native_or_API_executed=False))
                    for value in (0,0xffffffff,8,0x40,0x1848,0x80000000):
                        alternate,_=expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,args,argv,
                            source,level,struct.pack('<I',value)*1024)
                        derived=predict(alternate,heap_program,0x48450001,response_for(alternate,heap_program))
                        F.require(derived['selector_returned'] and len(derived['undefined'])==5,'Declared lower input preserved through source selector return')
                        stack_controls.append(dict(level=level,initial_lower_stack_DWORD=value,native_or_API_executed=False))
    for module in (M,M.M,M.M.M,M.M.M.M,M.D,M.R,M.N,M.D.E,M.F,M.C):
        for path,digest in module.PINS.items(): F.pin(path,digest)
    for path in out.iterdir():
        if path.is_file(): F.pin(path)
    closure=verify_manifest(F.PHYSICAL)
    report=dict(passed=True,scope='Original-BEFORE plus declared lower input and explicitly hypothetical complete version response; source-only draft',
        rows=rows,ordinary_BEFORE_models=48,hypothetical_response_formula_controls=controls,
        declared_stack_formula_controls=stack_controls,source_PCs=51,source_accesses=31,actual_source_CALLs=5,
        genuine_source_RETs=2,separate_API_return_reads=2,separate_API_transport_DWORDs=37,
        host_source_execution_stores=0,mappings=21,prior_mappings_preserved=20,new_raw_RX_page=COLD_PAGE,
        lower_stack_bytes_original_observed=False,original_stack_guard_growth_proved=False,TIB_and_Policy_changed=False,
        new_compiled_source_bytes=60,reused_heap_source_bytes=84,reused_selector_probe_source_bytes=86,
        executed_source_bytes=169,total_source_identity_bytes=2086,
        undefined_AF_universal_equivalence=False,current_native_compared=False,native_executed=False,
        HeapCreate_executed=False,GetVersionExA_executed=False,hypothetical_API_response_is_native_witness=False,
        selector_return_modelled=True,heap_mode_published=False,heap_initialized=False,heap_initializer_RET=False,
        original_attach_proved=False,whole_M4_complete=False,source_commands=commands+heap_commands,
        files=F.PHYSICAL,physical_closure=closure,seconds=(time.perf_counter_ns()-started)/1e9)
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','rows','source_commands','hypothetical_response_formula_controls','declared_stack_formula_controls')}))


if __name__=='__main__': main(*sys.argv[1:])
