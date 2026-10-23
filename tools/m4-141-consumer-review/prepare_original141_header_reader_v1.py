"""Exact physical legacy magic and explicit fresh-reader/captured-writer admission bridge."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141/header-reader-preparation-r1';out.mkdir();files={};ds=[]
 def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;files[str(p)]=v;return p
 p=pin(R/'tools/m4-141-consumer-review/validate_original141_v6.py');s=p.read_text()
 def edit(a,b):
  nonlocal s
  assert s.count(a)==1;s=s.replace(a,b);ds.append(dict(old=a,new=b,count=1))
 edit("header[:8]==b'MW4J141O'","header[:8]==b'MW4J138O'")
 anchor="  need(admission['files'].get(str(Path(__file__).resolve()))==sha(Path(__file__).resolve()),'Actual validator code belongs to exact ROOT admission')"
 edit(anchor,anchor+"""
  need(preflight_path==ROOT/'reports/m4-original141/root-strict-reader-admission-r1/report.json','Exact independently sealed reader-only admission')
  capture_preflight_path=ROOT/'reports/m4-original141/root-capture-admission-r2/report.json';capture_preflight_digest='2317169a720a88b44b8c14de8f78ffea13974efaca78d4dc88a1a5331c244697'
  need(Path(admission['capture_preflight_path']).resolve()==capture_preflight_path and admission['capture_preflight_sha256']==capture_preflight_digest and admission['files'].get(str(capture_preflight_path))==capture_preflight_digest,'Fresh reader admission physically binds immutable actually used writer admission')
  captured_writer_admission=read(pin(capture_preflight_path,capture_preflight_digest));need(captured_writer_admission['passed'] and captured_writer_admission['original141_writer_admitted']is True,'Actual current captured writer was independently admitted')
  for dependency,identity in captured_writer_admission['files'].items():pin(dependency,identity)
  need(admission['files'].get(str(Path(execution)/'report.json'))==sha(Path(execution)/'report.json'),'Fresh reader admission seals exact already-terminal writer execution before reader opens')""")
 edit("need(run['preflight_sha256']==preflight_digest,'Actual execution bound current independent preflight')","need(run['preflight_sha256']==capture_preflight_digest and Path(run['preflight_path']).resolve()==capture_preflight_path,'Actual captured execution bound immutable writer preflight, distinct from current reader-only gate')")
 rev=s
 for d in reversed(ds):assert rev.count(d['new'])==1;rev=rev.replace(d['new'],d['old'])
 assert rev==p.read_text();q=R/'tools/m4-141-consumer-review/validate_original141_v7.py';assert not q.exists();ast.parse(s);q.write_text(s,encoding='utf-8');pin(q)
 source=pin(R/'reports/m4-original141/source-preparation-r6/reference.cpp').read_bytes();assert b'std::memcpy(header.magic,debugger?"MW4J138D":"MW4J138O",8)'in source
 assert b'header.version=1;header.sequence_count=sequences;header.root_count=roots;header.total_phases=phase_count;header.page_count=observed_page_count;header.record_size=sizeof(Record);out.append("header.bin",&header,sizeof(header));'in source
 proof=json.loads(pin(R/'reports/m4-original141/root-compiled-review-r2/report.json','e756132a1c938d6b5318f8a2b65e954a17c44870be2bab556427767ef233214c').read_bytes());assert proof['passed']
 links=json.loads(pin(R/'reports/m4-original141/root-compiled-review-r2/physical-links.json').read_bytes());assert any(r['symbol']=='_main'for r in links)
 from importlib.util import spec_from_file_location,module_from_spec
 path=pin(R/'tools/analysis/pe.py');sp=spec_from_file_location('header_producer_PE',path);PE=module_from_spec(sp);sp.loader.exec_module(PE)
 build=json.loads(pin(R/'reports/m4-original141/build-r2/build.json','d5a3be0ae42a04f2ca52f2f49ad8163caa7a5599c2bd9a84170c222ba6c24ba9').read_bytes());worker=PE.PEImage(pin(build['worker'],build['worker_sha256']).read_bytes());hits=[]
 for sec in worker.sections:
  data=worker.data[sec['raw_offset']:sec['raw_offset']+sec['raw_size']]
  for magic in (b'MW4J138O',b'MW4J138D'):
   positions=[i for i in range(len(data))if data.startswith(magic,i)]
   hits.extend(dict(magic=magic.decode(),section=sec['name'],actual_address=worker.image_base+sec['virtual_address']+i,raw_offset=sec['raw_offset']+i)for i in positions)
 assert {h['magic']for h in hits}=={'MW4J138O','MW4J138D'} and all(h['section']=='.rdata'for h in hits)
 pin(R/'reports/m4-original141/root-capture-execution-r2/report.json','2897d2f5e3a6607e1609ea15a661a0cc76bffd12e2c9017a5b2993c7bb590820')
 pin(R/'reports/m4-original141/root-capture-validation-r1/report.json','761056b6b4a626280bc2fe2fffbf64afd198421af0f35b346913ab9a54349a52');pin(R/'reports/m4-original141/root-capture-validation-r1/failure.txt')
 d=out/'validator-deltas.json';d.write_text(json.dumps(ds,indent=2)+'\n',encoding='utf-8');pin(d);pin(__file__)
 report=dict(passed=True,prepared_only=True,exact_three_delta_inverse=True,header_magic_only_change=True,all_six_numeric_header_predicates_unchanged=True,actual_producer_magic=hits,capture_preflight_path=str(R/'reports/m4-original141/root-capture-admission-r2/report.json'),capture_preflight_sha256='2317169a720a88b44b8c14de8f78ffea13974efaca78d4dc88a1a5331c244697',new_reader_admission_path=str(R/'reports/m4-original141/root-strict-reader-admission-r1/report.json'),required_reader_fields=['passed=True','original141_validator_admitted=True','capture_preflight_path','capture_preflight_sha256','files exactvalidator7/currentworker/build/terminalexecution + immutablecaptureadmission2/all current dependencies'],one_reader_unchanged=True,worker_relaunch_required=False,worker_launched=False,reader_opened=False,initializer_credit=0,files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(sha(p),sha(q))
if __name__=='__main__':main()
