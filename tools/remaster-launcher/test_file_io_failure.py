"""Compile the actual file-I/O handler against Win32 in a small guest-memory harness.

Run in the Visual Studio developer environment with --compiler PATH_TO_CLANG_CL.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler', required=True)
    parser.add_argument('--source', type=Path, default=Path(__file__).parent / 'native-overrides/mfc_stage.hpp')
    args = parser.parse_args()
    text = args.source.read_text()
    handler = text[text.index('  if(n=="ReadFile"||n=="WriteFile")'):text.index('  if(n=="SetFilePointer")')]
    last_error = text[text.index(' struct LastError{'):text.index('\n', text.index(' struct LastError{'))]
    code = r'''
#include <windows.h>
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>
#include <cstdio>
struct Address { unsigned value; };
struct Memory {
    std::array<unsigned char,512> bytes{};
    template<class T>T load(Address a){T x;std::memcpy(&x,bytes.data()+a.value,sizeof x);return x;}
    template<class T>void store(Address a,T x){std::memcpy(bytes.data()+a.value,&x,sizeof x);}
};
struct Runtime {Memory mem;Memory& memory(){return mem;}};
struct Host {DWORD last_error{};std::vector<unsigned> files;};
struct Harness {
    Host host;Runtime runtime;std::array<unsigned,5> argv{};
    LAST_ERROR
    bool readable(unsigned a,unsigned z){return uint64_t(a)+z<=512;}
    bool writable(unsigned a,unsigned z){return readable(a,z);}
    void store(unsigned a,unsigned v){std::memcpy(runtime.mem.bytes.data()+a,&v,4);}
    [[noreturn]] void deny(const std::string& why,unsigned){throw std::runtime_error(why);}
    unsigned call(const std::string& n){
        auto arg=[&](unsigned i){return argv.at(i);};
        auto owned_file=[&](unsigned h){return std::find(host.files.begin(),host.files.end(),h)!=host.files.end();};
        auto hhandle=[](unsigned h){return reinterpret_cast<HANDLE>(intptr_t(int32_t(h)));};
        auto done=[](unsigned eax,unsigned nargs){if(nargs!=5)throw std::runtime_error("wrong ABI arity");return eax;};
        HANDLER
        throw std::runtime_error("unexpected service");
    }
};
void check(bool value,const char* why){if(!value)throw std::runtime_error(why);}
int main(){try{
    Harness h;h.runtime.mem.bytes.fill(0x5a);
    for(auto name:{"ReadFile","WriteFile"})for(unsigned handle:{0xffffffffU,0U}){
        h.argv={handle,32,4,16,0};h.store(16,99);SetLastError(0x1234);
        check(h.call(name)==0,"invalid handle must fail");
        check(h.host.last_error==ERROR_INVALID_HANDLE,"guest LastError must be invalid handle");
        check(GetLastError()==0x1234,"host LastError must be restored");
        check(h.runtime.mem.load<unsigned>({16})==0,"failed I/O byte count must be zero");
        check(h.runtime.mem.bytes[32]==0x5a,"failed read must not replace guest bytes");
    }
    h.argv={0x12345678,32,4,16,0};bool denied=false;
    try{h.call("ReadFile");}catch(const std::runtime_error&){denied=true;}
    check(denied,"arbitrary unowned handle must remain rejected");
    HANDLE f=CreateFileA("roundtrip.bin",GENERIC_READ|GENERIC_WRITE,0,nullptr,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
    check(f!=INVALID_HANDLE_VALUE,"test file create");unsigned token=unsigned(reinterpret_cast<uintptr_t>(f));h.host.files.push_back(token);
    h.argv={token,32,4,16,0};check(h.call("WriteFile")==1,"owned write");
    check(h.runtime.mem.load<unsigned>({16})==4,"owned write count");
    SetFilePointer(f,0,nullptr,FILE_BEGIN);h.runtime.mem.bytes[32]=0;
    check(h.call("ReadFile")==1,"owned read");check(h.runtime.mem.bytes[32]==0x5a,"owned read bytes");CloseHandle(f);
    std::puts("PASS: failed-open I/O returns real Win32 errors; guest buffer/count and host LastError preserved; owned I/O and ownership guards retained.");return 0;
}catch(const std::exception& e){std::fprintf(stderr,"FAIL: %s\n",e.what());return 1;}}
'''.replace('HANDLER', handler).replace('LAST_ERROR', last_error)
    with tempfile.TemporaryDirectory(prefix='mw34-file-io-') as temp:
        folder = Path(temp)
        source = folder / 'test.cpp'
        source.write_text(code)
        exe = folder / 'test.exe'
        subprocess.run([args.compiler, '/std:c++20', '/EHsc', str(source), '/Fe:' + str(exe)], cwd=folder, check=True)
        subprocess.run([str(exe)], cwd=folder, check=True)


if __name__ == '__main__':
    main()
