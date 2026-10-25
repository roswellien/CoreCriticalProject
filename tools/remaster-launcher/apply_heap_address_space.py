"""Keep native guest heap growth outside all existing guest mappings."""
from pathlib import Path
import argparse
import shutil


def apply(host):
    header = host / 'memory/guest_memory.hpp'
    source = header.read_text()
    marker = '    void unmap(GuestAddress start);'
    method = '''    // Find a 64-KiB-aligned hole without changing mappings or permissions.
    // Zero means no complete range fits before the exclusive limit.
    [[nodiscard]] unsigned find_unmapped_range(unsigned start, unsigned size, unsigned limit) const {
        if (!size || start >= limit) return 0;
        std::uint64_t at = (std::uint64_t(start) + 0xffffU) & ~std::uint64_t(0xffff);
        for (const auto& [base, region] : regions_) {
            const auto end = std::uint64_t(base) + region.size;
            if (end <= at) continue;
            if (at + size <= base) break;
            at = (end + 0xffffU) & ~std::uint64_t(0xffff);
            if (at + size > limit) return 0;
        }
        return at + size <= limit ? unsigned(at) : 0;
    }
'''
    if 'unsigned find_unmapped_range(' not in source:
        if source.count(marker) != 1:
            raise RuntimeError('Unexpected native GuestMemory interface')
        header.write_text(source.replace(marker, method + marker))
    elif method not in source:
        raise RuntimeError('Existing guest mapping search differs from the maintained implementation')
    helper = Path(__file__).with_name('native-overrides') / 'heap_partitions.hpp'
    shutil.copy2(helper, host / helper.name)
    path = host / 'mfc_stage.hpp'
    source = path.read_text()
    old = 'runtime.memory().write({at},z);});'
    new = 'runtime.memory().write({at},z);},\n   [&](unsigned at,unsigned size,unsigned limit){return runtime.memory().find_unmapped_range(at,size,limit);});'
    if old in source:
        if source.count(old) != 1:
            raise RuntimeError('Unexpected guest heap clear callback')
        source = source.replace(old, new)
    elif new not in source:
        raise RuntimeError('Missing native guest heap callback')
    source = source.replace('g.gheap_mapped=&s.host.gheap.mapped;',
                            'g.gheap_mapped=&s.host.gheap.fast_mapped;')
    if 'g.gheap_mapped=&s.host.gheap.fast_mapped;' not in source:
        raise RuntimeError('Missing translated heap fast gate')
    path.write_text(source)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
