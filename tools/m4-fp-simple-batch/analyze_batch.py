"""Compare actual raw two-root observations, keeping hardwareFX/legacyENV distinct."""
import argparse,collections,hashlib,json,mmap,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def require(ok,message):
    if not ok:raise ValueError(message)
def word(b,o):return struct.unpack_from('<I',b,o)[0]
def half(b,o):return struct.unpack_from('<H',b,o)[0]
def fields(b,native):
    x={'tag':struct.unpack_from('<5I',b),'cpu0':b[20:60],'cpu1':b[60:100]}
    if native:
        for k,a,z in [('state0',100,3604),('state1',3604,7108),('fx0',7108,7620),('fx1',7620,8132),('env0',8132,8160),('env1',8160,8188),('host0',8188,8700),('host1',8700,9212),('henv0',9212,9240),('henv1',9240,9268),('mem0',9268,46132),('mem1',46132,82996)]:x[k]=b[a:z]
        x['counts']=struct.unpack_from('<7I',b,82996);x['events']=[struct.unpack_from('<4I',b,83024+i*16) for i in range(4)]
    else:
        for k,a,z in [('fx0',100,612),('fx1',612,1124),('host0',1124,1636),('host1',1636,2148),('env0',2148,2176),('env1',2176,2204),('henv0',2204,2232),('henv1',2232,2260),('mem0',2260,39124),('mem1',39124,75988)]:x[k]=b[a:z]
    return x
def permitted_state():
    a=set(range(2312,2316))|set(range(2472,2476))|set(range(2770,2772))|set(range(2774,2782))|set(range(2784,2790))
    a|={2739,2745,2747,2749,2751,2753,2755,2757}
    for i in range(8):a.update(range(2486+16*i,2496+16*i))
    return a
def pair(o,n):
    errors=[]
    def eq(field,a,b):
        if a!=b:errors.append(field)
    eq('tag',o['tag'],n['tag'])
    for field in ('cpu0','cpu1','mem0','mem1'):eq(field,o[field],n[field])
    for ph in ('0','1'):
        ofx,nfx=o['fx'+ph],n['fx'+ph]
        eq('CW'+ph,ofx[:2],nfx[:2]);eq('definedFSW'+ph,half(ofx,2)&0xbaff,half(nfx,2)&0xbaff)
        eq('FTW'+ph,ofx[4],nfx[4]);eq('MXCSR'+ph,ofx[24:28],nfx[24:28]);eq('XMM'+ph,ofx[160:288],nfx[160:288])
        for i in range(8):eq('emptyStorage'+ph,ofx[32+16*i:42+16*i],nfx[32+16*i:42+16*i])
        oe,ne=bytearray(o['env'+ph]),bytearray(n['env'+ph]);struct.pack_into('<H',oe,4,half(oe,4)&0xbaff);struct.pack_into('<H',ne,4,half(ne,4)&0xbaff)
        eq('legacyENV'+ph,oe,ne)
        eq('hardwareFXZeroMetadata'+ph,ofx[6:24],bytes(18))
    before,after=n['state0'],n['state1'];allowed=permitted_state()
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before,after))):errors.append('protectedState')
    # Native State-to-projection consistency is distinct from hardware equality.
    for ph in ('0','1'):
        s=n['state'+ph];fx=n['fx'+ph];sw=half(s,2770)&0xb880
        for off,bit in ((2755,0),(2753,1),(2751,2),(2749,3),(2747,4),(2745,5),(2757,6),(2737,8),(2739,9),(2741,10),(2743,14)):sw|=s[off]<<bit
        eq('StateStatusProjection'+ph,half(fx,2),sw)
        eq('StateMetadataProjection'+ph,fx[6:24],s[2774:2792])
        for i in range(8):eq('StateStorageProjection'+ph,fx[32+16*i:42+16*i],s[2486+16*i:2496+16*i])
    pc=n['tag'][1];float_root=pc==0x4b5af0;count=4 if float_root else 3;tests=2 if float_root else 1
    eq('counts',n['counts'],(count,count-1,1,tests,tests,1,1))
    src=0x5c936c if float_root else 0x60b44c;dst=0x60b2b4 if float_root else 0x60b46c
    src_offset=4096+0x36c if float_root else 7*4096+0x44c;dst_offset=7*4096+(0x2b4 if float_root else 0x46c)
    expected=[(src,word(o['mem0'],src_offset),4,0)]*(2 if float_root else 1)+[(dst,word(o['mem1'],dst_offset),4,1),(0x20001800,0x10000100,4,0)]
    expected+=[(0,0,0,0)]*(4-count);eq('events',n['events'],expected)
    for label,r,xmm in [('original',o,128),('native',n,256)]:
        for a,z in [(0,5),(24,28)]+[(32+16*i,42+16*i) for i in range(8)]+[(160,160+xmm)]:eq(label+'HostFX',r['host0'][a:z],r['host1'][a:z])
        eq(label+'HostENV',r['henv0'],r['henv1'])
    return list(dict.fromkeys(errors))
