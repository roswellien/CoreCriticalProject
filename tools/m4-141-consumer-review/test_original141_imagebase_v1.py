"""Finite projected layout and exact source-payload inverse controls; no compilation."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141/imagebase-controls-r1';out.mkdir();files={};checks=[]
 def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;files[str(p)]=v;return p
 def read(p):return json.loads(pin(p).read_bytes())
 d=read(R/'reports/m4-original141/imagebase-preparation-r3/report.json')
 for p,h in d['files'].items():pin(p,h)
 child=R/'reports/m4-original141/source-preparation-r6';parent=R/'reports/m4-original141/source-preparation-r3'
 source=read(child/'report.json');assert source['passed'] and not source['whole_source_payload_byteidentical'] and source['physical_original_source_code_and_page_payload_byteidentical']
 before=pin(parent/'CMakeLists.txt').read_bytes();after=pin(child/'CMakeLists.txt').read_bytes();assert before.count(b'/BASE:0x18000000')==1 and after.count(b'/BASE:0x28000000')==1
 assert after.replace(b'/BASE:0x28000000',b'/BASE:0x18000000')==before
 identical=[]
 for p in parent.iterdir():
  if not p.is_file()or p.name in('report.json','pins.json','CMakeLists.txt'):continue
  assert pin(p).read_bytes()==pin(child/p.name).read_bytes();identical.append(p.name)
 bases=d['broker_unique_bases'];size=d['images'][0]['image_size']
 def layout(base,n,regions):
  assert base%65536==0 and n>0 and base+n<0x40000000
  assert len(regions)==len(set(regions))==36
  assert all(not(base<a+65536 and a<base+n)for a in regions)
 def check(name,fn,reject=False):
  try:fn()
  except AssertionError:assert reject,name
  else:assert not reject,name
  checks.append(dict(name=name,rejected=reject))
 check('new preferred range excludes every declared broker interval',lambda:layout(0x28000000,size,bases))
 check('old actual PE range rejected against guest stack',lambda:layout(0x18000000,size,bases),True)
 check('unaligned preferred base rejected',lambda:layout(0x28000001,size,bases),True)
 check('oversized signed32 range rejected',lambda:layout(0x28000000,0x18000000,bases),True)
 check('duplicate broker interval rejected',lambda:layout(0x28000000,size,bases[:-1]+[bases[0]]),True)
 check('preferred image moved into guest reserved region rejected',lambda:layout(0x20000000,size,bases),True)
 # Preserve actual full PE32 guest geometry and every allocation protection invariant.
 assert pin(child/'original_broker.hpp').read_bytes()==pin(parent/'original_broker.hpp').read_bytes()
 assert b'/DYNAMICBASE:NO /FIXED:NO /LARGEADDRESSAWARE'in after
 pin(__file__);p=out/'report.json';p.write_text(json.dumps(dict(passed=True,controls=checks,whole_identical_payload_files=identical,exact_CMake_one_token_inverse=True,actual_new_PE_awaiting_compile=True,projected_layout_only=True,original_worker_or_reader_launched=False,compiler_launched=False,initializer_credit=0,files=files),indent=2)+'\n',encoding='utf-8');print(sha(p))
if __name__=='__main__':main()
