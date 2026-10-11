"""Preserve v3; bind actual API incoming error and same-owner requested alias."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,a
 return s.replace(a,b,1)
api=P/'borrowed_version_api_v1.inc'
assert sha(api)=='ced31447ddedb572851fbb4063f77dea0a0ba9f368c636b43503b7766ce9c2f7'
s=api.read_text()
s=once(s,' void borrow_version_api(State&source,unsigned site,unsigned frame,unsigned ret){\n  check();',' void borrow_version_api(State&source,unsigned site,unsigned frame,unsigned ret){\n  fn::LastErrorBoundary errors;const auto source_error=errors.saved;\n  check();')
s=once(s,'  InvocationHostBoundary caller;fn::LastErrorBoundary errors;','  InvocationHostBoundary caller;')
s=once(s,'const auto error_before=GetLastError();mw34_version_native_api(provider,args.data(),&rec.hardware);const auto error_after=GetLastError();','SetLastError(source_error);const auto error_before=GetLastError();mw34_version_native_api(provider,args.data(),&rec.hardware);const auto error_after=GetLastError();rec.last_error={source_error,error_before,error_after};')
s=once(s,'   unsigned guest_pointer{};if(index==2&&pointer){const auto p=reinterpret_cast<std::uintptr_t>(pointer),base=reinterpret_cast<std::uintptr_t>(buffer.native);require(p>=base&&p-base<=buffer.extent&&length<=buffer.extent-(p-base),"Actual query pointer/length lie inside that same whole MFC native owner");guest_pointer=buffer.guest+unsigned(p-base);}',
'''   unsigned guest_pointer{},alias_offset{};const auto native_base=reinterpret_cast<std::uintptr_t>(buffer.native),native_pointer=reinterpret_cast<std::uintptr_t>(pointer);
   if(index==2){require(!unsigned(rec.hardware.after.rax)||pointer,"Actual successful root query must return a native owner alias");if(pointer){require(native_pointer>=native_base&&native_pointer-native_base<buffer.requested&&length<=buffer.requested-(native_pointer-native_base),"Actual query pointer and whole returned length lie inside requested resource bytes of the same MFC owner");alias_offset=unsigned(native_pointer-native_base);guest_pointer=buffer.guest+alias_offset;}}
   rec.owner_alias={buffer.guest,buffer.generation,buffer.requested,buffer.extent,native_base,native_pointer,alias_offset,length};''')
q=P/'borrowed_version_api_v2.inc';assert not q.exists();q.write_text(s)
header=P/'native_version_api_v1.hpp'
assert sha(header)=='dec29e48d8e974e96c3630d6e8c7d3ab20c98db822e19af140749ecb1d50d4c0'
s=once(header.read_text(),'struct alignas(16) Record {std::array<std::uint64_t,16>words;','struct alignas(16) Record {std::array<std::uint64_t,16>words;std::array<std::uint64_t,3>last_error;std::array<std::uint64_t,8>owner_alias;')
q=P/'native_version_api_v2.hpp';assert not q.exists();q.write_text(s)
p=P/'prepare_service_v3.py';s=p.read_text();parent_sha=sha(p)
s=once(s,"pin(R/'tools/m4-version-source/native_version_api_v1.hpp','dec29e48d8e974e96c3630d6e8c7d3ab20c98db822e19af140749ecb1d50d4c0')","pin(R/'tools/m4-version-source/native_version_api_v2.hpp','%s')"%sha(P/'native_version_api_v2.hpp'))
s=once(s,"pin(R/'tools/m4-version-source/borrowed_version_api_v1.inc').read_text()","pin(R/'tools/m4-version-source/borrowed_version_api_v2.inc','%s').read_text()"%sha(P/'borrowed_version_api_v2.inc'))
a='sink(stem+"-words.bin",std::as_bytes(std::span(v.words)),user);'
s=once(s,a,a+'sink(stem+"-last-error.bin",std::as_bytes(std::span(v.last_error)),user);sink(stem+"-owner-alias.bin",std::as_bytes(std::span(v.owner_alias)),user);')
s=once(s,"pin(R/'tools/m4-version-source/derive_service_v3.py');","pin(R/'tools/m4-version-source/derive_service_v3.py');pin(R/'tools/m4-version-source/derive_service_v4.py');pin(R/'tools/m4-version-source/prepare_service_v3.py','%s');pin(R/'tools/m4-version-source/borrowed_version_api_v1.inc','ced31447ddedb572851fbb4063f77dea0a0ba9f368c636b43503b7766ce9c2f7');pin(R/'tools/m4-version-source/native_version_api_v1.hpp','dec29e48d8e974e96c3630d6e8c7d3ab20c98db822e19af140749ecb1d50d4c0');"%parent_sha)
s=once(s,'typed_native_query_pointer_projection=True,','typed_native_query_pointer_projection=True,query_alias_inside_requested_resource_bytes=True,query_owner_alias_words=8,source_boundary_LastError_captured_before_diagnostics=True,actual_LastError_restored_immediately_before_native_API=True,actual_LastError_after_captured_before_diagnostics=True,guest_LastError_projection_claim=False,literal_4AF174_max52_copy_unchanged=True,')
q=P/'prepare_service_v4.py';assert not q.exists();q.write_text(s)
print(json.dumps(dict(emitted=str(q),prepare_sha256=sha(q),api_sha256=sha(P/'borrowed_version_api_v2.inc'),header_sha256=sha(P/'native_version_api_v2.hpp'),native_executed=False)))
