"""Preserve v1; emit whole lease history and fail closed on partial native commits."""
from pathlib import Path
import hashlib,json,sys
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=P/'borrowed_mfc_v1.inc';assert sha(p)=='c54a2d450a66abe54d89571d74c8b2d397b58064b61e8a71281a6c9f2ba00f9b'
s=p.read_text().replace('capacity','extent')
a='  check();require(bootstrapped&&version_buffer_live_';assert s.count(a)==1;s=s.replace(a,'  check();try{require(bootstrapped&&version_buffer_live_',1)
a='  try{binding->guard();binding->source_identity();capture("version-buffer-after");pause();}catch(...){poison();throw;}\n }';assert s.count(a)==1;s=s.replace(a,'  binding->guard();binding->source_identity();capture("version-buffer-after");pause();\n  }catch(...){poison();throw;}\n }',1)
q=P/'borrowed_mfc_v2.inc';assert not q.exists();q.write_text(s)
p=P/'prepare_service_v1.py';assert sha(p)=='582bfbd25d62b5a8e637a25cde66379cf090ac88ca177437cf25e84e2a3d086b'
s=p.read_text();changes={"borrowed_mfc_v1.inc":"borrowed_mfc_v2.inc",'unsigned guest,generation,requested,capacity;':'unsigned guest,generation,requested,extent;','same-generation full version native-buffer lease/commit':'same-generation whole actual source HeapAlloc extent lease/commit','commits_whole_capacity_not_requested_prefix_only=True':'commits_whole_source_HeapAlloc_extent_not_requested_prefix_only=True,does_not_claim_unmeasured_HeapSize_capacity=True',"pin(__file__)":"pin(__file__);pin(R/'tools/m4-version-source/derive_service_v2.py');pin(R/'tools/m4-version-source/prepare_service_v1.py','582bfbd25d62b5a8e637a25cde66379cf090ac88ca177437cf25e84e2a3d086b');pin(R/'tools/m4-version-source/borrowed_mfc_v1.inc','c54a2d450a66abe54d89571d74c8b2d397b58064b61e8a71281a6c9f2ba00f9b')"}
for a,b in changes.items():assert s.count(a)==1,a;s=s.replace(a,b)
a="need(s.count(a)==1,'One concrete public service forwarding seam');s=s.replace(a,b);impl.write_text(s)"
b="""need(s.count(a)==1,'One concrete public service forwarding seam');s=s.replace(a,b)
  a='  sink("heap-query-witness.bin",std::as_bytes(std::span(b.query_witness)),user);'
  b=a+'\\n  for(unsigned n=0;n<version_buffer_history_.size();++n){const auto&v=version_buffer_history_[n];const auto stem="version-buffer-"+std::to_string(n);sink(stem+"-lease.bin",std::as_bytes(std::span(v.lease)),user);sink(stem+"-native-before.bin",v.before,user);sink(stem+"-native-after.bin",v.after,user);}\\n  const std::array<unsigned,4>version_status{1,unsigned(version_buffer_live_),unsigned(version_buffer_history_.size()),unsigned(version_buffer_before_.size())};sink("version-buffer-status.bin",std::as_bytes(std::span(version_status)),user);'
  need(s.count(a)==1,'One exact lease-history emission seam');s=s.replace(a,b);impl.write_text(s)"""
assert s.count(a)==1;s=s.replace(a,b)
q=P/'prepare_service_v2.py';assert not q.exists();q.write_text(s)
print(json.dumps(dict(emitted=[str(P/'borrowed_mfc_v2.inc'),str(q)],native_executed=False)))