def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--original',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--directed',action='store_true');a=p.parse_args()
    require(not a.output.exists() and a.output.resolve().is_relative_to(ROOT/'reports/m4-fp-simple-batch'),'Fresh private comparison required')
    build=json.loads(a.build.read_text(encoding='utf-8-sig'));require(build['passed'],'Complete build required')
    pins={}
    for name,h in build['bindings'].items():require(sha(name)==h,'Compiled baseline binding changed: '+name);pins[name]=h
    count=5952 if a.directed else 96;original_count=5952 if a.directed else 480;comparisons={}
    with a.original.open('rb') as of,mmap.mmap(of.fileno(),0,access=mmap.ACCESS_READ) as om:
      require(om[:8]==b'MW4FPO01' and struct.unpack_from('<4I',om,8)==(1,original_count,9,4096) and len(om)==24+original_count*75988,'Original framing')
      index={}
      for i in range(original_count):
        tag=struct.unpack_from('<5I',om,24+i*75988)
        if tag[1] not in (0x4b5af0,0x4c79d0):continue
        require(tag[:4] not in index,'Duplicate original key');index[tag[:4]]=24+i*75988
      require(len(index)==count,'Original domain count')
      for level in ('O0','O2'):
        path=a.build.parent/(('directed-' if a.directed else 'default-')+level+'.bin');totals=collections.Counter();samples=[];bad=0;seen=set();per_root={}
        with path.open('rb') as nf,mmap.mmap(nf.fileno(),0,access=mmap.ACCESS_READ) as nm:
          require(nm[:8]==b'MW4FPN01' and struct.unpack_from('<6I',nm,8)==(1,count,83088,3504,9,4096) and len(nm)==32+count*83088,'Native framing')
          for i in range(count):
            n=fields(nm[32+i*83088:32+(i+1)*83088],True);key=n['tag'][:4];require(key in index and key not in seen,'Native key');seen.add(key)
            o=fields(om[index[key]:index[key]+75988],False);errors=pair(o,n);pc=hex(key[1]);per_root.setdefault(pc,{'records':0,'mismatch_records':0,'status_bit_differences':{}});root=per_root[pc];root['records']+=1
            if errors:
                bad+=1;root['mismatch_records']+=1;totals.update(errors);diff=half(o['fx1'],2)^half(n['fx1'],2)
                k=hex(diff);root['status_bit_differences'][k]=root['status_bit_differences'].get(k,0)+1
                if len(samples)<16:samples.append({'tag':n['tag'],'fields':errors,'originalSW':half(o['fx1'],2),'nativeSW':half(n['fx1'],2),'input_word':hex(n['events'][0][1])})
          require(seen==set(index),'Complete native domain')
        comparisons[level]={'records':count,'mismatch_records':bad,'field_totals':dict(totals),'roots':per_root,'samples':samples}
    report={'passed_observed_domain':all(x['mismatch_records']==0 for x in comparisons.values()),'scope':'Two exact complete simple FP roots, directed authored input/DE masked domain; no full startup or nonempty/unmasked domain',
            'directed':a.directed,'repaired':build['repaired'],'comparisons':comparisons,'undefined_FSW_mask_exclusions':'C0/C2/C3',
            'State_and_events':'Actual native State before/after protected bytes and typed event order; original State/events remain unobserved',
            'dual_metadata':'Legacy ENV compared independently; State FX metadata kept separate from zero hardwareFX fields6..23'}
    a.output.write_text(json.dumps(report,indent=2)+'\n');pins[str(a.original.resolve())]=sha(a.original);pins[str(a.build.resolve())]=sha(a.build);pins[str(Path(__file__))]=sha(__file__);pins[str(a.output.resolve())]=sha(a.output)
    a.output.with_suffix('.pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n')
    print(json.dumps({'passed_observed_domain':report['passed_observed_domain'],'mismatches':{k:v['mismatch_records'] for k,v in comparisons.items()},'roots':comparisons['O0']['roots']}))
if __name__=='__main__':main()
