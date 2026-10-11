from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];liftsha='e113cca27e1465195dc8b23a855b26bbd4c8233a329ce83201870324bf6f66b0'
for name in ('game_callbacks.py','symbol_attribution.py'):
 s=(ROOT/'tools/m4-fs-source'/name).read_text().replace('reports/m4-fs-source','reports/m4-container-source').replace('recovery-r3','recovery-r3').replace('lifts-r1','lifts-r2').replace('f5af3ee18fd942c5f58226b0ae98fca29d7bdc93877d7cfdd624a43cc0aa1ab8',liftsha)
 if name=='symbol_attribution.py':s=s.replace('== 17 and len(objects) == 34','== 22 and len(objects) == 44').replace('bodies=17, objects=34','bodies=22, objects=44')
 p=ROOT/'tools/m4-container-source'/name;assert not p.exists();compile(s,str(p),'exec');p.write_text(s)
