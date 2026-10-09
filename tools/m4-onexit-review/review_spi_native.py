"""Supplement the counterexample with the actual completed native SPI prefix."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-onexit-review'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 prior=pin(ROOT/'reports/m4-onexit-review/liveness-review-r1/report.json','6ed6bcb4cb55c6c1d4497a2ea560041b5cdf8b6e405276eb34be6fec73efa945')
 capture=pin(ROOT/'reports/m4-joint-startup54-root/execution-r4/O0/transport.json','b47878c5e5438b4295f02af1d525d4d21e8e786954e67dc2a4ea1b36da53bdb2')
 stage=json.loads(pin(capture.parent.parent/'O0-stage/stage.json').read_bytes());assert stage['status']=='nonzero_exit'and stage['exit_code']==1 and stage['artifact_sha256'][str(capture)]==sha(capture);pin(stage['argv'][0],stage['input_sha256'][stage['argv'][0]])
 script=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');s=importlib.util.spec_from_file_location('native_SPI_direct',script);D=importlib.util.module_from_spec(s);s.loader.exec_module(D);a=D.DirectSet(capture,pin)
 try:
  spi=a.data('sequence-0/phase-25.bin');consumer=a.data('sequence-0/phase-26.bin');assert len(spi)==len(consumer)==159716
  assert struct.unpack_from('<9I',spi)[:5]==(0,0,25,0x5e0110,0x482cf0)and struct.unpack_from('<9I',spi)[7:]==(0,1)
  assert struct.unpack_from('<9I',consumer)[2]==26 and struct.unpack_from('<9I',consumer)[4]==0x49d5c0 and struct.unpack_from('<9I',consumer)[7]==0
  registry_before=a.words('sequence-0/phase-26-before-registry.bin',32,'Q');registry_after=a.words('sequence-0/phase-26-after-registry.bin',32,'Q')
  assert registry_after[5]==registry_before[5]+1
  assert a.words('sequence-0/spi-fault.bin',6)==(0,0,0,0,1,1)
  api_before=a.data('sequence-0/spi-api-before.bin');api_after=a.data('sequence-0/spi-api-after.bin');assert len(api_before)==len(api_after)==4056
  ecx_before=struct.unpack_from('<I',api_before,4020)[0];ecx_after=struct.unpack_from('<I',api_after,4020)[0];root_ecx=struct.unpack_from('<I',spi,80)[0];next_ecx=struct.unpack_from('<I',consumer,40)[0]
  assert ecx_before==ecx_after==root_ecx==next_ecx==0
  page=a.data('sequence-0/phase-26-after-page-'+str(0x609000)+'.bin');assert len(page)==4096 and page[0x9e8]==0
  original=json.loads(prior.read_bytes())['actual_original_facts'][0];assert original['actual_original_global_byte']==0x6c
  failure=a.data('FAILURE.txt').decode();assert 'site=0x0042a570'in failure
  facts=dict(sequence=0,actual_completed_native_API_before_ECX=ecx_before,actual_completed_native_API_after_ECX=ecx_after,actual_completed_native_SPI_root_after_ECX=root_ecx,actual_next_constructor_before_ECX=next_ecx,actual_native_global_byte=page[0x9e8],actual_original_global_byte=original['actual_original_global_byte'],native_entire609000_page_sha256=hashlib.sha256(page).hexdigest(),later_enclosing_failure=failure)
 finally:a.close()
 out.mkdir(parents=True);pin(__file__);report=dict(inspection_passed=True,actual_native_counterexample_confirmed=True,previous_no_consumer_scope_valid=False,facts=facts,
  scope='Completed SPI and following byte-consuming constructor prefix in partial O0 selected54 run; no enclosing-run acceptance',source_or_native_modified=False,masking_allowed=False,initializer_credit=False,field_semantics_proven=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(inspection_passed=True,actual_native_counterexample_confirmed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
