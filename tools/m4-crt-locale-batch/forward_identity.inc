// Native PE export identity proof. This executes no original provider body.
struct ExportEntry {unsigned rva{};std::string forward;};
ExportEntry native_export(std::span<const std::byte>b,const std::string&name){
 auto word=[&](unsigned p){if(std::uint64_t(p)+2>b.size())throw std::invalid_argument("Native PE word bounds");unsigned short v{};std::memcpy(&v,b.data()+p,2);return v;};
 auto dword=[&](unsigned p){if(std::uint64_t(p)+4>b.size())throw std::invalid_argument("Native PE DWORD bounds");unsigned v{};std::memcpy(&v,b.data()+p,4);return v;};
 if(word(0)!=0x5a4d)throw std::invalid_argument("Native DOS image required");const auto pe=dword(0x3c),opt=pe+24;
 if(dword(pe)!=0x4550||word(pe+4)!=0x8664||word(opt)!=0x20b)throw std::invalid_argument("Native AMD64 PE export required");
 auto offset=[&](unsigned rva,unsigned size){unsigned matches{},result{};for(unsigned n=0;n<word(pe+6);++n){const auto p=opt+word(pe+20)+n*40,va=dword(p+12),rs=dword(p+16),rp=dword(p+20);if(rva>=va&&std::uint64_t(rva)+size<=std::uint64_t(va)+rs){result=rp+rva-va;++matches;}}if(matches!=1||std::uint64_t(result)+size>b.size())throw std::invalid_argument("Native export raw RVA bounds");return result;};
 auto text=[&](unsigned rva){const auto p=offset(rva,1);std::string s;for(unsigned n=0;n<4096;++n){if(p+n>=b.size())throw std::invalid_argument("Native export text bounds");const auto c=std::to_integer<unsigned char>(b[p+n]);if(!c)return s;s.push_back(static_cast<char>(c));}throw std::invalid_argument("Native terminated export text required");};
 const auto dir=dword(opt+112),size=dword(opt+116),p=offset(dir,40),functions=dword(p+20),names=dword(p+24),fn=dword(p+28),np=dword(p+32),ord=dword(p+36);
 if(!functions||!names||names>65536||functions>65536)throw std::invalid_argument("Bounded native export arrays required");
 unsigned matches{};ExportEntry result;for(unsigned n=0;n<names;++n){if(text(dword(offset(np+4*n,4)))!=name)continue;const auto index=word(offset(ord+2*n,2));if(index>=functions)throw std::invalid_argument("Native named ordinal bounds");result.rva=dword(offset(fn+4*index,4));if(result.rva>=dir&&std::uint64_t(result.rva)<std::uint64_t(dir)+size)result.forward=text(result.rva);++matches;}
 if(matches!=1||!result.rva)throw std::invalid_argument("Unique actual native named export required");return result;
}
NativeExportProof prove_native_export(const char*requested,std::uintptr_t actual,const m4_cmd_native::ApiIdentity&a){
 NativeExportProof proof;auto kernel=GetModuleHandleW(L"kernel32.dll");if(!kernel)throw std::runtime_error("Actual named native import module required");
 auto path=[&](HMODULE module){std::array<wchar_t,1024>b{};const auto n=GetModuleFileNameW(module,b.data(),static_cast<DWORD>(b.size()));if(!n||n>=b.size())throw std::runtime_error("Bounded actual native module path required");return std::wstring(b.data(),n);};
 const auto named_path=path(kernel),owner_path=path(reinterpret_cast<HMODULE>(a.owner));const auto named_bytes=m4_cmd_native::readfile(named_path,16*1024*1024),owner_bytes=m4_cmd_native::readfile(owner_path,16*1024*1024);
 const auto named=native_export(named_bytes,requested);const auto resolved=reinterpret_cast<std::uintptr_t>(GetProcAddress(kernel,requested));if(resolved!=actual)throw std::runtime_error("Actual imported named native export required");
 std::string alias=requested;if(named.forward.empty()){if(a.owner!=reinterpret_cast<std::uintptr_t>(kernel)||reinterpret_cast<std::uintptr_t>(kernel)+named.rva!=actual)throw std::runtime_error("Exact direct named native export owner/RVA required");}
 else{
  const std::array<std::pair<const char*,const char*>,5>allowed{{{"HeapAlloc","RtlAllocateHeap"},{"InitializeCriticalSection","RtlInitializeCriticalSection"},{"EnterCriticalSection","RtlEnterCriticalSection"},{"LeaveCriticalSection","RtlLeaveCriticalSection"},{"DeleteCriticalSection","RtlDeleteCriticalSection"}}};
  auto match=std::find_if(allowed.begin(),allowed.end(),[&](auto x){return std::string(requested)==x.first;});
  if(match==allowed.end()||named.forward!=std::string("NTDLL.")+match->second||a.owner!=reinterpret_cast<std::uintptr_t>(GetModuleHandleW(L"ntdll.dll")))throw std::runtime_error("Exact admitted actual native critical-section/allocator PE forwarder chain required");alias=match->second;
 }
 const auto owner=native_export(owner_bytes,alias);const auto owner_resolved=reinterpret_cast<std::uintptr_t>(GetProcAddress(reinterpret_cast<HMODULE>(a.owner),alias.c_str()));
 if(!owner.forward.empty()||a.owner+owner.rva!=actual||owner_resolved!=actual)throw std::runtime_error("Exact actual owner alias export RVA required");
 auto copy=[](auto&dst,const auto&src){if(src.size()>=dst.size())throw std::invalid_argument("Native identity field bounds");std::copy(src.begin(),src.end(),dst.begin());};
 proof.scalar={1,reinterpret_cast<std::uintptr_t>(kernel),actual,resolved,a.owner,owner_resolved};copy(proof.requested,std::string(requested));copy(proof.forwarder,named.forward);copy(proof.owner_export,alias);copy(proof.named_path,named_path);copy(proof.owner_path,owner_path);
 const auto named_sha=m4::sha256(named_bytes),owner_sha=m4::sha256(owner_bytes);if(named_sha.size()!=64||owner_sha.size()!=64)throw std::runtime_error("Native module digest bounds");std::copy(named_sha.begin(),named_sha.end(),proof.named_sha.begin());std::copy(owner_sha.begin(),owner_sha.end(),proof.owner_sha.begin());return proof;
}
