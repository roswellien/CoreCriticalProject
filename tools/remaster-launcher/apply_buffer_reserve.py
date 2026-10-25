"""Bounded small-buffer capacity reuse with exact-size fallback on allocation failure."""
from pathlib import Path
import argparse


def apply(host):
    p=host/'vk_scene.hpp';s=p.read_text(encoding='utf-8')
    helper=Path(__file__).parent/'native-overrides/buffer_reserve.hpp'
    if '#include "buffer_reserve.hpp"' in s:
        if 'reserve_hint' not in s or (host/helper.name).read_bytes()!=helper.read_bytes():
            raise ValueError('Partial or unknown buffer reserve adapter')
        return
    include='#include "texture_staging.hpp"'
    if s.count(include)!=1: raise ValueError('Texture staging include changed')
    s=s.replace(include,include+'\n#include "buffer_reserve.hpp"',1)
    begin=s.index('    void ensure(Buffer &b, VkDeviceSize size, VkBufferUsageFlags usage) {')
    end=s.index('    // A cached immutable device-local model buffer',begin)
    old=s[begin:end]
    if old.count('b.size = size;')!=1 or old.count('f.vkAllocateMemory')!=1:
        raise ValueError('Original buffer capacity or allocation route changed')
    new=old.replace('VkBufferUsageFlags usage) {','VkBufferUsageFlags usage, bool reserve_hint = true) {',1)
    anchor='''        if (b.buffer) {
            f.vkDestroyBuffer(device, b.buffer, nullptr);'''
    if new.count(anchor)!=1: raise ValueError('Original buffer destruction route changed')
    new=new.replace(anchor,'''        const auto requested = size;
        static const bool reserve = [] {
            const char* setting = std::getenv("MW34_BUFFER_RESERVE");
            if (!setting || !*setting || !std::strcmp(setting,"1")) return true;
            if (!std::strcmp(setting,"0")) return false;
            throw std::runtime_error("MW34_BUFFER_RESERVE must be 0 or 1");
        }();
        if (b.buffer && reserve && reserve_hint) size = mw34::allocation::stream_capacity(size);
        if (b.buffer) {
            static const bool trace = std::getenv("MW34_BUFFER_GROWTH_TRACE") != nullptr;
            if (trace) std::fprintf(stderr,"Buffer growth: present=%llu previous=%llu requested=%llu capacity=%llu\\n",
                (unsigned long long)(presents+1),(unsigned long long)b.size,
                (unsigned long long)requested,(unsigned long long)size);
            f.vkDestroyBuffer(device, b.buffer, nullptr);''',1)
    old_create='        check(f.vkCreateBuffer(device, &bi, nullptr, &b.buffer), "buffer");'
    if new.count(old_create)!=1: raise ValueError('Original buffer creation route changed')
    new=new.replace(old_create,'''        const auto created = f.vkCreateBuffer(device, &bi, nullptr, &b.buffer);
        if (size != requested && (created == VK_ERROR_OUT_OF_DEVICE_MEMORY || created == VK_ERROR_OUT_OF_HOST_MEMORY)) {
            b = {};
            ensure(b, requested, usage, false);
            return;
        }
        check(created, "buffer");''',1)
    old_alloc='        check(f.vkAllocateMemory(device, &ai, nullptr, &b.memory), "buffer memory");'
    if new.count(old_alloc)!=1: raise ValueError('Original memory allocation route changed')
    new=new.replace(old_alloc,'''        const auto allocated = f.vkAllocateMemory(device, &ai, nullptr, &b.memory);
        if (size != requested && (allocated == VK_ERROR_OUT_OF_DEVICE_MEMORY || allocated == VK_ERROR_OUT_OF_HOST_MEMORY)) {
            f.vkDestroyBuffer(device, b.buffer, nullptr);
            b = {};
            ensure(b, requested, usage, false);
            return;
        }
        check(allocated, "buffer memory");''',1)
    for call,label,extra in [
        ('f.vkBindBufferMemory(device, b.buffer, b.memory, 0)','bind buffer',''),
        ('f.vkMapMemory(device, b.memory, 0, VK_WHOLE_SIZE, 0, &b.mapped)','map buffer',' || result == VK_ERROR_MEMORY_MAP_FAILED'),
    ]:
        anchor='        check('+call+', "'+label+'");'
        if new.count(anchor)!=1: raise ValueError('Original '+label+' route changed')
        replacement='''        {
            const auto result = '''+call+''';
            if (size != requested && (result == VK_ERROR_OUT_OF_DEVICE_MEMORY || result == VK_ERROR_OUT_OF_HOST_MEMORY'''+extra+''')) {
                f.vkDestroyBuffer(device, b.buffer, nullptr);
                f.vkFreeMemory(device, b.memory, nullptr);
                b = {};
                ensure(b, requested, usage, false);
                return;
            }
            check(result, "'''+label+'''");
        }'''
        new=new.replace(anchor,replacement,1)
    s=s[:begin]+new+s[end:]
    p.write_text(s,encoding='utf-8',newline='\n');(host/helper.name).write_bytes(helper.read_bytes())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host',type=Path)
    apply(parser.parse_args().host.resolve(strict=True))
