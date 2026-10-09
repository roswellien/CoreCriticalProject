// Original x86 reference bootstrap: reserve exact guest regions before child CRT.
// This never supplies code/results and never runs an unadmitted guest entry.
#pragma once
#include <windows.h>
#include <array>
#include <cstdint>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace mw34::original_broker {
inline constexpr std::array<std::uint32_t,5> bases{0x480000,0x5b0000,0x5e0000,0x600000,0x20000000};
inline constexpr std::size_t reservation_size=65536;
inline constexpr DWORD deadline_ms=180000;
inline bool adopting{};

inline void require(bool ok,const std::string &reason) {
    if(!ok)throw std::runtime_error(reason+" Win32="+std::to_string(GetLastError()));
}
struct Handle {
    HANDLE value{};
    Handle()=default;
    explicit Handle(HANDLE h):value(h){}
    ~Handle(){if(value&&value!=INVALID_HANDLE_VALUE)CloseHandle(value);}
    Handle(const Handle&)=delete;Handle&operator=(const Handle&)=delete;
};
inline void diagnostic(std::uint32_t base) {
    MEMORY_BASIC_INFORMATION info{};
    require(VirtualQuery(reinterpret_cast<void *>(static_cast<std::uintptr_t>(base)),&info,sizeof(info))==sizeof(info),"Broker VirtualQuery failed");
    std::cerr<<"Original broker parent mapping: queried="<<base
      <<" allocation_base="<<reinterpret_cast<std::uintptr_t>(info.AllocationBase)
      <<" region_base="<<reinterpret_cast<std::uintptr_t>(info.BaseAddress)
      <<" region_bytes="<<info.RegionSize<<" state="<<info.State<<" type="<<info.Type
      <<" protect="<<info.Protect<<" allocation_protect="<<info.AllocationProtect<<'\n';
}
inline void validate_reserved(std::uint32_t base) {
    MEMORY_BASIC_INFORMATION info{};
    const auto pointer=reinterpret_cast<void *>(static_cast<std::uintptr_t>(base));
    require(VirtualQuery(pointer,&info,sizeof(info))==sizeof(info)&&info.AllocationBase==pointer&&
            info.BaseAddress==pointer&&info.RegionSize==reservation_size&&info.State==MEM_RESERVE&&
            info.Type==MEM_PRIVATE&&info.AllocationProtect==PAGE_NOACCESS,
            "Internal child lacks exact broker NOACCESS reservation base="+std::to_string(base));
}
inline void *reserve_or_adopt(std::uint32_t address) {
    const auto base=address&~0xffffU;
    bool reviewed{};for(const auto admitted:bases)reviewed|=admitted==base;
    require(reviewed,"Unreviewed original reservation region");
    const auto pointer=reinterpret_cast<void *>(static_cast<std::uintptr_t>(base));
    if(adopting){validate_reserved(base);return pointer;}
    // Reference body execution is always brokered. This explicit failure also
    // prevents a caller from silently reintroducing an in-process fallback.
    throw std::runtime_error("Original execution requires pre-CRT broker reservations");
}
inline std::wstring child_command() {
    std::array<wchar_t,32768> executable{};
    const auto length=GetModuleFileNameW(nullptr,executable.data(),static_cast<DWORD>(executable.size()));
    require(length>0&&length<executable.size(),"Broker executable path unavailable/truncated");
    const std::wstring_view original=GetCommandLineW();
    std::size_t end{};
    while(end<original.size()&&(original[end]==L' '||original[end]==L'\t'))++end;
    if(end<original.size()&&original[end]==L'"'){
        end=original.find(L'"',end+1);require(end!=std::wstring_view::npos,"Malformed executable command line");++end;
    }else{
        while(end<original.size()&&original[end]!=L' '&&original[end]!=L'\t')++end;
    }
    // Only the executable token is replaced; the OS-supplied raw argument tail
    // remains byte-for-byte Unicode. No shell or text-built file operation.
    return L'"'+std::wstring(executable.data(),length)+L"\" --pre-reserved"+std::wstring(original.substr(end));
}
inline std::optional<int> dispatch(int &argc,char **argv,unsigned expected_argc) {
    if(argc>1&&std::string_view(argv[1])=="--pre-reserved"){
        require(argc==static_cast<int>(expected_argc)+1,"Internal broker child argument count differs");
        for(const auto base:bases)validate_reserved(base);
        adopting=true;
        for(int i=1;i+1<argc;++i)argv[i]=argv[i+1];
        --argc;argv[argc]=nullptr;
        return std::nullopt;
    }
    if(argc!=static_cast<int>(expected_argc))return std::nullopt;
    diagnostic(bases[0]);
    Handle job(CreateJobObjectW(nullptr,nullptr));require(job.value!=nullptr,"Broker job creation failed");
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
    limits.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    require(SetInformationJobObject(job.value,JobObjectExtendedLimitInformation,&limits,sizeof(limits)),"Broker KILL_ON_CLOSE job setup failed");
    std::array<Handle,3> inherited;
    const std::array<DWORD,3> std_names{STD_INPUT_HANDLE,STD_OUTPUT_HANDLE,STD_ERROR_HANDLE};
    std::array<HANDLE,3> standard{};
    for(unsigned i=0;i<3;++i){
        const auto source=GetStdHandle(std_names[i]);
        require(source&&source!=INVALID_HANDLE_VALUE,"Broker standard handle unavailable");
        require(DuplicateHandle(GetCurrentProcess(),source,GetCurrentProcess(),&inherited[i].value,0,TRUE,DUPLICATE_SAME_ACCESS),"Broker standard handle duplication failed");
        standard[i]=inherited[i].value;
    }
    SIZE_T bytes{};InitializeProcThreadAttributeList(nullptr,1,0,&bytes);
    require(bytes!=0,"Broker handle-list size unavailable");
    std::vector<std::uint8_t> attributes(bytes);
    auto *list=reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(attributes.data());
    require(InitializeProcThreadAttributeList(list,1,0,&bytes),"Broker handle-list initialization failed");
    struct Attributes {LPPROC_THREAD_ATTRIBUTE_LIST value;~Attributes(){DeleteProcThreadAttributeList(value);}} cleanup{list};
    require(UpdateProcThreadAttribute(list,0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,standard.data(),sizeof(standard),nullptr,nullptr),"Broker explicit handle inheritance failed");
    STARTUPINFOEXW startup{};startup.StartupInfo.cb=sizeof(startup);startup.lpAttributeList=list;
    startup.StartupInfo.dwFlags=STARTF_USESTDHANDLES;
    startup.StartupInfo.hStdInput=standard[0];startup.StartupInfo.hStdOutput=standard[1];startup.StartupInfo.hStdError=standard[2];
    PROCESS_INFORMATION process{};
    auto command=child_command();
    std::array<wchar_t,32768> executable{};
    require(GetModuleFileNameW(nullptr,executable.data(),static_cast<DWORD>(executable.size()))>0,"Broker executable path unavailable");
    require(CreateProcessW(executable.data(),command.data(),nullptr,nullptr,TRUE,
            CREATE_SUSPENDED|CREATE_NO_WINDOW|EXTENDED_STARTUPINFO_PRESENT,nullptr,nullptr,&startup.StartupInfo,&process),"Suspended original child creation failed");
    Handle child(process.hProcess),thread(process.hThread);
    // Even assignment failure must terminate the suspended child; it has not
    // executed CRT, private code, or worker input at this point.
    if(!AssignProcessToJobObject(job.value,child.value)){
        const auto error=GetLastError();TerminateProcess(child.value,1);
        throw std::runtime_error("Original child job assignment failed Win32="+std::to_string(error));
    }
    for(const auto base:bases){
        const auto pointer=reinterpret_cast<void *>(static_cast<std::uintptr_t>(base));
        require(VirtualAllocEx(child.value,pointer,reservation_size,MEM_RESERVE,PAGE_NOACCESS)==pointer,
                "Pre-CRT guest reservation failed base="+std::to_string(base));
        MEMORY_BASIC_INFORMATION info{};
        require(VirtualQueryEx(child.value,pointer,&info,sizeof(info))==sizeof(info)&&
                info.AllocationBase==pointer&&info.BaseAddress==pointer&&info.RegionSize==reservation_size&&
                info.State==MEM_RESERVE&&info.Type==MEM_PRIVATE&&info.AllocationProtect==PAGE_NOACCESS,
                "Pre-CRT reservation proof failed");
    }
    require(ResumeThread(thread.value)!=static_cast<DWORD>(-1),"Original child resume failed");
    const auto waited=WaitForSingleObject(child.value,deadline_ms);
    if(waited!=WAIT_OBJECT_0){
        TerminateJobObject(job.value,1);WaitForSingleObject(child.value,5000);
        throw std::runtime_error(waited==WAIT_TIMEOUT?"Original broker execution deadline exceeded":"Original broker wait failed");
    }
    DWORD exit{};require(GetExitCodeProcess(child.value,&exit)&&exit!=STILL_ACTIVE,"Original child exit unavailable");
    std::cerr<<"Original broker child finished: pid="<<process.dwProcessId<<" exit="<<exit<<'\n';
    return static_cast<int>(exit);
}
} // namespace mw34::original_broker
