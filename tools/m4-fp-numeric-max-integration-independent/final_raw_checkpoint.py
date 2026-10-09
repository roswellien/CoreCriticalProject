"""Bind root raw/source reviews to the final compiler-emitted schema and r9."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PINS={}

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def pin(p,want=None):
    p=Path(p).resolve();h=sha(p);assert want is None or h==want,str(p)
    assert str(p) not in PINS or PINS[str(p)]==h
    PINS[str(p)]=h;return p

def main():
    base=ROOT/'reports/m4-fp-numeric-max-integration';out=base/'independent-final-raw-checkpoint-r1';assert not out.exists()
    build=base/'native-build-r5'
    report=json.loads(pin(build/'build.json','ad8c4b5f2e869da3fe664dc835ef59e529a156e95e3917da3ea170aab092a9cc').read_text());assert report['passed'] and not report['shared_runtime_modified'] and not report['whole_M4_complete']
    stages=[('independent-static-final-r1','045db0ffc9858cc7065c8de99450b5a9ba6f7cf3405ea262958c4181bc41ebd9','1fb54e7c9af7b6790e9dc6364c2fd2ef6dec49cf8bad1462413f9970ae722073'),('independent-persistent-final-r1','3da689a13b6ac5ee5de8e286360905eba7a8d25fb9f06325bc7264f9865aa405','3fb6e87c2d13956d0747f92afb14fc5968b3c4d22b9133b0cc0676afcdd1a409'),('independent-replay-final-r1','c90583f3f7f6b261763c1463283f5f1178d4801a01e899993d339e1bc0604094','b9b5c99a584b3b0b1e931290a6605c7b471af279b6bbf27677cc07fb4aa64ba4')]
    for name,rh,ph in stages:
        r=json.loads(pin(base/name/'report.json',rh).read_text());assert r['passed'] and not r['whole_M4_complete']
        for p,h in json.loads(pin(base/name/'pins.json',ph).read_text())['files'].items():pin(p,h)
    offsets=dict(tag=0,sequence=40,phase=44,before=48,after=4132,checkpoint=8216,memory_before=12300,memory_after=28684,host_before=45068,host_after=45580,host_env_before=46092,host_env_after=46120,events=46148,routes=46588,counts=46648)
    state=dict(eax=2216,ecx=2248,edx=2264,ebx=2232,esp=2312,ebp=2328,esi=2280,edi=2296,eip=2472,rflags=2080,flags=[2065,2067,2069,2071,2073,2075,2077],fs_base=2168,st0=2486,x87=2768,sw_flags=[2755,2753,2751,2749,2747,2745,2757,2737,2739,2741,2743])
    for level in ('O0','O2'):
        schema=json.loads(pin(build/f'unit-{level}/schema.json','b2928912aad1dc48620a46ebc065b616feb6f813260ee84d739ca4aa64fcb2d8').read_text())
        assert schema['record_bytes']==46680 and schema['view_bytes']==4084 and schema['event_bytes']==20 and schema['CXX_State_bytes']==3504 and schema['CXX_State_alignment']==16 and schema['raw_offsets']==offsets and schema['State_offsets']==state
        for mode in ('default','directed'):
            assert json.loads(pin(build/f'replay-{mode}-{level}/schema.json').read_text())==schema
    pin(ROOT/'tools/m4-runtime/runtime.hpp','41ed0a20e4f87cba3838127d943126ff88b453c39212c2ecdfe028242b4f3536');pin(ROOT/'tools/m4-runtime/runtime.cpp','48865157011deaa151dccbb598da3f5a8ed16ea1944d048549f97f66f32308f7')
    text=(ROOT/'tools/m4-runtime/runtime.hpp').read_text();assert 'alignas(64)' in text
    for name in ('review-source.py','failure.txt'):pin(base/'independent-static-r1'/name)
    out.mkdir();(out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py');pin(Path(__file__))
    result=dict(passed=True,scope='Root source/raw/model/schema/current-r9 identity checkpoint; author build and independent compiled source/fault closure remain pending',stages=[dict(directory=n,report_sha256=h,pins_sha256=p) for n,h,p in stages],compiled_schema=dict(record=46680,view=4084,State_bytes=3504,CXX_alignment=16,LLVM_type_alignment=8,owned_Runtime_storage_alignment=64,all_offsets_verified=True),native_persistent_phases=864,native_State_carry_boundaries=432,native_paired_replays=14688,original_wrappers=7344,separate_paired_original_leaves=7344,observer_corruption_rejects=328,physical_bindings=len(PINS),current_r9_sources_unchanged=True,identity_scope='Exact current disk/post-build source associations, not full execution-time process dependency attestation',selected_joint_initializer_roots=26,remaining_outside_joint_gate=118,whole_M4_complete=False)
    rp=out/'report.json';rp.write_text(json.dumps(result,indent=2)+'\n');pin(rp)
    (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
    print(json.dumps(dict(passed=True,report_sha256=sha(rp),pins_sha256=sha(out/'pins.json'),bindings=len(PINS))))

if __name__=='__main__':main()
