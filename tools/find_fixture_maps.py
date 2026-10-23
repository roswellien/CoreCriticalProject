import glob, os

fixtures = [
    b'spotlight1', b'c5strt10', b'c5strt04', b'c5strt09', b'c5strt12',
    b'mfglow01', b'runway01', b'm7runway01', b'lighthouse01', b'lighthouse04',
    b'point_flare', b'lflare1', b'lflare2'
]

zbds = glob.glob('MW3/zbd/**/*.zbd', recursive=True) + glob.glob('MW3/zbd/*.zbd')
results = {}

for z in zbds:
    with open(z, 'rb') as f:
        data = f.read().lower()
    found = []
    for fix in fixtures:
        if fix in data:
            found.append(fix.decode('ascii'))
    if found:
        results[z] = found

for k, v in results.items():
    print(k, v)
