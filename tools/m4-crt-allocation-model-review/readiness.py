"""Static readiness of the independent NULL-free and external protocol model."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys
sys.dont_write_bytecode=True
import predict
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from paths import publish_bytes,workspace_path
from manifests import normalized,verify_manifest,unique_object
REPORT_SHA='5ea56445e5367a421a28251f5e097b72f0d8370cf232a2fb4734b6698f14c2c6'
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main(name):
    out=workspace_path(ROOT/'reports/m4-crt-allocation-model-review'/name,reports=True)
    predict.need(re.fullmatch('readiness-r[1-9][0-9]*',name) and not out.exists(),'Fresh static-only readiness output')
    files={}
    def add(path,digest=None):
        path=Path(path).absolute();actual=sha(path)
        predict.need(digest is None or actual==digest,'Pinned readiness source identity')
        files[normalized(str(path))]=actual;return path
    receipt=add(ROOT/'reports/m4-crt-allocation-recovery/recovery-r1/report.json',REPORT_SHA)
    source=json.loads(receipt.read_bytes(),object_pairs_hook=unique_object)
    predict.need(source['passed'],'Frozen exact original source recovery')
    for path in (Path(__file__),Path(predict.__file__),predict.MODEL_PATH,Path(__file__).with_name('README.md'),Path(sys.executable),
                 ROOT/'tools/m4-pipeline/paths.py',ROOT/'tools/m4-pipeline/manifests.py'):
        add(path)
    loader=add(ROOT/'tools/m4-crt/recover_provider.py');provider=add(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',PROVIDER_SHA)
    spec=importlib.util.spec_from_file_location('allocation_readiness_PE',loader)
    pe_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe_module)
    pe=pe_module.PE(provider,PROVIDER_SHA)
    instructions={row['pc']:row for span in source['spans'].values() for row in span['instructions']}
    for pc,row in instructions.items():
        predict.need(pe.read(pc-pe.base,row['width']).hex()==row['bytes_hex'],'Fresh source bytes agree at every recovered instruction')
    initial=verify_manifest(files);checks=0;rows=[]
    for previous in (0,0xffffffff,0x20001900,0x7ffdf123,8,0x80000000):
        for DF in (0,1):
            state=bytearray((i*13+7)&255 for i in range(3504));fx=bytes((i*7+3)&255 for i in range(512));cpu=bytes((i*11+1)&255 for i in range(40))
            regs=dict(eax=0x13579bdf,ecx=0x2468abcd,edx=0xabcdef01,ebx=0xabcdef12,esp=0x20001858,ebp=0x20001970,esi=0x01234567,edi=0x89abcdef)
            for key,number in regs.items():struct.pack_into('<I',state,predict.source.REG[key],number)
            for offset in (2120,2184):struct.pack_into('<I',state,offset,0)
            TIB=0x7ffde000;struct.pack_into('<I',state,predict.source.FSBASE,TIB);struct.pack_into('<I',state,2472,0x78001390)
            state[predict.source.FLAGS['DF']]=DF
            memory={0x20001000:bytearray((i*17+5)&255 for i in range(4096)),TIB:bytearray(struct.pack('<I',previous))}
            struct.pack_into('<2I',memory[0x20001000],0x858,predict.FREE_MARKER,0)
            value=predict.free_null(dict(state=state,fx=fx,cpu=cpu,memory=memory))
            expected=(0x78001390,0x78001391,0x78001393,0x78001395,0x7800139a,0x7800139f,0x780013a5,0x780013a6,
                      0x780013ad,0x780013b0,0x780013b1,0x780013b2,0x780013b3,0x780013b6,0x780013b8,
                      0x78001416,0x78001419,0x78001420,0x78001421,0x78001422,0x78001423,0x78001424)
            predict.need(tuple(value['PCs'])==expected,'NULL branch exact22 authentic instruction identities');checks+=1
            predict.need(instructions[0x780013b8]['mnemonic']=='je' and '78001416' in instructions[0x780013b8]['operands'],
                         'Original pointer TEST/JZ selects normal epilogue');checks+=1
            predict.need(sum(instructions[pc]['width'] for pc in expected)==57,'NULL branch57 executed source bytes');checks+=1
            for offset in range(3504):
                modified={2472,2473,2474,2475,*range(predict.source.REG['eax'],predict.source.REG['eax']+4),
                          *range(predict.source.REG['ecx'],predict.source.REG['ecx']+4),*range(predict.source.REG['esp'],predict.source.REG['esp']+4),
                          *(predict.source.FLAGS[k] for k in ('CF','PF','AF','ZF','SF','OF'))}
                if offset not in modified:predict.need(value['state'][offset]==state[offset],'All unrelated State bytes carried');checks+=1
            predict.need(value['fx']==fx and value['cpu']==cpu,'Complete FX/CPU carried');checks+=1
            predict.need(struct.unpack('<I',value['memory'][TIB])[0]==previous,'Same source previous FS chain restored');checks+=1
            predict.need([a for a in value['accesses'] if a[1]==TIB]==[(0x7800139f,TIB,previous,4,0),(0x780013a6,TIB,0x20001844,4,1),(0x78001419,TIB,previous,4,1)],
                         'Normal FS read/install/remove chronology');checks+=1
            predict.need(value['state'][predict.source.FLAGS['DF']]==DF and
                         {k:value['state'][off] for k,off in predict.source.FLAGS.items() if k!='DF'}==dict(CF=0,PF=1,AF=0,ZF=1,SF=0,OF=0),
                         'NULL TEST final defined flags and scoped AF representative');checks+=1
            rows.append(dict(previous_FS0=previous,DF=DF,source_PCs=22,source_accesses=18,source_bytes=57,HeapFree_calls=0,
                             genuine_RETs=1,EAX=previous,public_return_type='void'))
    # External effects are separately typed, including the exact write order.
    base=dict(state=bytes(state),fx=fx,cpu=cpu,memory=memory);raw=bytearray(base['state'])
    struct.pack_into('<I',raw,predict.source.REG['esp'],0x20001860);struct.pack_into('<I',raw,2472,0x7800184c);base['state']=bytes(raw)
    writes,projections=[],[];external=predict.external_call(base,0x780012b3,24,predict.MALLOC_MARKER,writes,projections)
    predict.need(writes==[(0x780012b3,0x2000185c,24,4,1),(0x780012b3,0x20001858,predict.MALLOC_MARKER,4,1)] and
                 projections==[(1,0x7800184c,0x20001860,0x780012b3,0x20001858,24,0x20001858,predict.MALLOC_MARKER)],
                 'Research ABI separate argument/return stores followed by EIP/ESP-only projection');checks+=1
    final=verify_manifest(files);predict.need(initial['passed'] and final['passed'] and
        initial['unique_physical_dependencies']==final['unique_physical_dependencies']==len(files),'Readiness immutable physical inputs')
    out.mkdir(parents=True)
    pins=dict(schema='mw34-m4-allocation-model-review-pins-v1',files=files,physical_files=len(files))
    publish_bytes(out/'pins.json',(json.dumps(pins,sort_keys=True,indent=2)+'\n').encode())
    report=dict(schema='mw34-m4-allocation-model-readiness-v1',passed=True,checks=checks,
        frozen_source_report_sha256=REPORT_SHA,frozen_affine_model_sha256=predict.MODEL_SHA,predictor_sha256=sha(predict.__file__),
        NULL_free_static_controls=rows,external_ABI_protocol_checked=True,full_unrelated_State_FX_CPU_preserved=True,
        source_native_or_API_executed=False,current_native_capture_credit=False,AFTER_machine_state_used_as_seed=False,
        original_API_internals_equivalence=False,normal_SEH_handler_dispatch_proved=False,
        actual_native_observer_pending=True,physical_dependencies=len(files),files=files,pins_sha256=sha(out/'pins.json'))
    publish_bytes(out/'report.json',(json.dumps(report,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,checks=checks,path=str(out/'report.json'),sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))


if __name__=='__main__':main(sys.argv[1])
