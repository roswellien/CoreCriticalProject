import struct

with open('MW3/zbd/t1/texture.zbd', 'rb') as f:
    data = f.read()

print('Length of t1/texture.zbd:', len(data))
# Check header
magic, num_entries = struct.unpack_from('<4sI', data, 0)
print('Magic:', magic, 'Entries:', num_entries)

# Check entries
offset = 8
for i in range(min(num_entries, 100)):
    name_bytes = data[offset:offset+16]
    name = name_bytes.split(b'\x00')[0].decode('latin1', errors='ignore')
    # Let's inspect entry record size
    # Typically 16 bytes name + metadata or similar
    # Let's search for c5strt10
    if 'c5strt' in name or 'lighthouse' in name or 'flare' in name:
        print(f'Entry {i}: {name} at {offset}')
    offset += 64 # Let's see record stride
