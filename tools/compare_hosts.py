import os

dir_a = 'local/material-authoring-r1/native-lighting-integrated-r6/host-source'
dir_b = 'local/remaster/gpu-native-avatar-r1/host-source'

files_a = set(os.listdir(dir_a))
files_b = set(os.listdir(dir_b))

print("In B (Avatar) but not in A (Lighting):", sorted(files_b - files_a))
print("In A (Lighting) but not in B (Avatar):", sorted(files_a - files_b))

diffs = []
for f in sorted(files_a & files_b):
    pa = os.path.join(dir_a, f)
    pb = os.path.join(dir_b, f)
    if os.path.isfile(pa) and os.path.isfile(pb):
        if open(pa, 'rb').read() != open(pb, 'rb').read():
            diffs.append(f)
print("Files that differ between Lighting and Avatar:", diffs)
