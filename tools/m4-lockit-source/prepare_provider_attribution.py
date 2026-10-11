"""Physical provider COFF and exact callback attribution, including unadmitted bytes."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[2];T=ROOT/'tools/m4-lockit-source';B=ROOT/'reports/m4-lockit-source'
lift='062caafd46c0e8c174df4a830c052fa405452542139de2cb4a4d244e39d1b0fa'
assert hashlib.sha256((B/'provider-lifts-r2/report.json').read_bytes()).hexdigest()==lift
s=(T/'game_callbacks.py').read_text().replace('reports/m4-lockit-source/lifts-r1','reports/m4-lockit-source/provider-lifts-r2').replace('044316594ce299d04ff9e3aac5bd3bbc157c5ed758f7693db0238c1d727dcb0d',lift)
s=s.replace("interface['instructions']","interface['provider_instructions']")
s=s.replace("schema='mw34-onexit-game-original-callbacks-v1'","schema='mw34-Lockit-provider-original-callbacks-v1'").replace('Exact source/LLVM undefined flag attribution; no execution','Exact provider source/LLVM undefined flag attribution for fullcompiledintervals; initialized pathonly admitted; no execution')
(T/'provider_callbacks.py').write_text(s)
s=(T/'symbol_attribution.py').read_text().replace('reports/m4-lockit-source/lifts-r1','reports/m4-lockit-source/provider-lifts-r2').replace('044316594ce299d04ff9e3aac5bd3bbc157c5ed758f7693db0238c1d727dcb0d',lift)
s=s.replace("r'symbol-attribution-r[1-9][0-9]*'","r'provider-symbol-attribution-r[1-9][0-9]*'").replace('len(mapping) == 10 and len(objects) == 20','len(mapping) == 2 and len(objects) == 4').replace('bodies=10, objects=20','bodies=2, objects=4')
(T/'provider_symbol_attribution.py').write_text(s)
print('Prepared provider attribution for2bodies4COFF')
