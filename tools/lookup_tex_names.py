import json, glob, os

# Check effects-r5.json
with open('local/effect-lighting-r1/effects-r5.json', 'r') as f:
    eff = json.load(f)

# Also check normal-registry.json
with open('local/material-authoring-r1/normal-registry.json', 'r') as f:
    reg = json.load(f)

print('Models in reg:', list(reg.get('models', {}).keys()))

# Check textures in bank-hashes
with open('local/material-authoring-r1/native-lighting-integrated-r6/prepared/bank-hashes.json', 'r') as f:
    bh = json.load(f)
print('Bank hashes entries:', len(bh))
