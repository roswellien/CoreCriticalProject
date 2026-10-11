"""Own PE loader spans before source execution; captured endpoints are never input."""
import hashlib

def need(value,message):
    if not value:
        raise ValueError(message)


def mapped_regions(pe):
    """Same headers/section page ownership as the fixed-base native ImageLoader."""
    need(pe.image_base == 0x400000 and pe.size_of_image == 0x5f5000,
         'Exact current fixed-base game image extent')
    page = lambda n: (n + 4095) & ~4095
    regions = [(pe.image_base, page(pe.size_of_headers), 0, pe.size_of_headers)]
    for section in pe.sections:
        extent = max(section['raw_size'], section['virtual_size'])
        need(extent and section['virtual_address'] % 4096 == 0,
             'Whole admitted mapped game section')
        regions.append((pe.image_base + section['virtual_address'], page(extent),
                        section['raw_offset'], section['raw_size']))
    ordered = sorted(regions)
    need(all(a + n <= b for (a,n,_,_), (b,_,_,_) in zip(ordered,ordered[1:])),
         'Disjoint header and page-rounded PE section ownership')
    need(ordered[-1][0] + ordered[-1][1] == pe.image_base + pe.size_of_image,
         'Complete declared source loader image extent')
    return ordered


def admit(machine,pe):
    """Add only absent source ownership at model construction, preserving aliases.

    The source model normally supplies its code/data/backing allocations already.
    Raw resource bytes and loader zero tails require their own PE provenance too.
    Existing inputs, import patches and carried state are never overwritten.
    """
    need(not hasattr(machine,'_source_game_ownership'), 'Single initial game ownership admission')
    before = {address:bytes(value) for address,value in machine.memory.items()}
    added = []
    regions = mapped_regions(pe)
    for base,extent,offset,raw_size in regions:
        raw = pe.data[offset:offset + raw_size]
        need(len(raw) == raw_size <= extent, 'Complete physical PE raw section backing')
        initial = raw + bytes(extent - raw_size)
        cursor = base
        while cursor < base + extent:
            owners = [(address,value) for address,value in machine.memory.items()
                      if address <= cursor < address + len(value)]
            if owners:
                cursor = min(base + extent,max(address + len(value) for address,value in owners))
                continue
            next_owner = min((address for address,value in machine.memory.items()
                              if value and cursor < address < base + extent),default=base + extent)
            need(next_owner > cursor and cursor not in machine.memory,
                 'Fresh disjoint missing source allocation span')
            value = initial[cursor-base:next_owner-base]
            machine.memory[cursor] = bytearray(value)
            added.append(dict(address=cursor,bytes=len(value),sha256=hashlib.sha256(value).hexdigest(),
                              region_base=base,region_extent=extent,physical_raw_offset=offset,
                              physical_raw_size=raw_size,source='Own physical PE raw bytes plus loader-defined zero tail'))
            cursor = next_owner
    need(all(bytes(machine.memory[address]) == value for address,value in before.items()),
         'Every existing source input/alias byte preserved')
    for address,value in before.items():
        need(machine.bytes(address,len(value)) == value,
             'Every existing source ownership alias is consistent')
    # Exercise complete source alias consistency using the actual model reader.
    for base,extent,_,_ in regions:
        need(len(machine.bytes(base,extent)) == extent, 'Every complete own mapped PE region is readable')
    return dict(regions=[(base,extent)for base,extent,_,_ in regions],added=added,
                every_existing_source_byte_preserved=True,captured_endpoint_input=False,
                admission_phase='Machine construction before source bootstrap or selected roots')
