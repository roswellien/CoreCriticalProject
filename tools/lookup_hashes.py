import os, struct

def fnv1a64(data):
    h = 0xcbf29ce484222325
    for b in data:
        h ^= b
        h = (h * 0x100000001b3) & 0xffffffffffffffff
    return h

bound_hashes = {
    0x1cc6d281f19d36aa: "922754992", 0xd3fa37f5f75e18b3: "922755056", 0x77ce3aa75ca8aa2b: "922755120",
    0x8540706d3eb6df01: "922755376", 0x43f93af31207dbc0: "922755504", 0xfdc7a8bb3ce0b022: "922755440",
    0x6825fb9ed6fdbabe: "922755568", 0x2e226374834edecf: "922755632", 0x39cb8184c9f03902: "922755824",
    0x45138046971a3cb4: "922755760", 0xbbed7c2cc25ac517: "922755696", 0x9848a28232d83c37: "922759984",
    0x1774446b9c0a8fd5: "922759088", 0x10053d16b33009b3: "922758640", 0x978577d9c435e889: "922759024",
    0x7b98b136ac990020: "922758576", 0x2f6c446c2d0ddb6f: "922758512", 0x3200541e8d9d0e2e: "922757936",
    0x229347f64effc77b: "922758064", 0xe2593144b8fe62a2: "922758000", 0xb9a89877f16ca71c: "922759664",
    0xf7311862fddff25: "922771824"
}

bank_path = 'local/work-ahead/missilsrm-correction-v1/t1-texture-props-v1.zbd'
with open(bank_path, 'rb') as f:
    toc = f.read(65536)
    # Parse TOC: entries start at offset 8, 40 bytes each
    offset = 8
    while offset + 40 <= len(toc):
        off, flags = struct.unpack_from('<II', toc, offset)
        name = toc[offset+8:offset+40].split(b'\x00')[0].decode('latin1', errors='ignore')
        if not name: break
        if off < os.path.getsize(bank_path):
            f.seek(off)
            hdr = f.read(16)
            fmt, dims = struct.unpack_from('<II', hdr, 0)
            w = dims & 0xffff
            h = (dims >> 16) & 0xffff
            pix = f.read(w*h*2)
            thash = fnv1a64(pix)
            if thash in bound_hashes:
                print(f"Matched {name:16} ({w:4}x{h:4}) -> surface {bound_hashes[thash]} (hash={hex(thash)})")
        offset += 40
