"""Separate the private native host's CRT, codec and service allocation pools."""
from pathlib import Path
import argparse, shutil

def apply(host):
    helper=Path(__file__).with_name('native-overrides')/'heap_partitions.hpp'
    shutil.copy2(helper,host/helper.name)
    p=host/'mfc_stage.hpp';s=p.read_text()
    def replace(a,b):
        nonlocal s
        if s.count(a)!=1:raise RuntimeError('Unexpected native heap source: '+a[:90])
        s=s.replace(a,b)
    replace('#include "vk_scene.hpp"','#include "vk_scene.hpp"\n#include "heap_partitions.hpp"')
    start=s.index('struct GuestHeap{');end=s.index('struct SoundLock',start)
    s=s[:start]+'using GuestHeap=mw34::heap_partitions::GuestHeap;\n'+s[end:]
    start=s.index(' unsigned gheap_alloc(');end=s.index(' unsigned handle_token(',start)
    s=s[:start]+''' unsigned gheap_alloc(unsigned bytes,bool zero,unsigned owner=0){
  return host.gheap.allocate(bytes,zero,owner,[&](unsigned at,unsigned size){bool bad{};try{runtime.memory().map({at},size,Permissions::read|Permissions::write);}catch(...){bad=true;}if(bad)deny("Checked guest heap region mapping",at);},
   [&](unsigned at,unsigned size){std::vector<std::byte>z(size);runtime.memory().write({at},z);});}
 void gheap_free(unsigned at){if(!host.gheap.live.count(at))deny("HeapFree of a pointer that is not a live guest heap block",at);host.gheap.release(at);}
''' +s[end:]
    replace('const auto live=host.gheap.live.size();host.gheap.live.clear();host.gheap.free_blocks.clear();','const auto live=host.gheap.destroy(hs::token);')
    # Only the CRT import branch owns this native heap token. The codec creates
    # its own HeapCreate handle and must allocate from that handle's regions.
    start=s.index('  if(crt&&(n=="HeapAlloc"');end=s.index('  if(n=="GetLastError")',start)
    block=s[start:end].replace('gheap_alloc(bytes,flags&HEAP_ZERO_MEMORY)','gheap_alloc(bytes,flags&HEAP_ZERO_MEMORY,hs::token)')
    block=block.replace('if(host.gheap.live.count(arg(2))){const unsigned ptr=arg(2);','if(host.gheap.live.count(arg(2))){const unsigned ptr=arg(2);if(host.gheap.owner_of(ptr)!=hs::token)deny(n+" of a block owned by another guest heap",ptr);')
    s=s[:start]+block+s[end:]
    # Restrict replacements to the known guest-heap allocation expressions.
    replace('gheap_alloc(arg(2),flags&HEAP_ZERO_MEMORY)','gheap_alloc(arg(2),flags&HEAP_ZERO_MEMORY,arg(0))')
    replace('gheap_alloc(arg(3),flags&HEAP_ZERO_MEMORY)','gheap_alloc(arg(3),flags&HEAP_ZERO_MEMORY,arg(0))')
    p.write_text(s)
    # Photo/replay saves allocator metadata too. New records include ownership;
    # older files must reject visibly rather than restore an ambiguous heap.
    p=host/'photo_replay_math.hpp'
    if p.exists():
        s=p.read_text()
        replacements=[
            ('gheap_regions;','gheap_regions;\n    std::vector<std::pair<std::uint32_t, std::uint32_t>> gheap_region_owners;'),
            ("'L', 'Y', '1'","'L', 'Y', '2'"),
            ('"MW3RPLY1"','"MW3RPLY2"'),
            ('wr_pairs(f.gheap_regions);','wr_pairs(f.gheap_regions);\n            wr_pairs(f.gheap_region_owners);'),
            ('!rd_pairs(f.gheap_regions))','!rd_pairs(f.gheap_regions) || !rd_pairs(f.gheap_region_owners))')]
        for a,b in replacements:
            if s.count(a)!=1:raise RuntimeError('Unexpected replay heap source: '+a)
            s=s.replace(a,b)
        p.write_text(s)
        p=host/'photo_replay_stage.inc';s=p.read_text()
        a='rec.gheap_regions.assign(host.gheap.regions.begin(), host.gheap.regions.end());'
        assert s.count(a)==1;s=s.replace(a,a+'\n    rec.gheap_region_owners.assign(host.gheap.region_owners.begin(), host.gheap.region_owners.end());')
        a='host.gheap.free_blocks.clear();'
        assert s.count(a)==1;s=s.replace(a,'for (const auto& kv : rec.gheap_region_owners) {\n        const auto [it, added] = host.gheap.region_owners.emplace(kv.first, kv.second);\n        if (!added && it->second != kv.second) throw std::runtime_error("Replay heap ownership differs from this session");\n    }\n    '+a)
        a='host.gheap.region_end = std::max(host.gheap.region_end, rec.gheap_region_end);'
        assert s.count(a)==1;s=s.replace(a,'host.gheap.region_end = rec.gheap_region_end;')
        p.write_text(s)

    from apply_heap_address_space import apply as apply_address_space
    apply_address_space(host)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('host',type=Path)
    apply(parser.parse_args().host)
