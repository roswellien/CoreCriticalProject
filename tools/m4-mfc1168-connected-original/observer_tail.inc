static_assert(sizeof(Boundary)==664&&sizeof(NamedBoundary)==668);
struct ConnectedPatch {unsigned pc,size;void(*target)();unsigned char raw[9];};
static const std::array<ConnectedPatch,5> connected_patches{{
 {0x5ae3a8,5,&mfc_enter_hook,{0xe8,0x23,0xdb,0xff,0xff}},
 {0x5ae3ad,8,&mfc_return_hook,{0x8b,0x4c,0x24,0x04,0x8b,0x54,0x24,0x08}},
 {0x5ae3b7,9,&field_hook,{0x88,0x48,0x14,0x89,0x90,0x40,0x10,0,0}},
 {0x5ae3c4,6,&mbcp_enter_hook,{0xff,0x15,0x74,0xb6,0x5b,0}},
 {0x5ae3ca,7,&mbcp_return_hook,{0x59,0x6a,1,0x58,0xc2,8,0}}
}};
static void connected_patch_sources(bool install){
 // Validate every current physical source byte before installing any patch.
 if(install)for(const auto&b:connected_patches)require(!std::memcmp(reinterpret_cast<void*>(b.pc),b.raw,b.size),"Exact current MFC boundary source before any patch");
 for(const auto&b:connected_patches){DWORD old{},ignored{};auto*p=reinterpret_cast<unsigned char*>(b.pc);require(VirtualProtect(p,b.size,PAGE_EXECUTE_READWRITE,&old),"Current MFC boundary protect");if(install){p[0]=0xe9;const auto delta=reinterpret_cast<unsigned>(b.target)-b.pc-5;std::memcpy(p+1,&delta,4);for(unsigned n=5;n<b.size;++n)p[n]=0x90;}else std::memcpy(p,b.raw,b.size);require(FlushInstructionCache(GetCurrentProcess(),p,b.size)&&VirtualProtect(p,b.size,old,&ignored),"Current MFC boundary restore protection");}
}
static void connected_named_identity(){
 for(unsigned i=0;i<4;++i){named_targets[i]=dword(named_cells[i]);const auto expected=GetProcAddress(GetModuleHandleW(L"kernel32.dll"),named_names[i]);require(reinterpret_cast<unsigned>(expected)==named_targets[i],"Actual current named export and owning IAT identity");HMODULE owner_module{};require(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(expected),&owner_module),"Current named API physical owner");std::array<wchar_t,32768>path{};require(GetModuleFileNameW(owner_module,path.data(),path.size())>0,"Current named API owner path");const auto filename=std::filesystem::path(path.data()).string();dump("named-API/"+std::to_string(i)+"-path.txt",filename.data(),filename.size());const auto file=read(filename.c_str(),32<<20);const auto hash=sha256(file);dump("named-API/"+std::to_string(i)+"-sha256.txt",hash.data(),hash.size());dump("named-API/"+std::to_string(i)+"-entry64.bin",reinterpret_cast<void*>(named_targets[i]),64);MEMORY_BASIC_INFORMATION region{};require(VirtualQuery(expected,&region,sizeof(region))==sizeof(region),"Current named API target region");const std::array<unsigned,8>meta{reinterpret_cast<unsigned>(owner_module),named_targets[i],reinterpret_cast<unsigned>(region.BaseAddress),static_cast<unsigned>(region.RegionSize),region.State,region.Protect,region.Type,reinterpret_cast<unsigned>(region.AllocationBase)};dump("named-API/"+std::to_string(i)+"-owner-metadata.bin",meta.data(),sizeof(meta));}
 dump("named-API/targets.bin",named_targets,sizeof(named_targets));
}
static void connected_lock(const std::string&stem){const unsigned cell=0x7803708c,pointer=dword(cell);const std::array<unsigned,4>meta{cell,pointer,24,pointer?1U:0U};dump(stem+"/meta.bin",meta.data(),sizeof(meta));if(pointer){unsigned char bytes[24]{};require(safe_read(reinterpret_cast<void*>(pointer),bytes,24),"Actual current codepage lock24B readable");dump(stem+"/bytes.bin",bytes,24);}}
