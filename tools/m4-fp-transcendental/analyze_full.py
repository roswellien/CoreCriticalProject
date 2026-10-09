"""Additive exact seed/ordered-domain checks for the measured cosine gate."""
from pathlib import Path
import json
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import analyze_directed as directed
base=directed.base
CONTROLS=[0x007f,0x047f,0x087f,0x0c7f,0x027f,0x067f,0x0a7f,0x0e7f,0x037f,0x077f,0x0b7f,0x0f7f]

def initial_state(tag):
    fixture,entry,cw,top,_=tag
    seed=(fixture>>16)*3571+cw+(fixture&65535)*1709
    result=bytearray((position*29+seed+(position>>8)*7)&255 for position in range(3504))
    # Offsets from the pinned typed 34-structure layout, consumed by the
    # independently compiled initialization source. Opaque padding is retained.
    result[2112:2208]=bytes(96);result[2768:3280]=bytes(512)
    for position,value in [(2090,0x2b),(2106,0x2b),(2110,0x23)]:struct.pack_into('<H',result,position,value)
    for position,value in [(2216,0x13579bdf),(2248,0x2468ace0),(2264,0x81726354),(2232,0x10293847),
      (2312,0x20001800),(2328,0x92837465),(2280,0x56473829),(2296,0xaabbccdd),(2472,entry)]:
        struct.pack_into('<I',result,position,value)
    struct.pack_into('<Q',result,2080,0x202)
    for position in [2065,2067,2069,2071,2073,2075,2077,2737,2739,2741,2743,2745,2747,2749,2751,2753,2755,2757]:result[position]=0
    struct.pack_into('<HH',result,2768,cw,top<<11);struct.pack_into('<I',result,2792,0x1f80)
    for slot in range(8):
        result[2486+slot*16:2496+slot*16]=bytes(10)
        result[16+slot*64:32+slot*64]=bytes(16)
    return bytes(result)

def seed_issues(records):
    issues=[]
    for i,n in enumerate(records):
        expected=initial_state(n['tag'])
        if n['state0']!=expected:
            issues.append({'record':i,'field':'Complete State seed',
              'offsets':[j for j,(a,b) in enumerate(zip(expected,n['state0'])) if a!=b][:24]})
    return issues

def main():
    build,capture,previous,directory=map(lambda p:Path(p).resolve(),sys.argv[1:5])
    base.require(directory.is_relative_to(ROOT/'reports/m4-fp-transcendental') and not directory.exists(),'Fresh full comparison directory required')
    old=json.loads(previous.read_text());base.require(old['passed_observed_domain'],'Passing directed comparison required')
    pin_path=previous.parent/'pins.json';bindings=json.loads(pin_path.read_text())['files']
    for p,sha in bindings.items():base.require(base.digest(p)==sha,'Changed directed observation binding '+p)
    reference=directed.originals((capture.parent/'original.bin').read_bytes())
    keys=[((repeat<<16)|input_index,entry,cw,top) for repeat in range(2) for entry in base.ROOTS
      for input_index in range(32) for cw in CONTROLS for top in (0,7)]
    base.require(list(reference)==keys,'Exact original ordered corpus differs')
    for key,o in reference.items():
        cpu0=struct.pack('<10I',0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,0x202,key[1])
        cpu1=bytearray(cpu0);struct.pack_into('<I',cpu1,16,0x20001804);struct.pack_into('<I',cpu1,36,0x10000100)
        base.require(o['tag']==(*key,0) and o['cpu0']==cpu0 and o['cpu1']==cpu1,'Exact original CPU/return domain differs')
    repeats=0
    for key,o in reference.items():
        if key[0]>>16:continue
        other=reference[(key[0]|65536,*key[1:])]
        for field in ['cpu0','cpu1','fx0','fx1','env0','env1','mem0','mem1']:
            base.require(o[field]==other[field],'Original guest repeat changed '+field)
        repeats+=1
    comparisons={}
    for level in ('O0','O2'):
        records=list(directed.natives((build.parent/f'native-{level}.bin').read_bytes()))
        base.require([n['tag'][:4] for n in records]==keys,'Exact native ordered corpus differs')
        comparisons[level]={'records':len(records),'full_State_seed_bytes':len(records)*3504,
          'seed_issues':seed_issues(records)}
    fixed_reference=base.originals((ROOT/'reports/m4-fp-startup/run-r1/original.bin').read_bytes())
    fixed={level:base.check(base.natives((build.parent/f'native-fixed-{level}.bin').read_bytes()),fixed_reference) for level in ('O0','O2')}
    directory.mkdir(parents=True);report={'passed':all(not r['seed_issues'] for r in comparisons.values()) and
      all(not r['observed_mismatches'] for r in fixed.values()),'scope':'Additive exact full State seeds, directed order/repeats and default cosine comparison',
      'original_records':6144,'native_records':12288,'bitwise_original_guest_repeat_pairs':repeats,
      'directed_comparison':str(previous),'comparisons':comparisons,'default_comparisons':fixed,
      'full_State_after_model':True,'independent_review':False,'shared_Runtime_admitted':False}
    output=directory/'report.json';output.write_text(json.dumps(report,indent=2)+'\n')
    for p in [build,capture,previous,pin_path,Path(__file__).resolve(),Path(directed.__file__),Path(base.__file__),output]:bindings[str(p)]=base.digest(p)
    (directory/'pins.json').write_text(json.dumps({'files':bindings},indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'original':6144,'native':12288,'repeats':repeats,
      'seed_issues':{k:len(v['seed_issues']) for k,v in comparisons.items()},'default_mismatches':{k:v['observed_mismatches'] for k,v in fixed.items()}}))

if __name__=='__main__':main()
