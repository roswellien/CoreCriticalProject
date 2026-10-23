import struct, os

def fnv1a64(data):
    h = 0xcbf29ce484222325
    for b in data:
        h ^= b
        h = (h * 0x100000001b3) & 0xffffffffffffffff
    return h

# Load texture-banks.bin
bank_map_path = 'local/material-authoring-r1/native-lighting-integrated-r6/prepared/texture-banks.bin'
banks = {}
with open(bank_map_path, 'rb') as f:
    f.seek(8)
    count = struct.unpack('<I', f.read(4))[0]
    for _ in range(count):
        a, b = struct.unpack('<II', f.read(8))
        key = f.read(a).decode('latin1')
        val = f.read(b).decode('latin1')
        banks[key] = val

targets = [
    'spotlight1', 'c5strt10', 'c5strt04', 'c5strt09', 'c5strt12',
    'mfglow01', 'runway01', 'm7runway01', 'lighthouse01', 'lighthouse04',
    'point_flare', 'lflare1', 'lflare2'
]

discovered = {}

for bank_key, bank_file in banks.items():
    if not os.path.exists(bank_file): continue
    with open(bank_file, 'rb') as f:
        data = f.read(65536) # Read TOC header
    
    # TOC format in zbd: entries are 40 bytes each: offset (4), flags (4), name (32)
    # The TOC begins after initial header (or at offset 8/16)
    for t in targets:
        pos = 0
        while True:
            idx = data.lower().find(t.encode(), pos)
            if idx == -1: break
            # In 40-byte record: name starts at record + 8
            rec_start = idx - 8
            if rec_start >= 0 and rec_start + 40 <= len(data):
                off, flags = struct.unpack_from('<II', data, rec_start)
                name_raw = data[rec_start+8 : rec_start+40].split(b'\x00')[0].decode('latin1', errors='ignore')
                if name_raw.lower() == t and off < os.path.getsize(bank_file):
                    # Read texture header at offset
                    with open(bank_file, 'rb') as bf:
                        bf.seek(off)
                        hdr = bf.read(16)
                        if len(hdr) == 16:
                            fmt_tag, dim_tag = struct.unpack_from('<II', hdr, 0)
                            w = dim_tag & 0xffff
                            h = (dim_tag >> 16) & 0xffff
                            if w > 0 and h > 0 and w <= 4096 and h <= 4096:
                                pix = bf.read(w * h * 2)
                                if len(pix) == w * h * 2:
                                    thash = fnv1a64(pix)
                                    key = (name_raw, w, h)
                                    if key not in discovered:
                                        discovered[key] = {
                                            'name': name_raw,
                                            'width': w,
                                            'height': h,
                                            'hash': thash,
                                            'bank': bank_key
                                        }
                                        print(f"Discovered: {name_raw} {w}x{h} hash=0x{thash:016x} from {bank_key}")
            pos = idx + len(t)
