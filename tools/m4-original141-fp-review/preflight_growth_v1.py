"""Synthetic capacity/ownership/domain controls; no actual source run."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];P=R/'reports/m4-original141-fp-review/source-preparation-r2'
def main(out):
 assert not out.exists();out.mkdir(parents=True)
 s=importlib.util.spec_from_file_location('growth_controls',P/'registry_growth_v1.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
 assert g.predict((0x1000,0x107c,128,1),128)is False
 assert g.predict((0x1000,0x1080,128,1),128)is True
 roots=((17,0x40e250),(18,0x40ef50),(19,0x40f000),(50,0x479590),(137,0x5a3c30),(138,0x5a3ff0),(139,0x5a66f0))
 rows=[dict(identity=[seq,p,r],meta=[0x1000,0x1080 if p==138 else 0x107c,128,1],backing_bytes=128)for seq in range(6)for p,r in roots]
 assert g.domain(rows)==g.EXPECTED
 rejected=[]
 def reject(name,fn):
  try:fn()
  except ValueError:rejected.append(name);return
  raise AssertionError('Adverse must fail '+name)
 for name,meta,n in [('null-owner',[0,0,128,1],128),('past-owner',[0x1000,0x1084,128,1],128),('before-owner',[0x1000,0xffc,128,1],128),('unaligned-next',[0x1000,0x107e,128,1],128),('unaligned-capacity',[0x1000,0x107c,127,1],127),('mode',[0x1000,0x107c,128,0],128),('whole-backing',[0x1000,0x107c,128,1],127),('bool-type',[0x1000,0x107c,128,True],128),('overflow',[0xffffffc0,0xffffffc0,128,1],128)]:reject(name,lambda meta=meta,n=n:g.predict(meta,n))
 for seq in range(6):
  altered=copy.deepcopy(rows);next(r for r in altered if r['identity']==[seq,138,0x5a3ff0])['meta'][1]=0x107c
  reject('missing-growth-sequence-'+str(seq),lambda altered=altered:g.domain(altered))
 altered=copy.deepcopy(rows);altered[0]['meta'][1]=0x1080;reject('extra-growth-case',lambda:g.domain(altered))
 reject('missing-root',lambda:g.domain(rows[:-1]))
 altered=copy.deepcopy(rows);altered[0]=altered[1];reject('duplicate-case',lambda:g.domain(altered))
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,synthetic_positive_controls=3,rejected=rejected,source_evaluated=False,archive_reader_opened=False,acceptance_credit=0,files={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in (P/'report.json',P/'registry_growth_v1.py',Path(__file__).resolve())}),indent=2)+'\n');print(str(q))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
