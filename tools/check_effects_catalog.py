import json

with open('local/effect-lighting-r1/effects-r5.json', 'r') as f:
    eff = json.load(f)

targets = [
    'spotlight1', 'c5strt10', 'c5strt04', 'c5strt09', 'c5strt12',
    'mfglow01', 'mfglow', 'runway01', 'm7runway01',
    'lighthouse01', 'lighthouse04', 'point_flare', 'lflare1', 'lflare2'
]

sources = eff.get('sources', [])
print('Total sources in effects-r5:', len(sources))
found_count = 0
for s in sources:
    name = s.get('name', '').lower()
    for t in targets:
        if t in name:
            print(s)
            found_count += 1
print('Found target textures in sources:', found_count)
