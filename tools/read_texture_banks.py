import struct

path = 'local/material-authoring-r1/native-lighting-integrated-r6/prepared/texture-banks.bin'
with open(path, 'rb') as f:
    magic = f.read(8)
    count = struct.unpack('<I', f.read(4))[0]
    print('Magic:', magic, 'Count:', count)
    for i in range(count):
        a, b = struct.unpack('<II', f.read(8))
        key = f.read(a).decode('latin1')
        val = f.read(b).decode('latin1')
        print(f'{key} -> {val}')
