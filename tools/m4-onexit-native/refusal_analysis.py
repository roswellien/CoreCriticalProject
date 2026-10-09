"""Read-only analysis of canonical refusal and physical Windows export chains."""
import hashlib,importlib.util,json,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-crt-locale-batch-review'))
from transport import DirectSet
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=ROOT/'reports/m4-onexit-native/refusal-analysis-r1'
 if out.exists():raise RuntimeError('Fresh analysis only')
 out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).absolute();actual=sha(p)
  if h is not None and actual!=h:raise RuntimeError('Exact static/archive dependency required')
  pins[str(p)]=actual;return p
 spec=importlib.util.spec_from_file_location('onexit_physical_exports',pin(ROOT/'tools/m4-crt-locale-batch-review/check_v2.py'));exports=importlib.util.module_from_spec(spec);spec.loader.exec_module(exports)
 direct=DirectSet(pin(ROOT/'reports/m4-joint-startup54-root/execution-r2/O0/transport.json'),pin)
 try:
  prefix='sequence-0/selected/';api=direct.words(prefix+'locale-api-6-witness.bin',32,'Q')
  names=[direct.data(n).decode() for n in direct.names() if n.endswith('-name.bin')]
  kernel=pin(Path('C:/Windows/System32/kernel32.dll'));ntdll=pin(Path('C:/Windows/System32/ntdll.dll'))
  physical=[]
  for requested,alias in [('HeapSize','RtlSizeHeap'),('HeapReAlloc','RtlReAllocateHeap')]:
   named_rva,forward=exports.export(kernel,requested);owner_rva,owner_forward=exports.export(ntdll,alias)
   if forward!='NTDLL.'+alias or owner_forward:raise RuntimeError('Exact physically observed native forwarder chain')
   physical.append(dict(requested=requested,named_rva=named_rva,physical_forwarder=forward,owner_export=alias,owner_rva=owner_rva,owner_forwarder=owner_forward))
  source=pin(ROOT/'reports/m4-onexit-native/preparation-r7/forward_identity.inc');text=source.read_text()
  if '"HeapSize"' in text or '"HeapReAlloc"' in text:raise RuntimeError('Preserved source chain omission')
  if api[2]!=0x780015b5 or api[4]!=0x34bd0 or api[14] or 'locale-api-6-before' in names:raise RuntimeError('Actual refusal occurs before HeapSize invocation/checkpoint')
  report=dict(passed=True,scope='Read-only canonical refused-run and physical native export analysis; no new provider/API execution',api6_words=api,first_fault=direct.words(prefix+'locale-fault.bin',4),captured_reason=direct.data(prefix+'locale-fault-reason.bin').decode(),physical_exports=physical,inference='Actual HeapSize bridge measured_api invokes export proof before API6-before checkpoint; the exact physical NTDLL.RtlSizeHeap chain is absent from the frozen proof allowlist, causing its explicit runtime_error. Original exception text was erased, so this is a code/path inference supported by prior captured call-not-made facts.',files=pins)
  pin(__file__);report['files']=pins
  (out/'report.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
  print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),physical_exports=physical)))
 finally:direct.close()
if __name__=='__main__':main()
