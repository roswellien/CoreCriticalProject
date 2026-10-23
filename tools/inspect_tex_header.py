import struct

path = r'D:\Projects\MW34Recomp\local\work-ahead\missilsrm-correction-v1\t1-texture-props-v1.zbd'
with open(path, 'rb') as f:
    f.seek(0x1f359298)
    hdr = f.read(32)

print('Header at 0x1f359298:')
for i in range(0, len(hdr), 4):
    v = struct.unpack_from('<I', hdr, i)[0]
    print(f'Hdr +{i}: {v} (0x{v:08x})')
