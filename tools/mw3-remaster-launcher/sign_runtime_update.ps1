param(
    [Parameter(Mandatory=$true)][string]$Manifest,
    [Parameter(Mandatory=$true)][string]$SigningKey,
    [Parameter(Mandatory=$true)][string]$KeyId,
    [Parameter(Mandatory=$true)][string]$OutputFile
)
# Release-owner operation: the private key stays local, outside publication inputs.
# Signs update metadata, including the owner-authorized private precompiled
# runtime route. Original media and provider images remain outside the package.
$ErrorActionPreference='Stop'
if (Test-Path -LiteralPath $OutputFile) { throw 'Use a fresh signed update output file' }
$payload=[IO.File]::ReadAllBytes([IO.Path]::GetFullPath($Manifest))
if ($payload.Length -gt 1048576) { throw 'Update manifest is too large' }
$null=[Text.Encoding]::UTF8.GetString($payload) | ConvertFrom-Json
$rsa=[Security.Cryptography.RSA]::Create()
try {
    $rsa.ImportFromPem([IO.File]::ReadAllText([IO.Path]::GetFullPath($SigningKey)))
    if ($rsa.KeySize -lt 3072) { throw 'An RSA signing key of at least 3072 bits is required' }
    $signature=$rsa.SignData($payload,[Security.Cryptography.HashAlgorithmName]::SHA256,[Security.Cryptography.RSASignaturePadding]::Pss)
    $envelope=@{key_id=$KeyId;payload=[Convert]::ToBase64String($payload);signature=[Convert]::ToBase64String($signature)} | ConvertTo-Json
    $stream=[IO.File]::Open([IO.Path]::GetFullPath($OutputFile),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try {
        $bytes=[Text.Encoding]::UTF8.GetBytes($envelope)
        $stream.Write($bytes,0,$bytes.Length)
        $stream.Flush($true)
    } finally { $stream.Dispose() }
} finally { $rsa.Dispose() }
Write-Output "Signed update metadata: $OutputFile"
