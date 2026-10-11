"""Generate additive source callback and physical AMD64 symbol tools."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-next-source'
h='f5fc110ad15832c19d8be342c6b0f39a91c8ded617e0821f9cf37c661176df2b'
assert hashlib.sha256((R/'reports/m4-next-source/lifts-r1/report.json').read_bytes()).hexdigest()==h
for src,dest in(('symbol_attribution.py','symbol_attribution.py'),('game_callbacks.py','game_callbacks.py')):
 s=(R/'tools/m4-container-source'/src).read_text().replace('reports/m4-container-source/lifts-r2','reports/m4-next-source/lifts-r1').replace('reports/m4-container-source/recovery-r3','reports/m4-next-source/recovery-r1').replace('reports/m4-container-source','reports/m4-next-source').replace('e113cca27e1465195dc8b23a855b26bbd4c8233a329ce83201870324bf6f66b0',h).replace('bodies=22, objects=44','bodies=15, objects=30')
 (T/dest).write_text(s)
print('New callback/physical symbol tools prepared')
