"""Additive C++ declaration and exact getter-padding pack corrections."""
from pathlib import Path
source=Path(__file__).resolve().with_name('prepare_chronological_v2.py')
target=source.with_name('prepare_chronological_v3.py')
assert not target.exists()
text=source.read_text()
def one(old,new):
    global text
    assert text.count(old)==1,old
    text=text.replace(old,new,1)
one("        need(all(len(v)==4096 for _,v in pages.values()),'No instruction extends a sparse page')", """        getter_raw,getter_offset=physical(0x40a850,5)
        need(getter_raw[:4]==bytes.fromhex('8b4104c3'),'Whole physical getter body')
        # The fifth hook byte is actual unreachable padding after the source
        # RET. It is a physical input, never a claimed reached instruction.
        base=0x40a000;page=pages[base][1];need(page[0x854]in(0xcc,getter_raw[4]),'Exact sparse getter padding')
        overlay.append(dict(address=0x40a854,old_hex=bytes([page[0x854]]).hex(),source_hex=getter_raw[4:].hex(),physical_source_PC=0x40a854,scope='Unexecuted physical padding beyond getterRET'))
        page[0x854]=getter_raw[4]
        padding=dict(pc=0x40a854,size=1,image_offset=getter_offset+4,origin=0,scope='Unexecuted physical padding beyond sourceRET')
        need(padding['pc']not in known,'Independent getter padding span')
        spans.append(padding);new.append(padding)
        need(all(len(v)==4096 for _,v in pages.values()),'No instruction extends a sparse page')""")
one("declarations='struct ConstructorAllocSite", "declarations='extern \\\"C\\\" void ctor_getter_bridge();\\nstruct ConstructorAllocSite")
# The getter's raw array and row need two closes, then both std::array closes.
one("','.join(hex(v)for v in getter)+'}}};\\n'", "','.join(hex(v)for v in getter)+'}}}};\\n'")
one("        pin(__file__);pin(ROOT/'tools/m4-capture-direct/capture_direct_v3.cpp')", "        pin(__file__);pin(HERE/'prepare_chronological.py');pin(HERE/'prepare_chronological_v2.py');pin(HERE/'derive_chronological_v2.py');pin(HERE/'derive_chronological_v3.py');pin(ROOT/'tools/m4-capture-direct/capture_direct_v3.cpp')")
target.write_text(text)
