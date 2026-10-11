"""Versioned diagnostic-only optimization of prepared source comparison tools."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
from exact_equal import selfcheck
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-fs-provider-review'/name;assert not out.exists();out.mkdir(parents=True);pins={};generated={}
 def bind(p):
  p=Path(p).resolve();pins[str(p)]=sha(p);return p
 parent=bind(ROOT/'reports/m4-fs-provider-review/preparation-r1/report.json');assert sha(parent)=='19c5a0f66cdefded9ceedb148fe4f6e5af41c8dd3a36bf3ff19aeb770981a523'
 for name in('final_observer109.py','observe109.py'):
  p=bind(HERE/name);s=p.read_text()
  if name=='final_observer109.py':
   old='need=S.need;equal=S.equal';new='from exact_equal import equal\nneed=S.need;S.equal=equal';assert s.count(old)==1;s=s.replace(old,new)
  else:
   s=s.replace('import final_observer109 as V','import final_observer109_v2 as V').replace("with_name('final_observer109.py')","with_name('final_observer109_v2.py')")
   start=s.index('def equal(a,b,label):');end=s.index('\ndef projection',start);s=s[:start]+'from exact_equal import equal\n'+s[end:]
  q=p.with_name(p.stem+'_v2.py');assert not q.exists();ast.parse(s);q.write_text(s,encoding='utf-8');generated[str(q)]=sha(q)
 bind(HERE/'exact_equal.py');bind(__file__);tests=selfcheck();r=dict(passed=True,scope='Every complete len/byte equality check retained; diagnostic byte enumeration runs only on failure and is capped16',same_comparison_semantics=True,new_benchmark_speedup_claimed=False,selfcheck=tests,generated=generated,files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),selfcheck=tests)))
if __name__=='__main__':main(sys.argv[1])
