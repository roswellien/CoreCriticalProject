import os, glob, re

fixtures = [
    'spotlight1', 'c5strt10', 'c5strt04', 'c5strt09', 'c5strt12',
    'mfglow01', 'runway01', 'm7runway01', 'lighthouse01', 'lighthouse04',
    'point_flare', 'lflare1', 'lflare2'
]

# Scan all reader and gamez files
total_occurrences = {}
for fix in fixtures:
    total_occurrences[fix] = 0

per_operation = {
    'Training (t1)': {},
    'Operation 1 (c1)': {},
    'Operation 2 (c2)': {},
    'Operation 3 (c3)': {},
    'Operation 4 (c4/c4b)': {},
    'Other': {}
}

for root, dirs, files in os.walk('MW3/zbd'):
    for f in files:
        if not f.endswith('.zbd'): continue
        path = os.path.join(root, f)
        op = 'Other'
        if 't1' in path: op = 'Training (t1)'
        elif 'c1' in path: op = 'Operation 1 (c1)'
        elif 'c2' in path: op = 'Operation 2 (c2)'
        elif 'c3' in path: op = 'Operation 3 (c3)'
        elif 'c4' in path or 'c4b' in path: op = 'Operation 4 (c4/c4b)'
        
        with open(path, 'rb') as fp:
            data = fp.read().lower()
        
        for fix in fixtures:
            # count occurrences
            c = data.count(fix.encode('ascii'))
            if c > 0:
                total_occurrences[fix] += c
                per_operation[op][fix] = per_operation[op].get(fix, 0) + c

print("=== TOTAL WORLD TEXTURE REFERENCES IN GAME DATA ===")
for fix, count in sorted(total_occurrences.items(), key=lambda x: -x[1]):
    print(f"  {fix:15}: {count} references")

print("\n=== PER OPERATION DISTRIBUTION ===")
for op, counts in per_operation.items():
    print(f"\n{op}:")
    for fix, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {fix:15}: {count} references")
