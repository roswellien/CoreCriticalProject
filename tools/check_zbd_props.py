with open(r'D:\Projects\MW34Recomp\local\work-ahead\missilsrm-correction-v1\t1-texture-props-v1.zbd', 'rb') as f:
    data = f.read()

print('Length of t1-texture-props-v1.zbd:', len(data))

# Search for texture names in the binary
names = [
    b'c5strt10', b'c5strt04', b'c5strt09', b'c5strt12',
    b'lighthouse01', b'lighthouse04', b'point_flare', b'lflare1', b'lflare2'
]

for name in names:
    pos = 0
    matches = []
    while True:
        idx = data.lower().find(name, pos)
        if idx == -1: break
        matches.append(idx)
        pos = idx + len(name)
    print(f'{name.decode()}: {len(matches)} occurrences at {matches[:5]}')
