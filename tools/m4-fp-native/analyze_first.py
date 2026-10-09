"""Raw observations of the first compiled FP candidate; no acceptance shortcut.

Software State/FX/ENV projections and hardware original FX/ENV observations
retain their distinct provenance. Every mismatch is retained in the report.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while block:=f.read(1048576):h.update(block)
    return h.hexdigest()
def require(ok,why):
    if not ok:raise ValueError(why)
def u32(data,offset):return struct.unpack_from('<I',data,offset)[0]
def native(data):
    require(len(data)==32+48*83088 and data[:8]==b'MW4FPN01' and
            struct.unpack_from('<6I',data,8)==(1,48,83088,3504,9,4096),'Native fixed layout/count differs')
    for offset in range(32,len(data),83088):
        r=data[offset:offset+83088]
        yield {'tag':struct.unpack_from('<5I',r), 'cpu0':r[20:60],'cpu1':r[60:100],
               'state0':r[100:3604],'state1':r[3604:7108],
               'fx0':r[7108:7620],'fx1':r[7620:8132],
               'env0':r[8132:8160],'env1':r[8160:8188],
               'host0':r[8188:8700],'host1':r[8700:9212],
               'henv0':r[9212:9240],'henv1':r[9240:9268],
               'mem0':r[9268:46132],'mem1':r[46132:82996],
               'counts':struct.unpack_from('<7I',r,82996),
               'events':[struct.unpack_from('<4I',r,83024+i*16) for i in range(4)]}
def originals(data):
    require(len(data)==24+480*75988 and data[:8]==b'MW4FPO01' and
            struct.unpack_from('<4I',data,8)==(1,480,9,4096),'Original fixed layout/count differs')
    result={}
    for offset in range(24,len(data),75988):
        r=data[offset:offset+75988];tag=struct.unpack_from('<5I',r)
        if tag[1]!=0x4133c0:continue
        require(tag[:4] not in result,'Duplicate original key')
        result[tag[:4]]={'tag':tag,'cpu0':r[20:60],'cpu1':r[60:100],
                         'fx0':r[100:612],'fx1':r[612:1124],
                         'env0':r[2148:2176],'env1':r[2176:2204],
                         'mem0':r[2260:39124],'mem1':r[39124:75988]}
    require(len(result)==48,'Complete first-root original domain missing');return result
def check(records,reference):
    problems=[];checked=0;view_distinctions=0;seen=set()
    def issue(index,field,before,after):
        problems.append({'record':index,'field':field,'original':str(before),'native':str(after)})
    allowed=set(range(2472,2476))|set(range(2312,2316))|set(range(2770,2772))|set(range(2774,2792))
    allowed|={2755,2753,2751,2749,2747,2745,2757,2737,2739,2741,2743}
    for i in range(8):allowed.update(range(2486+i*16,2496+i*16))
    fp_spans=[(0,5),(24,28)]+[(32+i*16,42+i*16) for i in range(8)]+[(160,288)]
    for index,r in enumerate(records):
        key=r['tag'][:4];require(key in reference and key not in seen,'Native key missing/repeated');seen.add(key)
        o=reference[key];checked+=1
        if r['tag']!=o['tag']:issue(index,'tag',o['tag'],r['tag'])
        for field in ('cpu0','cpu1','mem0','mem1','env0','env1'):
            if r[field]!=o[field]:
                positions=[i for i,(a,b) in enumerate(zip(o[field],r[field])) if a!=b]
                issue(index,field,{'sha256':hashlib.sha256(o[field]).hexdigest(),'first_offsets':positions[:20]},
                      {'sha256':hashlib.sha256(r[field]).hexdigest(),'bytes_at_offsets':[r[field][i] for i in positions[:20]]})
        for phase in ('0','1'):
            for a,b in fp_spans:
                if r['fx'+phase][a:b]!=o['fx'+phase][a:b]:issue(index,'FX'+phase+' architectural span '+str((a,b)),o['fx'+phase][a:b].hex(),r['fx'+phase][a:b].hex())
        # The State metadata is retained as the legacy view. It must not be
        # zeroed merely to reproduce this machine's distinct FXSAVE view.
        if r['fx1'][6:24]!=o['fx1'][6:24]:view_distinctions+=1
        changed=[i for i,(a,b) in enumerate(zip(r['state0'],r['state1'])) if a!=b and i not in allowed]
        if changed:issue(index,'protected State',[],changed)
        if r['counts']!=(4,3,1,2,2,1,1):issue(index,'bridge counts',(4,3,1,2,2,1,1),r['counts'])
        expected=[(0x5e1f58,u32(o['mem0'],4*4096+0xf58),4,0)]*2
        expected +=[(0x604e40,u32(o['mem1'],6*4096+0xe40),4,1),(0x20001800,0x10000100,4,0)]
        if r['events']!=expected:issue(index,'actual ordered bridge events',expected,r['events'])
        for a,b in [(0,5),(24,28)]+[(32+i*16,42+i*16) for i in range(8)]+[(160,416)]:
            if r['host0'][a:b]!=r['host1'][a:b]:issue(index,'host FX restoration '+str((a,b)),r['host0'][a:b].hex(),r['host1'][a:b].hex())
        if r['henv0']!=r['henv1']:issue(index,'host legacy ENV restoration',r['henv0'].hex(),r['henv1'].hex())
    require(seen==reference.keys(),'Native domain incomplete')
    return {'records':checked,'observed_mismatches':len(problems),'issues':problems,'separate_FX_State_metadata_views':view_distinctions}
def main():
    build,output=map(lambda p:Path(p).resolve(),sys.argv[1:3]);require(output.is_relative_to(ROOT/'reports/m4-fp-native') and not output.exists(),'Fresh private analysis path required')
    closure=ROOT/'reports/m4-fp-startup/run-r1/closure/pins.json'
    require(digest(closure)=='2e62afe363336541379664032cc6d09ae75382caf4337e63578a3a8dc3d2a3fd','Exact original closure map required')
    bindings=json.loads(closure.read_text())['files'];metadata=json.loads(build.read_text())
    require(metadata['passed'],'Compiled observation recipe incomplete')
    bindings={**bindings,**metadata['bindings']}
    for path,sha in bindings.items():require(digest(path)==sha,'Observation binding changed: '+path)
    original_path=ROOT/'reports/m4-fp-startup/run-r1/original.bin';reference=originals(original_path.read_bytes());comparisons={}
    for level in ('O0','O2'):comparisons[level]=check(native((build.parent/('native-'+level+'.bin')).read_bytes()),reference)
    report={'passed_observed_domain':all(v['observed_mismatches']==0 for v in comparisons.values()),
            'scope':'First FP candidate observation only; no directed input, full-domain or M4 admission',
            'original_hardware_vs_native_State_projection':True,'comparisons':comparisons,
            'limitations':['Actual fixed 20.0 input only','No nonempty x87 or unmasked exception domain',
                           'No defined-bit architectural review or independent final review yet',
                           'FX State metadata and hardware FX metadata remain separately represented',
                           'No shared startup Runtime integration or connected FP initialization order']}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    bindings[str(build)]=digest(build);bindings[str(Path(__file__).resolve())]=digest(__file__);bindings[str(output)]=digest(output)
    pin_path=output.with_suffix('.pins.json');require(not pin_path.exists(),'Fresh analysis pins required');pin_path.write_text(json.dumps({'files':bindings},indent=2)+'\n')
    print(json.dumps({'report':str(output),'observed_mismatches':{k:v['observed_mismatches'] for k,v in comparisons.items()}}))
if __name__=='__main__':main()
