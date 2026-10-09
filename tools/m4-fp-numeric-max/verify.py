"""Combine direct hardware comparison with complete software observer model."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
sys.dont_write_bytecode=True
from analyze import Raw,compare,bind
from model import schedule,checks
ROOT=Path(__file__).resolve().parents[2]
def main():
 original,build,out=map(lambda x:Path(x).resolve(),sys.argv[1:4]);assert out.is_relative_to(ROOT/'reports/m4-fp-numeric-max') and not out.exists();out.mkdir(parents=True);results=[];pack=(ROOT/'reports/m4-fp-numeric-max/recovery-r1/pages.bin').read_bytes()
 for mode in ('default','directed'):
  o=Raw(original/(mode+'.bin'),b'MW4NMO01',35764);expected=list(schedule(mode=='directed'));assert len(expected)==o.count
  for level in ('O0','O2'):
   n=Raw(build/(mode+'-'+level+'.bin'),b'MW4NMN01',47432);assert n.count==o.count;failures=Counter();samples=[];counts={'ordered_events':0,'routes':0,'State_bytes_checked':0,'live_checkpoints':0,'C1_proved_finite':0,'C1_observed_only':0}
   for i,t in enumerate(expected):
    a,b=o.record(i),n.record(i);import struct
    assert struct.unpack_from('<10I',a)==t,'Actual domain order changed'
    paired=o.record(i-1) if t[2]==0x4c19f0 else None
    diff=compare(a,b)+checks(a,b,paired,pack);failures.update(diff)
    if diff and len(samples)<64:samples.append({'index':i,'tag':t,'errors':diff})
    counts['ordered_events']+=2 if t[2]==0x780c10f0 else 22;counts['routes']+=0 if t[2]==0x780c10f0 else 2;counts['State_bytes_checked']+=3504*2+(3504 if paired else 0);counts['live_checkpoints']+=bool(paired)
    # Finite binary32 load is exact in fp80; the same finite value stores back
    # exactly to binary32. Headroom prevents overflow/underflow of x87 stack.
    if t[1]<=10:
     assert not (struct.unpack_from('<H',a,634)[0]&0x200),'Exact finite conversion C1 differs';counts['C1_proved_finite']+=1
    else:counts['C1_observed_only']+=1
   results.append({'mode':mode,'level':level,'records':o.count,'passed':not failures,'errors':dict(failures),'samples':samples,'counts':counts,'original':bind(o.path),'native':bind(n.path)})
 report={'passed':all(r['passed'] for r in results),'results':results,'sources':[bind(__file__),bind(Path(__file__).with_name('model.py')),bind(Path(__file__).with_name('analyze.py'))],
 'scope':'Standalone bounded exact game/provider closure, full CPU/pages/native State/events/routes; original State/events unobserved. Intermediate legacy metadata inferred from paired actual leaf FNSTENV plus recovered no-FP integer call route, while debugger CONTEXT zero metadata is retained as separate observed projection.',
 'FP_conditions':'C1 credited only finite exact load/store cases; C0/C2/C3 and remaining C1 and dead empty raw80 retained as observations','full_M4_complete':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([{'mode':r['mode'],'level':r['level'],'passed':r['passed'],'errors':r['errors'],'counts':r['counts']} for r in results]))
if __name__=='__main__':main()
