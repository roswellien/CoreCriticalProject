"""Independent review of the enlarged SPI volatile-field counterexample."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(name):
 out=ROOT/'reports/m4-onexit-review'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;(pins.update({str(p):v}));return p
 claim=json.loads(pin(ROOT/'reports/m4-onexit-source/spi-suffix-r1/report.json','e673f9232340bb5efd3e61712621e1f461fbab7e9c40f067b75491b861b36f9d').read_bytes())
 assert claim['inspection_complete'] and not claim['passed'] and claim['destination']==0x6099e8
 PE=load('review_suffix_PE',pin(ROOT/'tools/analysis/pe.py'));image=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=PE.PEImage(image)
 rows=claim['source_flow']
 assert [(r['pc'],r['bytes_hex'])for r in rows]==[(0x49d5d0,'51'),(0x49d5d1,'8a442403'),(0x49d5d5,'a2e8996000')]
 static=json.loads(pin(ROOT/'reports/m4-spi-workarea/static-r1/report.json').read_bytes());body={r['pc']:r for r in static['body']}
 assert body[0x482cca]['bytes']=='b906000000' and body[0x482cdb]['bytes']=='f3a5' and body[0x482cdd]['bytes']=='ff15dcb65b00'
 for r in rows+static['body']:
  n=r.get('width',r.get('size'));raw=bytes.fromhex(r.get('bytes_hex',r.get('bytes')));off,_=pe.rva_range(r['pc']-0x400000,n);assert image[off:off+n]==raw
 native=pin(ROOT/'reports/m4-joint-startup54/preparation-r6/spi_context.hpp','61b78ff8f01ae1c7160311030e08af2409d142112f219c372847851b3abbb67c').read_text()
 assert 's_.gpr.rax.dword=static_cast<unsigned>(result);s_.gpr.rsp.dword+=20;s_.gpr.rip.dword=return_pc;'in native and 's_.gpr.rcx'not in native
 D=load('review_suffix_archive',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'))
 original=json.loads(pin(ROOT/'reports/m4-onexit-source/original-run-r4/report.json','da0fd8d0bd3c1c0b4e57bc7a8b33875d33020aa8ab240cfd5d011b247620fe0e').read_bytes());a=D.DirectSet(original['original_capture'],pin);facts=[]
 try:
  for sequence in range(6):
   spi=a.data(f'phase/{sequence}/25.bin');consumer=a.data(f'phase/{sequence}/26.bin')
   assert len(spi)==len(consumer)==242304
   ecx=struct.unpack_from('<I',spi,80)[0];service_ecx=struct.unpack_from('<I',spi,240564+44)[0];incoming=struct.unpack_from('<I',consumer,40)[0];byte=consumer[121060+22*4096+0x9e8]
   assert ecx==service_ecx==incoming==0x6c9cbe03 and byte==(ecx>>24)==0x6c
   facts.append(dict(sequence=sequence,actual_original_SPI_after_ECX=ecx,actual_original_next_before_ECX=incoming,actual_original_global_byte=byte))
 finally:a.close()
 out.mkdir(parents=True);pin(__file__)
 result=dict(inspection_passed=True,previous_liveness_scope_admissible=False,source_receipt_sha256=sha(ROOT/'reports/m4-onexit-source/spi-suffix-r1/report.json'),
  scope='Six actual originals and byte-bound literal consumed-ECX chain. Current native SPI service only preserves incoming ECX; completed REP MOVSD source yields zero before API, so its representative source byte is predicted zero.',
  actual_original_facts=facts,source_flow=rows,native_ECX_zero_origin='Literal MOV ECX,6 followed by completed REP MOVSD; service retains this incoming ECX',
  native_source_predicted_byte=0,native_counterexample_execution_claimed=False,full54_cross_equality=False,field_semantics_proven=False,whole_game_liveness=False,
  masking_allowed=False,hardcoded_historical_API_clobber_allowed=False,required_resolution='Characterize the consumed source-local byte and its later consumers under an explicit source ABI/observation scope, or implement independently justified service compatibility.',
  initializer_credit=False,files=pins)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(inspection_passed=True,old_scope_admissible=False,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
