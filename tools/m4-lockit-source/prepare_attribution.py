"""Add additive exact undefined-callback and physical-symbol tools."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[2];T=ROOT/'tools/m4-lockit-source';B=ROOT/'reports/m4-lockit-source'
lift='044316594ce299d04ff9e3aac5bd3bbc157c5ed758f7693db0238c1d727dcb0d'
assert hashlib.sha256((B/'lifts-r1/report.json').read_bytes()).hexdigest()==lift
s=(ROOT/'tools/m4-next-source/game_callbacks.py').read_text().replace('reports/m4-next-source','reports/m4-lockit-source').replace('f5fc110ad15832c19d8be342c6b0f39a91c8ded617e0821f9cf37c661176df2b',lift)
(T/'game_callbacks.py').write_text(s)
s=(ROOT/'tools/m4-next-source/symbol_attribution_v2.py').read_text().replace('reports/m4-next-source','reports/m4-lockit-source').replace('f5fc110ad15832c19d8be342c6b0f39a91c8ded617e0821f9cf37c661176df2b',lift)
s=s.replace('len(mapping) == 15 and len(objects) == 30','len(mapping) == 10 and len(objects) == 20').replace('bodies=15, objects=30','bodies=10, objects=20').replace('All sealed game/sentinel bodies and COFFs','All ten sealed four-root bodies and COFFs')
(T/'symbol_attribution.py').write_text(s)
print('Prepared exact callback and physical COFF attribution for ten bodies')
