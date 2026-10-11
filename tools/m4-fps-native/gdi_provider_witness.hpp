// Read-only actual target observations surrounding the real owned GDI call.
// Included inside mw34::m4_widget_native. No source State/CPU/FX is populated.
template<class Emit>static void observe_gdi_identity(unsigned serial,unsigned kind,void*target,const char*side,Emit emit){
 require(kind<3&&target,"Exact current real GDI target");
 HMODULE owner{};require(GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<const char*>(target),&owner),"Actual native GDI owning image");
 MEMORY_BASIC_INFORMATION mbi{};require(VirtualQuery(target,&mbi,sizeof(mbi))==sizeof(mbi)&&mbi.AllocationBase==owner&&mbi.Type==MEM_IMAGE&&mbi.State==MEM_COMMIT,"Actual current GDI committed owning image");
 const auto address=reinterpret_cast<std::uintptr_t>(target),base=reinterpret_cast<std::uintptr_t>(mbi.BaseAddress);const auto protection=mbi.Protect&255;
 require(base<=address&&address+64>=address&&address+64<=base+mbi.RegionSize&&(protection==PAGE_EXECUTE||protection==PAGE_EXECUTE_READ||protection==PAGE_EXECUTE_READWRITE||protection==PAGE_EXECUTE_WRITECOPY)&&!(mbi.Protect&PAGE_GUARD),"Whole actual GDI entry64 executable image extent");
 char path[32768]{};const auto length=GetModuleFileNameA(owner,path,sizeof(path));require(length&&length<sizeof(path),"Complete current GDI owning image path");
 std::ifstream file(path,std::ios::binary|std::ios::ate);require(file.good(),"Actual current GDI physical owning file");const auto n=file.tellg();require(n>0&&n<=64*1024*1024,"Finite complete native GDI image bytes");std::vector<std::byte>bytes(static_cast<std::size_t>(n));file.seekg(0);file.read(reinterpret_cast<char*>(bytes.data()),n);require(file.good(),"Whole actual GDI owning file read");const auto digest=mw34::m4::sha256(bytes);
 const auto prefix="GDI-provider/"+std::to_string(serial)+"/"+side;const std::array<std::uint64_t,9>w{1,kind,address,reinterpret_cast<std::uintptr_t>(owner),base,mbi.RegionSize,mbi.State,mbi.Protect,mbi.Type};
 emit(prefix+"-identity.bin",w.data(),sizeof(w));emit(prefix+"-path.txt",path,length);emit(prefix+"-sha256.txt",digest.data(),digest.size());emit(prefix+"-entry64.bin",target,64);
}
