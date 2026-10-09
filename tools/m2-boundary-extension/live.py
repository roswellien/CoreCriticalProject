"""Exercise the actual timer provider through each worker's selected guest bridge."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
from build import OUT, sha
from compare import CODE, STACK, HEADER, REQ, RES_SIZE, MASK, read_results, expected, validate_build

def cases():
    result=[]
    for i,argument in enumerate((0,1,0x7fffffff,0x80000000,0xffffffff,0xa5a5f00c,0xa5a5f00d,0xa5a5f00e)):
        regs=[(0x12345678*(j+1)+i*0x10203)&MASK for j in range(8)]
        regs[4]=STACK+65+i*31  # Deliberately exercise unaligned frames.
        result.append(tuple(regs+[0x202,CODE,argument,(0x76543210+i)&MASK,0,i&1,0x10203040+i]))
    return result

def verify(qs,path,bits,metadata,shim_rva=None):
    if metadata.get('provider')!='WINMM.timeGetTime' or metadata.get('pointer_bits')!=bits or any(metadata.get(key)!=8 for key in ('live_context_cases','provider_calls','bridge_calls')):
        raise ValueError('Actual live provider/bridge declaration changed')
    target=metadata['guest_iat_target']
    if bits==64 and target!=CODE+0x300 or bits==32 and not (target==metadata['executable_base']+metadata['shim_rva'] and 0<metadata['shim_rva']<metadata['image_size'] and target<=MASK):
        raise ValueError('Unadmitted live IAT target')
    if bits==32 and (shim_rva is None or metadata['shim_rva']!=shim_rva):
        raise ValueError('Original live shim differs from the linked executable')
    module=Path(metadata['module_path'])
    if module.name.lower()!='winmm.dll' or not module.is_file():raise ValueError('Live Winmm provider missing')
    dll=module.read_bytes();pe=struct.unpack_from('<I',dll,0x3c)[0]
    if dll[pe:pe+4]!=b'PE\0\0' or struct.unpack_from('<H',dll,pe+4)[0]!=(0x14c if bits==32 else 0x8664):raise ValueError('Live provider architecture mismatch')
    ticks=[]
    for i,(q,actual) in enumerate(zip(qs,read_results(path,len(qs),bits),strict=True)):
        words=struct.unpack_from('<16I',actual)
        tick=words[15]
        if words[12:15]!=(4,1,1) or words[2]!=tick:
            raise ValueError('Provider result/counters were not consumed by compiled chain')
        want=expected(q,actual_timer=tick,iat_target=target)
        if actual!=want:
            offset=next(j for j,(a,b) in enumerate(zip(actual,want)) if a!=b)
            raise ValueError(f'Live case{i} byte{offset} differs from full ABI/page oracle')
        ticks.append(tick)
    deltas=[(b-a)&MASK for a,b in zip(ticks,ticks[1:])]
    if any(not (0<delta<=10000) for delta in deltas):raise ValueError('Actual provider DWORD clock did not progress')
    return {'cases':len(qs),'provider_calls':len(qs),'bridge_calls':len(qs),'ticks':ticks,
            'unsigned_delta_ms':deltas,'provider_module':{'path':str(module),'sha256':sha(module)},
            'guest_iat_target':target,'pointer_bits':bits,'zero_mismatches':True}

def run(replay=False):
    build=validate_build();qs=cases();request=OUT/'live-requests.bin'
    encoded=HEADER.pack(b'MW34BEXQ',1,8,REQ.size,32)+b''.join(REQ.pack(*q) for q in qs)
    if replay:
        if request.read_bytes()!=encoded:raise ValueError('Saved live requests changed')
    else:request.write_bytes(encoded)
    workers={}
    for kind,worker in build['workers'].items():
        path=OUT/f'live-results-{kind}.bin';meta_path=OUT/f'live-worker-{kind}.json'
        if not replay:
            child=subprocess.run([worker['path'],'--live-timer',str(request),str(path),str(OUT/'calls.bin')],capture_output=True,text=True,check=True)
            meta=json.loads(child.stdout);meta_path.write_text(json.dumps(meta,indent=2)+'\n')
        meta=json.loads(meta_path.read_text())
        observation=verify(qs,path,32 if kind=='reference' else 64,meta,build['original_shim_rva'])
        observation.update({'worker_sha256':worker['sha256'],'results_sha256':sha(path),'metadata_sha256':sha(meta_path)})
        workers[kind]=observation
    report={'schema_version':1,'status':'passed','scope':'actual live provider through full selected bridge/guest context; no cross-process tick equality claim',
            'original_cases':8,'native_cases':16,'build_sha256':sha(OUT/'build.json'),'requests_sha256':sha(request),
            'oracle_sha256':sha(Path(__file__)),'workers':workers,'zero_mismatches':True}
    destination=OUT/('live-replay.json' if replay else 'live-comparison.json')
    destination.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--replay',action='store_true');run(parser.parse_args().replay)
