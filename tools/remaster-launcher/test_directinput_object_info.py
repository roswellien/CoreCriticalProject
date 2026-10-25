"""Compile and exercise the actual native GetObjectInfo ABI handler with SDK layouts."""
from pathlib import Path
import argparse
import subprocess

HARNESS = r'''
#define DIRECTINPUT_VERSION 0x0700
#include <windows.h>
#include <dinput.h>
#include <array>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>
unsigned checks;
void require(bool condition){++checks;if(!condition)throw std::runtime_error("DirectInput query check failed");}
struct Address{unsigned value;};
struct Memory {
 std::array<unsigned char,1024> bytes;
 unsigned readable_end=1024,writable_end=1024;
 bool read(unsigned at,unsigned size){return at>=16&&at<=readable_end&&size<=readable_end-at;}
 bool write(unsigned at,unsigned size){return at>=16&&at<=writable_end&&size<=writable_end-at;}
 template<class T>void store(Address at,T value){require(write(at.value,sizeof(T)));std::memcpy(bytes.data()+at.value,&value,sizeof(T));}
};
struct Runtime{Memory data;Memory& memory(){return data;}};
struct Device {
 HRESULT result=DI_OK;unsigned calls{},object{},how{},size{};
 DIDEVICEOBJECTINSTANCEA expected{};
 HRESULT GetObjectInfo(DIDEVICEOBJECTINSTANCEA* out,DWORD id,DWORD flags){
  ++calls;object=id;how=flags;size=out->dwSize;
  std::memset(&expected,0x6d,sizeof(expected));expected.dwSize=size;
  expected.guidType={0x12345678,0x1234,0x5678,{1,2,3,4,5,6,7,8}};
  expected.dwOfs=0x24;expected.dwType=0x100001;expected.dwFlags=1;
  strcpy_s(expected.tszName,"Controller axis fixture");
  // Deliberately dirty the host output even on provider failure. No failed
  // provider output is allowed to overwrite the original guest bytes.
  std::memcpy(out,&expected,size);
  return result;
 }
};
struct Stage {
 Runtime runtime;Device device;Device* dv=&device;
 std::vector<std::string> apis{"IDirectInputDevice2A::GetObjectInfo"};
 std::array<unsigned,4> arguments{0x1234,128,0,0};
 unsigned result{},cleanup{};
 unsigned arg(unsigned i){return arguments.at(i);}
 bool readable(unsigned p,unsigned n){return runtime.memory().read(p,n);}
 bool writable(unsigned p,unsigned n){return runtime.memory().write(p,n);}
 unsigned load(unsigned p){require(readable(p,4));unsigned v;std::memcpy(&v,runtime.memory().bytes.data()+p,4);return v;}
 [[noreturn]]void deny(const char*,unsigned){throw std::runtime_error("Denied invalid guest output");}
 void* done(unsigned hr,unsigned count){result=hr;cleanup=count;return this;}
 void* call(){std::string n="GetObjectInfo";
HANDLER
 throw std::runtime_error("Query handler not reached");
 }
 Stage(unsigned size){runtime.data.bytes.fill(0xa5);runtime.data.store<unsigned>({128},size);}
};
int main(){
 static_assert(sizeof(DIDEVICEOBJECTINSTANCEA)==316&&sizeof(DIDEVICEOBJECTINSTANCE_DX3A)==292);
 for(unsigned size:{292U,316U})for(unsigned how:{unsigned(DIPH_BYOFFSET),unsigned(DIPH_BYID),unsigned(DIPH_BYUSAGE),0xdeadbeefU})
 for(HRESULT hr:{HRESULT(DI_OK),HRESULT(DIERR_OBJECTNOTFOUND),HRESULT(DIERR_INVALIDPARAM),HRESULT(E_POINTER)}){
  Stage stage(size);auto saved=stage.runtime.data.bytes;
  stage.arguments[2]=0x27;stage.arguments[3]=how;stage.device.result=hr;
  stage.call();require(stage.cleanup==4&&stage.result==unsigned(hr));
  require(stage.device.calls==1&&stage.device.size==size&&stage.device.object==0x27&&stage.device.how==how);
  if(SUCCEEDED(hr)){
   require(!std::memcmp(stage.runtime.data.bytes.data()+128,&stage.device.expected,size));
   for(unsigned i=0;i<stage.runtime.data.bytes.size();++i)
    if(i<128||i>=128+size)require(stage.runtime.data.bytes[i]==saved[i]);
  }else require(stage.runtime.data.bytes==saved);
 }
 for(unsigned size:{0U,1U,16U,291U,293U,315U,317U,0xffffffffU}){
  Stage stage(size);auto saved=stage.runtime.data.bytes;bool denied=false;
  try{stage.call();}catch(const std::runtime_error&){denied=true;}
  require(denied&&stage.device.calls==0&&stage.runtime.data.bytes==saved);
 }
 for(unsigned at:{0U,1022U,0xfffffff0U}){
  Stage stage(316);stage.arguments[1]=at;auto saved=stage.runtime.data.bytes;bool denied=false;
  try{stage.call();}catch(const std::runtime_error&){denied=true;}
  require(denied&&stage.device.calls==0&&stage.runtime.data.bytes==saved);
 }
 for(unsigned size:{292U,316U}){
  Stage stage(size);stage.runtime.data.writable_end=128+size-1;
  auto saved=stage.runtime.data.bytes;bool denied=false;
  try{stage.call();}catch(const std::runtime_error&){denied=true;}
  require(denied&&stage.device.calls==0&&stage.runtime.data.bytes==saved);
 }
 std::printf("%u actual DirectInput query layout, bounds, HRESULT, canary and stack-cleanup checks passed\n",checks);
}
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-source',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--compiler',required=True,type=Path)
    args=parser.parse_args()
    source=(args.host_source/'mfc_stage.hpp').read_text(encoding='utf-8')
    begin=source.index('    if(n=="GetObjectInfo")')
    end=source.index('    if(n=="GetDeviceInfo")',begin)
    from apply_directinput_object_info import HANDLER
    if source[begin:end]!=HANDLER:
        raise ValueError('Test must exercise the maintained handler verbatim')
    cpp=args.output/'directinput-query-checks.cpp';exe=args.output/'directinput-query-checks.exe'
    cpp.write_text(HARNESS.replace('HANDLER',source[begin:end]),encoding='utf-8')
    command=[str(args.compiler),'/nologo','/std:c++20','/O2','/EHsc','/MD',str(cpp),
             '/Fe'+str(exe),'/Fo'+str(args.output/'directinput-query-checks.obj')]
    result=subprocess.run(command,text=True,capture_output=True)
    (args.output/'query-check-build.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    result.check_returncode()
    subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
