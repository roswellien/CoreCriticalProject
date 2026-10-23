"""Add bounded fault-only texture/heap evidence to the current split native host."""
from pathlib import Path
import shutil


def apply(host):
    host = Path(host)
    path = host / 'mfc_stage.hpp'
    text = path.read_text(encoding='utf-8')

    def replace(old, new):
        nonlocal text
        if text.count(old) != 1:
            raise ValueError('Unexpected texture diagnostic seam: ' + old[:80])
        text = text.replace(old, new)

    replace('#include "large_texture_seek.hpp"', '#include "large_texture_seek.hpp"\n#include "texture_read_diagnostics.hpp"')
    replace('unsigned large_texture_seeks{};', 'unsigned large_texture_seeks{};mw34::texture_diagnostics::RecentSeeks texture_seeks;unsigned failed_heap_bytes{},failed_heap_owner{},heap_failures{};')
    replace('  return host.gheap.allocate(bytes,zero,owner,', '  const unsigned allocated=host.gheap.allocate(bytes,zero,owner,')
    replace('runtime.memory().write({at},z);});}', '''runtime.memory().write({at},z);});
  if(!allocated){host.failed_heap_bytes=bytes;host.failed_heap_owner=owner;++host.heap_failures;}
  return allocated;}''')
    replace('   if(ph)store(ph,unsigned(hi));return done(r,4);}', '''   host.texture_seeks.push({h,arg(1),ph,arg(3),unsigned(r),host.last_error,host.replacement_bank_files.count(h)!=0,std::find(returns.begin(),returns.begin()+depth,0x00518e08U)!=returns.begin()+depth,wide});
   if(ph)store(ph,unsigned(hi));return done(r,4);}''')
    # No new memory reads during normal execution. All diagnostic reads are
    # bounded metadata recovered from the exact admitted fault call chain.
    anchor='  [[noreturn]] static void flat_fault_throw(){'
    method='''  void texture_fault_evidence(){
   try{
    const auto&h=host.gheap;std::uint64_t live=0,free=0;for(const auto&[p,n]:h.live)live+=n;for(const auto&[p,n]:h.free_blocks)free+=n;
    std::fprintf(stderr,"Texture fault heap: mapped=%08x top=%08x limit=%08x live_bytes=%llu free_bytes=%llu blocks=%zu failures=%u last_failed_bytes=%08x owner=%08x\\n",h.mapped,h.top,h.hi,(unsigned long long)live,(unsigned long long)free,h.live.size(),host.heap_failures,host.failed_heap_bytes,host.failed_heap_owner);
    const auto&history=host.texture_seeks;std::fprintf(stderr,"Texture fault seeks: count=%u open_replacements=%zu widened=%u\\n",history.count,host.replacement_bank_files.size(),host.large_texture_seeks);
    const unsigned first=history.count>8?history.count-8:0;for(unsigned i=first;i<history.count;++i){const auto&s=history.entries[i%8];std::fprintf(stderr,"  seek handle=%08x offset=%08x high_ptr=%08x origin=%u result=%08x error=%u replacement=%u texture_caller=%u widened=%u\\n",s.handle,s.offset,s.high_pointer,s.origin,s.result,s.error,unsigned(s.replacement),unsigned(s.texture_caller),unsigned(s.widened));}
    const auto f=mw34::texture_diagnostics::read_frame(std::span<const unsigned>(returns.data(),depth),std::span<const unsigned>(returns_sp.data(),depth),[&](unsigned a,unsigned n){return readable(a,n);},[&](unsigned a){return load(a);});
    const auto entry=mw34::texture_diagnostics::lookup_entry(std::span<const unsigned>(returns.data(),depth),std::span<const unsigned>(returns_sp.data(),depth),[&](unsigned a,unsigned n){return readable(a,n);},[&](unsigned a){return load(a);});
    if(entry){char name[33]{};bool text=true;for(unsigned i=0;i<32;++i){const auto c=runtime.memory().load<unsigned char>({entry+i});if(!c)break;if(c<32||c>126){text=false;break;}name[i]=char(c);}if(text)std::fprintf(stderr,"Texture fault table: name=%s offset=%08x palette_index=%08x\\n",name,load(entry+32),load(entry+36));}
    if(f.found){std::fprintf(stderr,"Texture fault fread: site=%08x destination=%08x size=%u count=%u stream=%08x object=%08x\\n",f.site,f.destination,f.size,f.count,f.stream,f.object);
     if(f.object&&readable(f.object,28)){const unsigned dims=load(f.object+4),flags=load(f.object+8),pal=load(f.object+12);std::fprintf(stderr,"Texture fault descriptor: pixels=%u width=%u height=%u flags=%08x palette_fields=%08x palette_count=%d pixel_ptr=%08x alpha_ptr=%08x palette_ptr=%08x\\n",load(f.object),dims&65535,dims>>16,flags,pal,int(short(pal>>16)),load(f.object+16),load(f.object+20),load(f.object+24));}
     if(f.stream&&readable(f.stream,28))std::fprintf(stderr,"Texture fault FILE: ptr=%08x remaining=%08x base=%08x flags=%08x fd=%u buffer_size=%u\\n",load(f.stream),load(f.stream+4),load(f.stream+8),load(f.stream+12),load(f.stream+16),load(f.stream+24));
    }
   }catch(...){std::fprintf(stderr,"Texture fault metadata unavailable; preserving original fault\\n");}
  }
'''
    replace(anchor, method + anchor)
    replace('const auto&g=owner->state.gpr;std::fprintf', 'owner->texture_fault_evidence();const auto&g=owner->state.gpr;std::fprintf')
    main_path = host / 'main_v2.inc'
    main = main_path.read_text(encoding='utf-8')
    main_anchor = ' require(argc==7,"Composition: exact-game exact-entry-object exact-provider exact-pack before-inputs fresh-directory");'
    if main.count(main_anchor) != 1:
        raise ValueError('Unexpected native startup diagnostic seam')
    main = main.replace(main_anchor, ' mw34::texture_diagnostics::hardware_summary();\n' + main_anchor)
    gpu_path = host / 'vk_scene.hpp'
    gpu = gpu_path.read_text(encoding='utf-8')
    gpu_anchor = '        pool(256);\n        // 1x1 opaque white texture'
    if gpu.count(gpu_anchor) != 1:
        raise ValueError('Unexpected GPU diagnostic seam')
    gpu = gpu.replace(gpu_anchor, '''        if (std::getenv("MW34_SEH_LOG")) {
            VkPhysicalDeviceProperties diagnostic_props{};
            f.vkGetPhysicalDeviceProperties(gpu, &diagnostic_props);
            std::uint64_t local_bytes=0;
            for (unsigned i=0;i<memory.memoryHeapCount;++i)
                if (memory.memoryHeaps[i].flags & VK_MEMORY_HEAP_DEVICE_LOCAL_BIT)
                    local_bytes+=memory.memoryHeaps[i].size;
            std::fprintf(stderr,"Playtest GPU: vendor=%04x device=%04x driver_raw=%08x vulkan_api=%08x device_local_heap_MiB=%llu\\n",diagnostic_props.vendorID,diagnostic_props.deviceID,diagnostic_props.driverVersion,diagnostic_props.apiVersion,(unsigned long long)(local_bytes/1048576));
        }
''' + gpu_anchor)
    shutil.copyfile(Path(__file__).with_name('native-overrides') / 'texture_read_diagnostics.hpp', host / 'texture_read_diagnostics.hpp')
    path.write_text(text, encoding='utf-8')
    main_path.write_text(main, encoding='utf-8')
    gpu_path.write_text(gpu, encoding='utf-8')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
