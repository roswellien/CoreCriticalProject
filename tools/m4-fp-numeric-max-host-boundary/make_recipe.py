"""Derive a separately owned recipe from the frozen r5 recipe, without editing it."""
from pathlib import Path
import hashlib
root=Path(__file__).resolve().parents[2]
old=root/'tools/m4-fp-numeric-max-integration/build.ps1'
text=old.read_text()
changes=[
("reports/m4-fp-numeric-max-integration'","reports/m4-fp-numeric-max-host-boundary'"),
('build/m4-nmx-integration-','build/m4-nmx-host-boundary-'),
("$nmxPrep=Join-Path $nmxAllowed 'preparation-r4';", "$nmxPrep=Join-Path $nmxRoot 'reports/m4-fp-numeric-max-integration/preparation-r4';$nmxDerivative=Join-Path $nmxAllowed 'derivation-r2';$nmxD=Get-Content -Raw -LiteralPath (Join-Path $nmxDerivative 'derivation.json')|ConvertFrom-Json;if((Hash-Nmx (Join-Path $nmxDerivative 'derivation.json'))-ne'086e1a021aaa8b0fae07585558bf4644285fe9f735ba186e39efe46c5cc509e2'){throw 'Exact derivative required'};foreach($nmxPair in $nmxD.files.PSObject.Properties){if((Hash-Nmx $nmxPair.Name)-ne$nmxPair.Value){throw 'Derivative input changed'}};"),
("(Get-ChildItem -LiteralPath $nmxPrep -File);", "(Get-ChildItem -LiteralPath $nmxPrep -File);(Get-ChildItem -LiteralPath $nmxDerivative -File);"),
('"-DMW34_NMX_OBJECT=$nmxObject")', '"-DMW34_NMX_OBJECT=$nmxObject","-DMW34_NMX_SOURCE_DIR=$nmxDerivative")'),
("'mw34_nmx_integration.exe'", "'mw34_nmx_host_boundary.exe'"),
("scope='NEW shared-r9 compiled wrapper/body/exact MSVCP50 leaf native unit candidate; independent/offline comparison pending'", "scope='NEW Session-owned numerical host boundary; direct captures precede harness cleanup; unchanged guest IR/domain/r9; independent comparison pending'"),
]
for a,b in changes:
 assert text.count(a)==1,(a,text.count(a))
 text=text.replace(a,b)
out=Path(__file__).with_name('build.ps1')
assert not out.exists()
out.write_text(text)
print(hashlib.sha256(out.read_bytes()).hexdigest())
