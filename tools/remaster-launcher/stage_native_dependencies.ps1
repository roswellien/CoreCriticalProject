param(
    [Parameter(Mandatory=$true)][string]$RuntimeDirectory,
    [Parameter(Mandatory=$true)][string]$RedistributableDirectory
)
# App-local prerequisites from an existing Microsoft installation. No download,
# system installation or generated game code is performed by this helper.
$ErrorActionPreference='Stop'
$RuntimeDirectory=[IO.Path]::GetFullPath($RuntimeDirectory)
$manifestPath=Join-Path $RuntimeDirectory 'runtime.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$files=@('msvcp140.dll','vcruntime140.dll','vcruntime140_1.dll')
$pins=@{}
foreach($name in $files){
    $source=Join-Path $RedistributableDirectory $name
    $signature=Get-AuthenticodeSignature -LiteralPath $source
    if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation'){
        throw "Expected a valid Microsoft redistributable signature: $name"
    }
    $target=Join-Path $RuntimeDirectory "bin/$name"
    if(Test-Path -LiteralPath $target){throw "Use a runtime without already-staged native prerequisites: $name"}
    $pins[$name]=@{source=$source;sha256=(Get-FileHash -LiteralPath $source).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $source).Length}
}
foreach($name in $files){
    $target=Join-Path $RuntimeDirectory "bin/$name"
    Copy-Item -LiteralPath $pins[$name].source -Destination $target
    if((Get-FileHash -LiteralPath $target).Hash.ToLowerInvariant() -ne $pins[$name].sha256){throw "Redistributable changed: $name"}
    $manifest.files | Add-Member -NotePropertyName "bin/$name" -NotePropertyValue @{bytes=$pins[$name].bytes;sha256=$pins[$name].sha256}
}
$manifest | ConvertTo-Json -Depth 45 | Set-Content -LiteralPath $manifestPath
$pins | ConvertTo-Json -Depth 5
