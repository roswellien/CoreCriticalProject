"""Schema-only adverses; no actual output file, worker, or raw reader opened."""
from pathlib import Path
import ast,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-preresource-strict-review/schema-preflight-r1';assert not out.exists();out.mkdir(parents=True)
 p=R/'tools/m4-138-preresource-strict-review/ordinary_case.py';s=importlib.util.spec_from_file_location('schema_only',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 prep=R/'reports/m4-138-preresource-strict-review/preparation-r1/report.json';v=json.loads(prep.read_bytes());assert v['passed']and v['whole_parent_inverse']
 for q,h in v['files'].items():assert sha(q)==h
 ast.parse((prep.parent/'verify_case_v1.py').read_text());ast.parse((Path(__file__).parent/'aggregate_v1.py').read_text())
 class Schema:
  def __init__(self,d):self.d=d;self.entries=d
  def data(self,k):return self.d[k]
 checks=[]
 def reject(name,fn):
  try:fn()
  except (ValueError,KeyError,struct.error):checks.append(name);return
  raise AssertionError('Adverse not rejected: '+name)
 base={'before/State.bin':b'a'*3504,'after/State.bin':b'a'*3504,'before/private.bin':b'z','after/private.bin':b'z'}
 assert m.retry_scope(Schema(base),'before/','after/',('State.bin','private.bin'))==2
 for key in base:
  d=dict(base);d.pop(key);reject('missing-'+key,lambda d=d:m.retry_scope(Schema(d),'before/','after/',('State.bin','private.bin')))
 d=dict(base);d['after/extra.bin']=b'x';reject('extra-after-field',lambda:m.retry_scope(Schema(d),'before/','after/'))
 for key in ('after/State.bin','after/private.bin'):
  d=dict(base);d[key]=b'!'+d[key][1:];reject('changed-'+key,lambda d=d:m.retry_scope(Schema(d),'before/','after/'))
 hw=bytes(1632);m.hardware(hw)
 for offset in(1088,1600):
  b=bytearray(hw);b[offset]=1;reject('whole-hardware-byte-'+str(offset),lambda b=b:m.hardware(bytes(b)))
 reject('short-hardware',lambda:m.hardware(hw[:-1]))
 cpu=struct.pack('<10I',0,0,0,0,0x20001800,0,0,0,0x202,0x5ae3e4);page=bytearray(4096);struct.pack_into('<I',page,0x800,0x410a80);frame=bytes(page[0x800:0x840]);m.frame64(frame,cpu,bytes(page))
 for offset in(0,4,63):
  b=bytearray(frame);b[offset]^=1;reject('entry-frame-byte-'+str(offset),lambda b=b:m.frame64(bytes(b),cpu,bytes(page)))
 for offset in(16,36):
  b=bytearray(cpu);b[offset]^=1;reject('entry-CPU-byte-'+str(offset),lambda b=b:m.frame64(frame,bytes(b),bytes(page)))
 reject('short-entry64',lambda:m.frame64(frame[:-1],cpu,bytes(page)))
 files={str(q.resolve()):sha(q)for q in(p,Path(__file__),prep,prep.parent/'verify_case_v1.py',Path(__file__).parent/'aggregate_v1.py')}
 result=dict(passed=True,scope='Bounded synthetic schema controls only; no actual runtime refusal evidence',adverses=checks,count=len(checks),actual_case_review_executed=False,worker_executed=False,reader_opened=False,accepted_function_credit=0,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,count=len(checks),sha256=sha(out/'report.json'))))
if __name__=='__main__':main()
