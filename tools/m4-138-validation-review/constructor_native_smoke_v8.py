"""Narrow ordinary O0 seq0 first-constructor literal frontier; no canonical lane."""
from pathlib import Path
import json,hashlib,importlib.util,sys,traceback
sys.dont_write_bytecode=True;R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/"reports/m4-138-validation-review"/name;assert not out.exists();out.mkdir();pins={};passed=False;f=None;result=None
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.file_digest(p.open("rb"),"sha256").hexdigest();assert h is None or h==v;pins[str(p)]=v;return p
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(R/p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  receipt=json.loads(pin(R/"reports/m4-138-validation-review/constructor37-raw-export-r1/report.json","2d5039d9ec0e4ae118a10c031f367bef3f97f78175bb0e57b3dbb2f813e582a1").read_bytes());assert receipt["passed"]and receipt["reader_closed"]
  E=load("tools/m4-joint-startup131/paired_exports.py","ex");A=load("tools/m4-138-validation-review/constructor_native_input_v7.py","input");D=load("tools/m4-constructor-native/derive_source_v5.py","derive");f=E.Facade(receipt["paired_exports"][0],pin)
  inp=A.build(f,"O0",0,0x4103f0);q=out/"input.json";q.write_text(json.dumps(inp,indent=2)+"\n");pin(q)
  preparation=pin(R/"reports/m4-constructor-native/source-comparison-preparation-r1/report.json","26b896f0523439030cbdd6cf4bd98cfadfbb9b15451bf80950600c37db892e6e")
  OriginalAPI=D.M.ActualAPIs
  class DiagnosticAPI(OriginalAPI):
   def __call__(self,m,target):
    fact=self.facts[self.index]if self.index<len(self.facts)else None
    (out/"API-frontier.json").write_text(json.dumps(dict(source_PC=m.PCs[-1],source_target=target,source_CPU=list(m.projected_cpu()),API_index=self.index,expected_fact=fact),indent=2)+"\n")
    return super().__call__(m,target)
  D.M.ActualAPIs=DiagnosticAPI
  result=D.derive(inp,preparation);q=out/"source-derivation.json";q.write_text(json.dumps(result,indent=2)+"\n");pin(q);passed=True
 except BaseException:(out/"failure.txt").write_text(traceback.format_exc());raise
 finally:
  if f is not None:f.close()
  q=out/"report.json";q.write_text(json.dumps(dict(passed=passed,scope="Single current native37 O0 sequence0 root4103F0 literal frontier only; current native own prior-region carry source review pending, no endpoint comparison or acceptance",source_computed=result is not None,source_AFTER_seed=False,canonical_reader_opened=False,ordinary_reader_closed=True,initializer_credit=0,files=pins),indent=2)+"\n");print(hashlib.file_digest(q.open("rb"),"sha256").hexdigest())
if __name__=="__main__":main(sys.argv[1])
