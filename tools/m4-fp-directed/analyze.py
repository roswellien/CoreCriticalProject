"""Retain complete directed original/native mismatches, without narrowing scope."""
from pathlib import Path
import importlib.util
import json
import re
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tools/m4-fp-native/analyze_first.py'
spec=importlib.util.spec_from_file_location('first_observation',BASE);first=importlib.util.module_from_spec(spec);spec.loader.exec_module(first)
digest,require=first.digest,first.require
def parse_native(data):
    require(len(data)==32+2016*83088 and data[:8]==b'MW4FPN01' and struct.unpack_from('<6I',data,8)==(1,2016,83088,3504,9,4096),'Directed native extent/header differs')
    spans={'cpu0':(20,60),'cpu1':(60,100),'state0':(100,3604),'state1':(3604,7108),
           'fx0':(7108,7620),'fx1':(7620,8132),'env0':(8132,8160),'env1':(8160,8188),
           'host0':(8188,8700),'host1':(8700,9212),'henv0':(9212,9240),'henv1':(9240,9268),
           'mem0':(9268,46132),'mem1':(46132,82996)}
    for offset in range(32,len(data),83088):
        r=data[offset:offset+83088];result={key:r[a:b] for key,(a,b) in spans.items()}
        result.update(tag=struct.unpack_from('<5I',r),counts=struct.unpack_from('<7I',r,82996),events=[struct.unpack_from('<4I',r,83024+i*16) for i in range(4)])
        yield result
def parse_original(data,inputs,pack):
    require(len(data)==24+2016*75988 and data[:8]==b'MW4FPO01' and struct.unpack_from('<4I',data,8)==(1,2016,9,4096),'Directed original extent/header differs')
    reference={};expected_keys={(rep<<16|i,0x4133c0,cw,top) for rep in (0,1) for i in range(42) for cw in (0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f) for top in (0,7)}
    spans={'cpu0':(20,60),'cpu1':(60,100),'fx0':(100,612),'fx1':(612,1124),'env0':(2148,2176),'env1':(2176,2204),'mem0':(2260,39124),'mem1':(39124,75988)}
    initial=bytearray(b''.join(pack[12+i*4104+8:12+i*4104+4104] for i in range(6,15)))
    struct.pack_into('<I',initial,8*4096+0x800,0x10000100)
    cpu=[0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,0x202,0x4133c0]
    for offset in range(24,len(data),75988):
        r=data[offset:offset+75988];tag=struct.unpack_from('<5I',r);key=tag[:4]
        require(key in expected_keys and key not in reference and tag[4]==0,'Directed original domain/status differs')
        result={key:r[a:b] for key,(a,b) in spans.items()};result['tag']=tag
        wanted=bytearray(initial);struct.pack_into('<I',wanted,4*4096+0xf58,inputs[tag[0]&0xffff])
        require(result['mem0']==wanted,'Original controlled input/full-page before differs')
        changed=[i for i,(a,b) in enumerate(zip(result['mem0'],result['mem1'])) if a!=b]
        require(all(6*4096+0xe40<=i<6*4096+0xe44 for i in changed),'Original wrote outside the reviewed store')
        require(result['cpu0']==struct.pack('<10I',*cpu),'Original input CPU differs');after=list(cpu);after[4]+=4;after[9]=0x10000100
        require(result['cpu1']==struct.pack('<10I',*after),'Original return/CPU differs')
        # FXSAVE hardware metadata and legacy ENV are separately recorded.
        require(result['fx1'][6:24]==bytes(18),'Measured original hardware FX metadata view changed')
        require(struct.unpack_from('<I',result['env1'],12)[0]==0x4133dc and struct.unpack_from('<H',result['env1'],18)[0]==0x11d and
                struct.unpack_from('<I',result['env1'],20)[0]==0x604e40,'Actual original legacy store metadata differs')
        for a,b in [(0,5),(24,28)]+[(32+i*16,42+i*16) for i in range(8)]+[(160,288)]:require(r[1124+a:1124+b]==r[1636+a:1636+b],'Original host hardware FX restoration differs')
        require(r[2204:2232]==r[2232:2260],'Original host ENV restoration differs')
        reference[key]=result
    require(reference.keys()==expected_keys,'Original complete domain missing')
    for key,r in reference.items():
        if key[0]<65536:
            other=reference[(key[0]|65536,*key[1:])]
            require(all(r[k]==other[k] for k in spans),'Original repeated guest observation differs')
    return reference
def main():
    build,capture,output=map(lambda p:Path(p).resolve(),sys.argv[1:4]);require(output.is_relative_to(ROOT/'reports/m4-fp-directed') and not output.exists(),'Fresh private comparison required')
    b=json.loads(build.read_text());c=json.loads(capture.read_text());require(b['passed'] and c['passed_capture'],'Complete compiled/native and original capture required')
    bindings={**b['bindings'],**c['bindings']}
    for path,sha in bindings.items():require(digest(path)==sha,'Directed binding changed: '+path)
    corpus=ROOT/'tools/m4-fp-directed/corpus.hpp';inputs=[int(v,16) for v in re.findall(r'0x[0-9a-f]{8}',corpus.read_text())];require(len(inputs)==42,'Exact authored input corpus differs')
    reference=parse_original((capture.parent/'original.bin').read_bytes(),inputs,(ROOT/'reports/m4-fp-startup/research-r1/pages.bin').read_bytes())
    comparisons={level:first.check(parse_native((build.parent/('native-'+level+'.bin')).read_bytes()),reference) for level in ('O0','O2')}
    report={'passed_observed_domain':all(v['observed_mismatches']==0 for v in comparisons.values()),
            'scope':'42 authored first-root FP inputs,12 masked CWs,empty TOP0/7,two repeats; no full FP/M4 admission',
            'original_records':2016,'original_repeat_pairs':1008,'native_comparisons':4032,'comparisons':comparisons,
            'limitations':['Other nine required FP roots remain separate','No defined-bit architectural or independent final admission yet','No nonempty x87 or unmasked trap domain','No Runtime integration/connected startup FP order']}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    for file in (build,capture,output,BASE,Path(__file__).resolve()):bindings[str(file)]=digest(file)
    output.with_suffix('.pins.json').write_text(json.dumps({'files':bindings},indent=2)+'\n')
    print(json.dumps({'passed_observed_domain':report['passed_observed_domain'],'mismatches':{k:v['observed_mismatches'] for k,v in comparisons.items()},'report':str(output)}))
if __name__=='__main__':main()
