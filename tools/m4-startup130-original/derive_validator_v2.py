from pathlib import Path
p=Path(__file__).resolve().parent;s=(p/'family_phase.py').read_text();assert 'mf[1]==len(filename)+3'in s
(p/'family_phase_v2.py').write_text(s.replace('mf[1]==len(filename)+3','mf[1]==len(filename)+4'))
s=(p/'validate.py').read_text();assert 'from family_phase import'in s
(p/'validate_v2.py').write_text(s.replace('from family_phase import','from family_phase_v2 import').replace("pin(ROOT/'tools/m4-startup130-original/family_phase.py')","pin(ROOT/'tools/m4-startup130-original/family_phase_v2.py')"))
