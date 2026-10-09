"""Fresh canonical-byte build, old recipe sources remain unchanged."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
s=Path(__file__).with_name('build_native.ps1').read_text()
s=s.replace('build/m4-nmx-carry-native-', 'build/m4-nmx-carry-canonical-')
s=s.replace("Join-Path $PSScriptRoot 'native'", "Join-Path $PSScriptRoot 'canonical'")
s=s.replace("'mw34_nmx_carry_native.exe'", "'mw34_nmx_canonical_carry.exe'")
needle='  $nmxBuilds.Add([ordered]@{level=$nmxLevel;directory=$nmxTrees[$nmxLevel];object=$nmxObject;worker=$nmxExe;unit_directory=$nmxUnit})'
assert s.count(needle)==1
extra="""  $nmxLegacyExe=Join-Path $nmxTrees[$nmxLevel] 'mw34_nmx_canonical_legacy.exe';$nmxLegacyUnit=Join-Path $nmxOut "legacy-unit-$nmxLevel"
  Run-Nmx $nmxLegacyExe @('--unit',(Join-Path $nmxRoot 'MW3/Mech3.exe'),(Join-Path $nmxRoot 'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'),$nmxObject,$nmxLegacyUnit) (Join-Path $nmxOut "legacy-unit-$nmxLevel.log")
  foreach($nmxCorpus in @('default','directed')){Run-Nmx $nmxLegacyExe @('--replay',(Join-Path $nmxRoot 'MW3/Mech3.exe'),(Join-Path $nmxRoot 'local/mw3-staged/Shared_DLLs/MSVCP50.DLL'),$nmxObject,(Join-Path $nmxRoot "reports/m4-fp-numeric-max/original-r5-normal-windows/$nmxCorpus.bin"),(Join-Path $nmxOut "legacy-replay-$nmxCorpus-$nmxLevel")) (Join-Path $nmxOut "legacy-replay-$nmxCorpus-$nmxLevel.log")}
  $nmxBuilds.Add([ordered]@{level=$nmxLevel;directory=$nmxTrees[$nmxLevel];object=$nmxObject;worker=$nmxExe;unit_directory=$nmxUnit;legacy_worker=$nmxLegacyExe;legacy_unit_directory=$nmxLegacyUnit})"""
s=s.replace(needle,extra)
s=s.replace("scope='NEW authored carry-domain baseline/repair unit, no original execution; measured observer/independent acceptance pending'", "scope='NEW canonical eleven-shadow-byte guard plus inherited separately measured carry/C1 repair, required outer numerical boundary; actual unit and frozen ORIGINAL BEFORE replays only; independent acceptance pending'")
out=Path(__file__).with_name('build_canonical.ps1');assert not out.exists();out.write_text(s)
