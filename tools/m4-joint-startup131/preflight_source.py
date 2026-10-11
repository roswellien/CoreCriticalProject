"""Bounded source-only loader construction checks; no archive or execution."""
from pathlib import Path
import ast, hashlib, importlib.util, json, sys, traceback
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup131-source'/name;assert not out.exists();out.mkdir(parents=True);files={};passed=False;result={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 try:
  receipt=json.loads(pin(ROOT/'reports/m4-joint-startup131-source/preparation-r1/report.json','c8fc77b26a83e9d5dccce678c01bc043183ba974d1c57d631647e9a313b08a7b').read_bytes());assert receipt['passed']
  for p,h in receipt['files'].items():pin(p,h);ast.parse(Path(p).read_text())
  p=pin(ROOT/'tools/m4-joint-startup131/mfc_source.py');s=importlib.util.spec_from_file_location('mfc_static_loader_preflight',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
  preparation=json.loads(pin(ROOT/'reports/m4-joint-startup131/preparation-r1/report.json','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25').read_bytes());extension=m.Extension(preparation,pin)
  before={'memory':{}};result=extension.loader(before);assert len(extension.new)==8 and len(extension.normal_PCs)==142 and len(extension.contracts['normal_APIs'])==4
  second={'memory':dict(before['memory'])};assert extension.loader(second)==result and second['memory']==before['memory']
  invalid={'memory':dict(before['memory'])};a=preparation['inputs']['role_owners'][4]['new'];b=bytearray(invalid['memory'][a]);b[20]^=1;invalid['memory'][a]=bytes(b)
  try:extension.loader(invalid)
  except ValueError as e:assert 'complete declared source input'in str(e);result['changed_whole_borrowed_BEFORE_rejected']=True
  else:raise ValueError('Altered complete borrowed input unexpectedly admitted')
  result.update(constructed_source_regions=len(before['memory']),whole_new_loader_regions=8,typed_rewritten_cells=6,whole_CRT_merge_cells=3,genuine_instruction_order=142,typed_API_declarations=4)
  pin(__file__);pin(sys.executable)
  for p,h in files.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Source-only construction/identity test of declared genuine BEFORE loader inputs; no caller state, native runtime, canonical capture, phase execution, or initializer credit',counts=result,files=files,capture_reader_opened=False,native_worker_executed=False,initializer_credit=0)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
