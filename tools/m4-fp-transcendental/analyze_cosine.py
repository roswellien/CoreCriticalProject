"""Compare actual native cosine records with separately captured originals.

Undefined condition fields and empty-tag raw80 are compared as observations,
without architectural admission. Actual legacy ENV and hardware FX metadata
remain separate; native State is an explicit software projection.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-fp-native'))
from analyze_first import digest,require
ROOTS={0x4ce5a0:(0x5cc530,0x60b4a0),0x4ce5c0:(0x5cc538,0x60b4a4),
 0x4ce5e0:(0x5cc540,0x60b49c),0x4ce600:(0x5cc548,0x60b494)}

def originals(data):
    require(data[:8]==b'MW4FPO01' and struct.unpack_from('<4I',data,8)==(1,480,9,4096) and
      len(data)==24+480*75988,'Exact original observation layout/count required')
    records={}
    for offset in range(24,len(data),75988):
        r=data[offset:offset+75988];tag=struct.unpack_from('<5I',r)
        if tag[1] not in ROOTS:continue
        require(tag[:4] not in records,'Duplicate original key')
        records[tag[:4]]={'tag':tag,'cpu0':r[20:60],'cpu1':r[60:100],
          'fx0':r[100:612],'fx1':r[612:1124],'env0':r[2148:2176],'env1':r[2176:2204],
          'host0':r[1124:1636],'host1':r[1636:2148],'henv0':r[2204:2232],'henv1':r[2232:2260],
          'mem0':r[2260:39124],'mem1':r[39124:75988]}
    require(len(records)==192,'Four complete original domains required');return records

def natives(data):
    require(data[:8]==b'MW4COS01' and struct.unpack_from('<6I',data,8)==(1,192,83088,3504,9,4096)
      and len(data)==32+192*83088,'Native cosine observation layout/count differs')
    for offset in range(32,len(data),83088):
        r=data[offset:offset+83088]
        yield {'tag':struct.unpack_from('<5I',r),'cpu0':r[20:60],'cpu1':r[60:100],
          'state0':r[100:3604],'state1':r[3604:7108],'fx0':r[7108:7620],'fx1':r[7620:8132],
          'env0':r[8132:8160],'env1':r[8160:8188],'host0':r[8188:8700],'host1':r[8700:9212],
          'henv0':r[9212:9240],'henv1':r[9240:9268],'mem0':r[9268:46132],'mem1':r[46132:82996],
          'counts':struct.unpack_from('<8I',r,82996),
          'events':[struct.unpack_from('<IQII',r,83028+i*20) for i in range(3)]}

def check(records,reference):
    problems=[];seen=set();mismatch_records=set();status_xors={};distinct=0
    def issue(i,field,o,n):
        mismatch_records.add(i)
        def view(data):
            if isinstance(data,bytes):return {'sha256':hashlib.sha256(data).hexdigest(),'prefix':data[:36].hex()}
            return data
        problems.append({'record':i,'field':field,'original':view(o),'native':view(n)})
    allowed=set(range(2472,2476))|set(range(2312,2316))|set(range(2770,2772))|set(range(2774,2792))
    allowed|={2755,2753,2751,2749,2747,2745,2757,2737,2739,2741,2743}
    for i in range(8):allowed.update(range(2486+i*16,2496+i*16))
    fp_spans=[(0,5),(24,28)]+[(32+i*16,42+i*16) for i in range(8)]+[(160,288)]
    for i,n in enumerate(records):
        key=n['tag'][:4];require(key in reference and key not in seen,'Native domain key missing/repeated');seen.add(key);o=reference[key]
        if n['tag']!=o['tag']:issue(i,'tag',o['tag'],n['tag'])
        for field in ('cpu0','cpu1','mem0','mem1','env0','env1'):
            if o[field]!=n[field]:
                issue(i,field,o[field],n[field])
                problems[-1]['offsets']=[j for j,(a,b) in enumerate(zip(o[field],n[field])) if a!=b][:24]
        for phase in ('0','1'):
            for a,b in fp_spans:
                if o['fx'+phase][a:b]!=n['fx'+phase][a:b]:issue(i,'FX'+phase+' span '+str((a,b)),o['fx'+phase][a:b],n['fx'+phase][a:b])
        swxor=struct.unpack_from('<H',o['fx1'],2)[0]^struct.unpack_from('<H',n['fx1'],2)[0]
        status_xors[swxor]=status_xors.get(swxor,0)+1
        if o['fx1'][6:24]!=n['fx1'][6:24]:distinct+=1
        changed=[j for j,(a,b) in enumerate(zip(n['state0'],n['state1'])) if a!=b and j not in allowed]
        if changed:issue(i,'Protected State',[],changed)
        if n['counts']!=(3,2,1,2,2,1,1,1):issue(i,'Actual bridge/primitive counts',(3,2,1,2,2,1,1,1),n['counts'])
        input_address,output_address=ROOTS[key[1]]
        expected=[(input_address,struct.unpack_from('<Q',o['mem0'],3*4096+(input_address&4095))[0],8,0),
          (output_address,struct.unpack_from('<I',o['mem1'],7*4096+(output_address&4095))[0],4,1),(0x20001800,0x10000100,4,0)]
        if n['events']!=expected:issue(i,'Actual ordered events',expected,n['events'])
        for side,record,xmm_end in [('original',o,288),('native',n,416)]:
            spans=[(0,5),(24,28)]+[(32+j*16,42+j*16) for j in range(8)]+[(160,xmm_end)]
            for a,b in spans:
                if record['host0'][a:b]!=record['host1'][a:b]:issue(i,side+' host FX restoration',record['host0'][a:b],record['host1'][a:b])
            if record['henv0']!=record['henv1']:issue(i,side+' host ENV restoration',record['henv0'],record['henv1'])
    require(seen==reference.keys(),'Incomplete native comparison domain')
    return {'records':len(seen),'mismatch_records':len(mismatch_records),'observed_mismatches':len(problems),
      'status_xor_counts':status_xors,'separate_FX_legacy_metadata_records':distinct,'issues':problems}

def main():
    build,directory=map(lambda p:Path(p).resolve(),sys.argv[1:3])
    require(directory.is_relative_to(ROOT/'reports/m4-fp-transcendental') and not directory.exists(),'Fresh private analysis directory required')
    metadata=json.loads(build.read_text());require(metadata['passed'],'Actual compiled build incomplete')
    original_pins=ROOT/'reports/m4-fp-startup/run-r1/closure/pins.json'
    require(digest(original_pins)=='2e62afe363336541379664032cc6d09ae75382caf4337e63578a3a8dc3d2a3fd','Exact original capture closure required')
    bindings={**json.loads(original_pins.read_text())['files'],**metadata['bindings']}
    for p,sha in bindings.items():require(digest(p)==sha,'Observation binding changed '+p)
    original=ROOT/'reports/m4-fp-startup/run-r1/original.bin';reference=originals(original.read_bytes())
    comparisons={level:check(natives((build.parent/f'native-{level}.bin').read_bytes()),reference) for level in ('O0','O2')}
    directory.mkdir(parents=True)
    report={'passed_observed_domain':all(v['observed_mismatches']==0 for v in comparisons.values()),
      'scope':'Four default-input cosine native observation domains; independent review and directed domains open',
      'original_records':192,'native_records':384,'comparisons':comparisons,
      'limitations':['All x87 tags empty; TOP0/7 only; exceptions masked','Original State/events unobserved',
       'Empty-tag raw80 and undefined C0/C2/C3 compared as observations only','Separate native legacy State and original hardware FX metadata',
       'No shared Runtime registration, full initializer order or native menu execution']}
    path=directory/'report.json';path.write_text(json.dumps(report,indent=2)+'\n')
    for p in (build,original_pins,Path(__file__).resolve(),path):bindings[str(p)]=digest(p)
    (directory/'pins.json').write_text(json.dumps({'files':bindings},indent=2)+'\n')
    print(json.dumps({'original':192,'native':384,'mismatch_records':{k:v['mismatch_records'] for k,v in comparisons.items()},
      'status_xors':{k:v['status_xor_counts'] for k,v in comparisons.items()}}))

if __name__=='__main__':main()
