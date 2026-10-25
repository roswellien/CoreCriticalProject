"""Exercise the actual ensure() method against allocation/map failures without a GPU."""
from pathlib import Path
import argparse, subprocess


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--compiler',required=True)
    p.add_argument('--vulkan-headers',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(exist_ok=True,parents=True)
    s=(a.host_source/'vk_scene.hpp').read_text(encoding='utf-8')
    begin=s.index('    void ensure(Buffer &b, VkDeviceSize size, VkBufferUsageFlags usage, bool reserve_hint = true) {')
    end=s.index('    // A cached immutable device-local model buffer',begin)
    method=s[begin:end]
    harness=r'''
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan_core.h>
#include "buffer_reserve.hpp"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <stdexcept>
#include <vector>
unsigned checks{};
void require(bool ok){++checks;if(!ok)throw std::runtime_error("Buffer capacity/fallback check failed");}
struct Mock {
    struct Buffer {VkBuffer buffer{};VkDeviceMemory memory{};VkDeviceSize size{};void* mapped{};};
    VkDevice device{};unsigned long long presents{};
    struct Fns {
        unsigned long long serial=1;
        unsigned fail_at{};VkResult failure=VK_ERROR_OUT_OF_DEVICE_MEMORY;
        std::map<VkBuffer,VkDeviceSize> buffers;
        std::map<VkDeviceMemory,std::vector<unsigned char>> memories;
        std::vector<VkDeviceSize> sizes;
        VkResult result(unsigned point){if(fail_at==point){fail_at=0;return failure;}return VK_SUCCESS;}
        VkResult vkCreateBuffer(VkDevice,const VkBufferCreateInfo* info,const void*,VkBuffer* out){
            sizes.push_back(info->size);const auto r=result(1);if(r!=VK_SUCCESS){*out={};return r;}
            *out=reinterpret_cast<VkBuffer>(++serial);buffers[*out]=info->size;return r;
        }
        void vkDestroyBuffer(VkDevice,VkBuffer b,const void*){require(buffers.erase(b)==1);}
        void vkGetBufferMemoryRequirements(VkDevice,VkBuffer b,VkMemoryRequirements* r){r->size=buffers.at(b);r->alignment=1;r->memoryTypeBits=1;}
        VkResult vkAllocateMemory(VkDevice,const VkMemoryAllocateInfo* info,const void*,VkDeviceMemory* out){
            const auto r=result(2);if(r!=VK_SUCCESS){*out={};return r;}
            *out=reinterpret_cast<VkDeviceMemory>(++serial);memories[*out].resize(std::size_t(info->allocationSize));return r;
        }
        void vkFreeMemory(VkDevice,VkDeviceMemory m,const void*){require(memories.erase(m)==1);}
        VkResult vkBindBufferMemory(VkDevice,VkBuffer,VkDeviceMemory,VkDeviceSize){return result(3);}
        VkResult vkMapMemory(VkDevice,VkDeviceMemory m,VkDeviceSize,VkDeviceSize,unsigned,void** out){
            const auto r=result(4);*out=r==VK_SUCCESS?memories.at(m).data():nullptr;return r;
        }
    } f;
    static void check(VkResult result,const char*){if(result!=VK_SUCCESS)throw std::runtime_error("Visible Vulkan failure");}
    static bool has_type(const VkMemoryRequirements&,VkMemoryPropertyFlags){return false;}
    static unsigned type(const VkMemoryRequirements&,VkMemoryPropertyFlags){return 0;}
    void release(Buffer& b){if(b.buffer)f.vkDestroyBuffer(device,b.buffer,nullptr);if(b.memory)f.vkFreeMemory(device,b.memory,nullptr);b={};}
__ENSURE__
};
int main(){
    _putenv_s("MW34_BUFFER_RESERVE","1");
    using mw34::allocation::stream_capacity;
    for(std::uint64_t n=0;n<20000000;n+=97){
        const auto capacity=stream_capacity(n);require(capacity>=n);require(capacity-n<65536);
        if(n<16*1024*1024)require(capacity%65536==0);else require(capacity==n);
    }
    require(stream_capacity(~std::uint64_t{})==~std::uint64_t{});
    Mock h;Mock::Buffer b;
    h.ensure(b,96,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);require(b.size==96);require(h.f.sizes.size()==1);
    h.ensure(b,97,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);require(b.size==65536);require(h.f.sizes.size()==2);
    h.ensure(b,65536,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);require(h.f.sizes.size()==2);
    h.ensure(b,65537,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);require(b.size==131072);h.release(b);
    Mock exact;Mock::Buffer e;
    exact.ensure(e,96,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,false);
    exact.ensure(e,97,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT,false);require(e.size==97);exact.release(e);
    for(unsigned point=1;point<=4;++point)for(auto error:{VK_ERROR_OUT_OF_DEVICE_MEMORY,VK_ERROR_OUT_OF_HOST_MEMORY}){
        Mock test;Mock::Buffer v;test.ensure(v,96,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);
        test.f.fail_at=point;test.f.failure=error;test.ensure(v,97,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);
        require(v.size==97);require(test.f.sizes==std::vector<VkDeviceSize>{96,65536,97});
        require(test.f.buffers.size()==1);require(test.f.memories.size()==1);require(v.mapped!=nullptr);test.release(v);
    }
    Mock mapping;Mock::Buffer m;mapping.ensure(m,96,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);
    mapping.f.fail_at=4;mapping.f.failure=VK_ERROR_MEMORY_MAP_FAILED;mapping.ensure(m,97,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);
    require(m.size==97);require(mapping.f.buffers.size()==1);require(mapping.f.memories.size()==1);mapping.release(m);
    for(unsigned point=1;point<=4;++point){
        Mock test;Mock::Buffer v;test.ensure(v,96,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);
        test.f.fail_at=point;test.f.failure=VK_ERROR_DEVICE_LOST;bool threw=false;
        try{test.ensure(v,97,VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);}catch(const std::runtime_error&){threw=true;}
        require(threw);require(test.f.sizes.size()==2);test.release(v);
    }
    std::printf("%u actual buffer growth, bounded reserve, exact fallback and visible-error checks passed\n",checks);
}
'''.replace('__ENSURE__',method)
    source=a.output/'buffer-reserve-checks.cpp';source.write_text(harness,encoding='utf-8')
    exe=a.output/'buffer-reserve-checks.exe'
    command=[a.compiler,'/nologo','/std:c++20','/O2','/EHsc','/MD','/I'+str(a.host_source),'/I'+str(a.vulkan_headers),str(source),'/Fe'+str(exe),'/Fo'+str(a.output/'buffer-reserve-checks.obj')]
    result=subprocess.run(command,text=True,capture_output=True)
    (a.output/'buffer-reserve-build.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError('Buffer fixture compile failed; see '+str(a.output/'buffer-reserve-build.log'))
    subprocess.run([str(exe)],check=True)


if __name__=='__main__':main()
