"""Add genuine bounded heap pressure for the actual moved-alias control only."""
from pathlib import Path
import hashlib
HERE=Path(__file__).parent
def derive(name,old,replacements):
 p=HERE/name;assert not p.exists();s=(HERE/old).read_text()
 for a,b in replacements:assert s.count(a)==1,(old,a);s=s.replace(a,b)
 p.write_text(s)
pressure=r'''
// Research allocations have no guest aliases and are excluded from source owner
// credit. They occupy real blocks on the exact live private heap so a genuine
// HeapReAlloc can move; the source request, flags, API and result are unchanged.
inline HANDLE pressure_heap{};
inline std::vector<std::array<std::uint64_t,12>>pressure_rows;
inline std::array<mw34::m4_cmd_native::ApiIdentity,3>pressure_before,pressure_after;
inline mw34::m4_cmd_native::ApiIdentity pressure_identity(const char*requested,std::uintptr_t target){
 using namespace mw34::m4_cmd_native;
 auto kernel=GetModuleHandleW(L"kernel32.dll");check(kernel,"Research pressure named kernel module");
 ApiIdentity a;a.target=target;a.named_target=reinterpret_cast<std::uintptr_t>(GetProcAddress(kernel,requested));
 check(a.named_target==target,"Research pressure imported and named API match");a.region=region(reinterpret_cast<void*>(target));a.owner=a.region.allocation;
 const char*alias=std::string_view(requested)=="HeapAlloc"?"RtlAllocateHeap":std::string_view(requested)=="HeapSize"?"RtlSizeHeap":requested;
 a.owner_named_target=reinterpret_cast<std::uintptr_t>(GetProcAddress(reinterpret_cast<HMODULE>(a.owner),alias));
 check(a.owner_named_target==target&&a.region.state==MEM_COMMIT&&a.region.type==MEM_IMAGE,
       "Research pressure executable actual owning API export");
 std::array<wchar_t,32768>path{};auto n=GetModuleFileNameW(reinterpret_cast<HMODULE>(a.owner),path.data(),path.size());
 check(n&&n<path.size(),"Research pressure physical owning module path");a.module_path.assign(path.data(),n);
 a.module_sha=mw34::m4::sha256(readfile(std::filesystem::path(a.module_path),16*1024*1024));return a;
}
inline void pressure_start(std::uint64_t heap){
 check(!pressure_heap&&pressure_rows.empty()&&heap,"Fresh exact research pressure heap");pressure_heap=reinterpret_cast<HANDLE>(heap);
 mw34::m4_nmx_integration::NumericHostBoundary hardware(0x37f);mw34::m4_spi_connected::ErrorBoundary error;
 pressure_before={pressure_identity("HeapAlloc",reinterpret_cast<std::uintptr_t>(&::HeapAlloc)),
                  pressure_identity("HeapSize",reinterpret_cast<std::uintptr_t>(&::HeapSize)),
                  pressure_identity("HeapFree",reinterpret_cast<std::uintptr_t>(&::HeapFree))};
 for(unsigned n=0;n<256;++n){
  SetLastError(0x4D573354);auto p=::HeapAlloc(pressure_heap,0,128);const auto allocation_error=GetLastError();
  check(p!=nullptr,"Actual bounded research pressure allocation succeeded");
  auto capacity=::HeapSize(pressure_heap,0,p);check(capacity>=128&&capacity<=4096,"Actual bounded research pressure capacity");
  pressure_rows.push_back({1,n,heap,128,reinterpret_cast<std::uintptr_t>(p),capacity,allocation_error,0,0,0,0,0});
 }
}
inline void pressure_release(){
 if(!pressure_heap)return;
 for(auto&row:pressure_rows){SetLastError(0x4D573354);row[7]=1;row[8]=::HeapFree(pressure_heap,0,reinterpret_cast<void*>(row[4]));row[9]=GetLastError();check(row[8],"Every actual research pressure block released once");}
 pressure_after={pressure_identity("HeapAlloc",reinterpret_cast<std::uintptr_t>(&::HeapAlloc)),
                 pressure_identity("HeapSize",reinterpret_cast<std::uintptr_t>(&::HeapSize)),
                 pressure_identity("HeapFree",reinterpret_cast<std::uintptr_t>(&::HeapFree))};
 check(pressure_before==pressure_after,"Actual research pressure API identities unchanged");pressure_heap=nullptr;
}
'''
derive('fixture_hooks_v3.hpp','fixture_hooks_v2.hpp',[
 ('struct Latest {',pressure+'\nstruct Latest {'),
 ('const bool sizing=site==0x780015B5,reallocating=site==0x78011C27;',
  'const bool sizing=site==0x780015B5,reallocating=site==0x78011C27;\n if(selected==9&&point==40&&reallocating&&!pressure_heap&&pressure_rows.empty())pressure_start(b.summary()[15]);')])
derive('fixture_v4.inc','fixture_v3.inc',[
 ('#include "fixture_hooks_v2.hpp"','#include "fixture_hooks_v3.hpp"'),
 ('t.c->registry().finish();t.cleanup_ok=',
  'mw34_onexit_review::pressure_release();t.c->registry().finish();t.cleanup_ok='),
 ('review_dump(c,w,prefix+"-cleaned/");',
  '''review_dump(c,w,prefix+"-cleaned/");
 if(!retry&&!mw34_onexit_review::pressure_rows.empty()){
  w.append(prefix+"-pressure.bin",std::as_bytes(std::span(mw34_onexit_review::pressure_rows)));
  for(unsigned k=0;k<3;++k)for(unsigned after=0;after<2;++after){
   const auto&a=(after?mw34_onexit_review::pressure_after:mw34_onexit_review::pressure_before)[k];
   const auto id=prefix+"-pressure-"+std::to_string(k)+(after?"-after":"-before");
   const std::array<std::uint64_t,11>v{a.target,a.named_target,a.owner,a.owner_named_target,a.region.base,a.region.bytes,a.region.allocation,a.region.state,a.region.type,a.region.protect,a.region.allocation_protect};
   w.append(id+".bin",std::as_bytes(std::span(v)));w.append(id+"-module-path.bin",std::as_bytes(std::span(a.module_path)));w.append(id+"-module-sha.bin",std::as_bytes(std::span(a.module_sha)));
  }
 }'''),
 ('mw34_onexit_review::owned_guest_aliases.clear();','mw34_onexit_review::owned_guest_aliases.clear();mw34_onexit_review::pressure_rows.clear();mw34_onexit_review::pressure_heap=nullptr;')])
derive('build_controls_v5.py','build_controls_v4.py',[
 ("fixture=pin(HERE/'fixture_v3.inc');hooks=pin(HERE/'fixture_hooks_v2.hpp')","fixture=pin(HERE/'fixture_v4.inc');hooks=pin(HERE/'fixture_hooks_v3.hpp')"),
 ("(out/'fixture_hooks_v2.hpp').write_bytes", "(out/'fixture_hooks_v3.hpp').write_bytes"),
 ("out/'fixture_hooks_v2.hpp'", "out/'fixture_hooks_v3.hpp'")])
derive('build_controls_v5.ps1','build_controls_v4.ps1',[("build_controls_v4.py","build_controls_v5.py")])
print('Derived fresh pressure control fixture and build script')
