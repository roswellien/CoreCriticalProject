"""Additive109 derivative of sealed persistent103 comparison, no capture mutation."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
t=(ROOT/'tools/m4-mfc-source/compare_connected.py').read_text()
def change(a,b):
 global t
 assert t.count(a)==1,a
 t=t.replace(a,b)
t=t.replace('selected103','selected109').replace('native103','native109').replace('persistent103','persistent109')
change("out=ROOT/'reports/m4-mfc-source'/name","out=ROOT/'reports/m4-fs-source'/name")
t=t.replace("ROOT/'tools/m4-mfc-source/game_model.py'","ROOT/'tools/m4-fs-source/game_model.py'")
change("op=pin(ROOT/'reports/m4-mfc-source/original-run-r3/report.json','a50819520282272712899cb64faedd8d568c08a22d6d25e65fbc18358571faa0');ori=D.DirectSet(json.loads(op.read_bytes())['original_capture'],pin)","op=pin(ROOT/'reports/m4-fs-source/original-validation-r1/report.json','a419e9a7819ba38077621efdda6da5440c0f00042c6c492d7dc672ebeab632b4');ori=D.DirectSet(json.loads(op.read_bytes())['original_capture'],pin)")
change("+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes());roots=","+json.loads(pin(ROOT/'reports/m4-mfc-source/recovery-r4/mfc-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes());roots=")
t=t.replace("ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json'","ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json'")
change("len(expected_callbacks)==75,'All75","len(expected_callbacks)==81,'All81")
p=ROOT/'tools/m4-fs-source/compare_connected.py';assert not p.exists();p.write_text(t)
