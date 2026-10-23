import difflib

for fname in ['mesh_override_stage.inc', 'override_arm_damage_plans.inc']:
    pa = f'local/material-authoring-r1/native-lighting-integrated-r6/host-source/{fname}'
    pb = f'local/remaster/gpu-native-avatar-r1/host-source/{fname}'
    lines_a = open(pa, 'r', encoding='utf-8').readlines()
    lines_b = open(pb, 'r', encoding='utf-8').readlines()
    diff = list(difflib.unified_diff(lines_a, lines_b, fromfile='Lighting', tofile='Avatar'))
    print(f"=== DIFF {fname} ===")
    print("".join(diff[:40]))
