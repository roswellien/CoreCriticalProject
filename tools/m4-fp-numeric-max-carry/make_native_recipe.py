"""Separate carry-unit recipe from frozen host-boundary recipe; no ancestor edits."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[2]
s=(ROOT/'tools/m4-fp-numeric-max-host-boundary/build.ps1').read_text()
s=s.replace('param([Parameter(Mandatory=$true)][string]$OutputDirectory)','param([Parameter(Mandatory=$true)][string]$OutputDirectory,[Parameter(Mandatory=$true)][string]$PreparationDirectory,[Parameter(Mandatory=$true)][string]$PreparationSHA256)')
s=s.replace('reports/m4-fp-numeric-max-host-boundary','reports/m4-fp-numeric-max-carry').replace('build/m4-nmx-host-boundary-','build/m4-nmx-carry-native-')
a=s.index("$nmxDerivative=Join-Path $nmxAllowed 'derivation-r4';");b=s.index('$nmxR9=',a)
s=s[:a]+"$nmxDerivative=[IO.Path]::GetFullPath($PreparationDirectory);if([IO.Path]::GetDirectoryName($nmxDerivative)-ne$nmxAllowed -or (Hash-Nmx (Join-Path $nmxDerivative 'preparation.json'))-ne$PreparationSHA256){throw 'Exact private carry preparation required'};$nmxD=Get-Content -Raw -LiteralPath (Join-Path $nmxDerivative 'pins.json')|ConvertFrom-Json;foreach($nmxPair in $nmxD.files.PSObject.Properties){if((Hash-Nmx $nmxPair.Name)-ne$nmxPair.Value){throw 'Carry preparation input changed'}};"+s[b:]
s=s.replace('(Get-ChildItem -LiteralPath $PSScriptRoot -File);','(Get-ChildItem -LiteralPath $PSScriptRoot -File);(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot \'native\') -File);')
s=s.replace("'-S',$PSScriptRoot,", "'-S',(Join-Path $PSScriptRoot 'native'),")
s=s.replace("'mw34_nmx_host_boundary.exe'", "'mw34_nmx_carry_native.exe'")
lines=s.splitlines();lines=[line for line in lines if "@('--check-publication'" not in line and 'foreach($nmxCorpus in' not in line]
s='\n'.join(lines)+'\n';s=s.replace("@('--unit',(Join-Path $nmxRoot", "@((Join-Path $nmxRoot")
s=s.replace("scope='NEW Session-owned numerical host boundary; direct captures precede harness cleanup; unchanged guest IR/domain/r9; independent comparison pending'", "scope='NEW authored carry-domain baseline/repair unit, no original execution; measured observer/independent acceptance pending'")
s=s.replace('runtime_r9=$nmxR9;', 'preparation=$nmxDerivative;preparation_sha256=$PreparationSHA256;runtime_r9=$nmxR9;')
out=Path(__file__).with_name('build_native.ps1');assert not out.exists();out.write_text(s);print(hashlib.sha256(out.read_bytes()).hexdigest())
