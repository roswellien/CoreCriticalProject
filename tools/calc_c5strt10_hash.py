def fnv1a64(data):
    h = 0xcbf29ce484222325
    for b in data:
        h ^= b
        h = (h * 0x100000001b3) & 0xffffffffffffffff
    return h

path = r'D:\Projects\MW34Recomp\local\work-ahead\missilsrm-correction-v1\t1-texture-props-v1.zbd'
with open(path, 'rb') as f:
    f.seek(0x1f359298 + 16)
    pixels = f.read(512 * 256 * 2)

h = fnv1a64(pixels)
print(f'c5strt10 in t1-texture-props-v1: 512x256 fmt=1 hash=0x{h:016x} ({h})')
