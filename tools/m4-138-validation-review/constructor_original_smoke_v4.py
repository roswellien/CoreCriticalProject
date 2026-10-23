from pathlib import Path
import json,hashlib,importlib.util,traceback,sys
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-validation-review'/name;assert not out.exists();out.mkdir();pins={};a=None;passed=False;stage='preflight'
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.file_digest(p.open('rb'),'sha256').hexdigest();assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(R/p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  V=json.loads(pin(R/'reports/m4-138-validation-review/constructor-input-capture-validation-r2/report.json','aec13bc32dc8a0a02b5d9fd63d999e52c82bef8e9d63dbee8f74b330a786469f').read_bytes());assert V['passed']and V['reader_closed'];E=load('tools/m4-joint-startup131/paired_exports.py','ex');A=load('tools/m4-138-validation-review/constructor_original_input_v4.py','a');D=load('tools/m4-constructor-native/derive_source_v6.py','derive');preparation=pin(R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json','26b896f0523439030cbdd6cf4bd98cfadfbb9b15451bf80950600c37db892e6e');program,_=D.M.source_program(preparation);a=E.Facade(V['paired_exports'][0],pin);stage='own BEFORE adapter';inp=A.build(a,0,0x4103f0,program);(out/'input.json').write_text(json.dumps(inp,indent=2));stage='literal source';result=D.derive(inp,preparation);(out/'source.json').write_text(json.dumps(result,default=lambda v:v.hex()));passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc())
 finally:
  if a:a.close()
  pin(__file__);q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,stage=stage,canonical_reader_opened=False,ordinary_reader_closed=True,source_AFTER_seed=False,whole_TIB_claim=False,original_State_claim=False,initializer_credit=0,files=pins),indent=2));print(hashlib.file_digest(q.open('rb'),'sha256').hexdigest())
if __name__=='__main__':main(sys.argv[1])
