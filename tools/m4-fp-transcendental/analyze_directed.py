"""Measured authored binary64 corpus, full pages and exact State after-model."""
from pathlib import Path
import json
import re
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import analyze_cosine as base
COUNT=6144

def originals(data):
    base.require(data[:8]==b'MW4FPO01' and struct.unpack_from('<4I',data,8)==(1,COUNT,9,4096)
      and len(data)==24+COUNT*75988,'Actual directed original layout differs')
    result={}
    for offset in range(24,len(data),75988):
        r=data[offset:offset+75988];tag=struct.unpack_from('<5I',r)
        base.require(tag[1] in base.ROOTS and tag[:4] not in result,'Original root/key differs')
        result[tag[:4]]={'tag':tag,'cpu0':r[20:60],'cpu1':r[60:100],'fx0':r[100:612],'fx1':r[612:1124],
          'env0':r[2148:2176],'env1':r[2176:2204],'host0':r[1124:1636],'host1':r[1636:2148],
          'henv0':r[2204:2232],'henv1':r[2232:2260],'mem0':r[2260:39124],'mem1':r[39124:75988]}
    return result

def natives(data):
    base.require(data[:8]==b'MW4COS01' and struct.unpack_from('<6I',data,8)==(1,COUNT,83088,3504,9,4096)
      and len(data)==32+COUNT*83088,'Actual directed native layout differs')
    # The baseline parser consumes the identical record layout, one 192-record
    # chunk at a time. No original/native outputs are used during execution.
    for offset in range(32,len(data),192*83088):
        chunk=b'MW4COS01'+struct.pack('<6I',1,192,83088,3504,9,4096)+data[offset:offset+192*83088]
        yield from base.natives(chunk)

def extra(records,reference,pack,inputs):
    problems=[];before_memory=b''.join(pack[12+i*4104+8:12+i*4104+4104] for i in range(6,15))
    for index,n in enumerate(records):
        o=reference[n['tag'][:4]];repeat,input_index=n['tag'][0]>>16,n['tag'][0]&65535
        base.require(repeat in (0,1) and input_index<len(inputs),'Authored input key differs')
        input_address,output_address=base.ROOTS[n['tag'][1]]
        expected=bytearray(before_memory);struct.pack_into('<Q',expected,3*4096+(input_address&4095),inputs[input_index])
        struct.pack_into('<I',expected,8*4096+0x800,0x10000100)
        if o['mem0']!=expected:problems.append({'record':index,'field':'Original authored before pages'})
        after=bytearray(expected);offset=7*4096+(output_address&4095);after[offset:offset+4]=o['mem1'][offset:offset+4]
        if o['mem1']!=after:problems.append({'record':index,'field':'Original one-store after pages'})
        # Exact after-model from separately observed original architectural or
        # explicitly observed storage fields; every other State byte survives.
        state=bytearray(n['state0']);struct.pack_into('<I',state,2312,0x20001804);struct.pack_into('<I',state,2472,0x10000100)
        sw=struct.unpack_from('<H',o['fx1'],2)[0]
        for position,bit in [(2755,0),(2753,1),(2751,2),(2749,3),(2747,4),(2745,5),(2757,6),
          (2737,8),(2739,9),(2741,10),(2743,14)]:state[position]=(sw>>bit)&1
        struct.pack_into('<H',state,2770,sw&0xb880)
        state[2774:2776]=o['env1'][18:20];state[2776:2780]=o['env1'][12:16];state[2780:2782]=o['env1'][16:18]
        state[2784:2788]=o['env1'][20:24];state[2788:2790]=o['env1'][24:26]
        for slot in range(8):state[2486+slot*16:2496+slot*16]=o['fx1'][32+slot*16:42+slot*16]
        if n['state1']!=state:
            problems.append({'record':index,'field':'Complete State after-model',
              'offsets':[i for i,(a,b) in enumerate(zip(state,n['state1'])) if a!=b][:24]})
    return problems

def main():
    build,capture,directory=map(lambda p:Path(p).resolve(),sys.argv[1:4])
    base.require(directory.is_relative_to(ROOT/'reports/m4-fp-transcendental') and not directory.exists(),'Fresh private comparison directory required')
    metadata=json.loads(build.read_text());observed=json.loads(capture.read_text())
    base.require(metadata['passed'] and observed['passed_capture'],'Both actual workers must complete')
    bindings={**metadata['bindings'],**observed['bindings']}
    for p,sha in bindings.items():base.require(base.digest(p)==sha,'Changed actual binding '+p)
    corpus=ROOT/'tools/m4-fp-transcendental/directed/corpus.hpp'
    inputs=[int(value,16) for value in re.findall(r'0x([0-9a-f]{16})ULL',corpus.read_text())]
    base.require(len(inputs)==32,'Exact authored corpus size differs')
    pack_path=ROOT/'reports/m4-fp-startup/research-r1/pages.bin';pack=pack_path.read_bytes()
    reference=originals((capture.parent/'original.bin').read_bytes());comparisons={}
    for level in ('O0','O2'):
        records=list(natives((build.parent/f'native-{level}.bin').read_bytes()))
        comparisons[level]=base.check(records,reference)
        comparisons[level]['full_after_model_issues']=extra(records,reference,pack,inputs)
    directory.mkdir(parents=True);report={'passed_observed_domain':all(not c['observed_mismatches'] and not c['full_after_model_issues'] for c in comparisons.values()),
      'scope':'Actual directed four-cosine observations; no independent, connected or broad-state admission',
      'original_records':COUNT,'native_records':2*COUNT,'comparisons':comparisons,
      'limitations':['Empty x87 only; TOP0/7; masked exceptions; this hardware only','Original State and event trace unobserved',
       'Undefined condition fields and dead raw80 compared as observations','Native FX legacy projection is not original hardware FX metadata',
       'No shared Runtime or full M4 credit']}
    report_path=directory/'report.json';report_path.write_text(json.dumps(report,indent=2)+'\n')
    for p in (build,capture,corpus,Path(__file__).resolve(),Path(base.__file__),report_path):bindings[str(p)]=base.digest(p)
    (directory/'pins.json').write_text(json.dumps({'files':bindings},indent=2)+'\n')
    print(json.dumps({'original':COUNT,'native':2*COUNT,'mismatch_records':{k:v['mismatch_records'] for k,v in comparisons.items()},
      'status_xors':{k:v['status_xor_counts'] for k,v in comparisons.items()},'model_issues':{k:len(v['full_after_model_issues']) for k,v in comparisons.items()}}))

if __name__=='__main__':main()
