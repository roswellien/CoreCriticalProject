import struct

path = r'D:\Projects\MW34Recomp\local\work-ahead\missilsrm-correction-v1\t1-texture-props-v1.zbd'
with open(path, 'rb') as f:
    f.seek(12264 - 16)
    block = f.read(128)

print('Block around 12264:')
print(block)

# Look at fields: offset, size, dimensions
for i in range(0, len(block)-4, 4):
    val = struct.unpack_from('<I', block, i)[0]
    print(f'Offset +{i}: {val} (0x{val:08x})')
