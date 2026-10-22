param(
    [Parameter(Mandatory=$true)][string[]]$File,
    [Parameter(Mandatory=$true)][string]$SignTool,
    [Parameter(Mandatory=$true)][string]$Dlib,
    [Parameter(Mandatory=$true)][string]$Metadata,
    [Parameter(Mandatory=$true)][string]$ReceiptPath
)
$ErrorActionPreference='Stop'
foreach ($path in @($SignTool,$Dlib,$Metadata)) {
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing signing input: $path" }
}
if (Test-Path -LiteralPath $ReceiptPath) { throw 'Use a fresh signing receipt path' }
$configuration=Get-Content -LiteralPath $Metadata -Raw | ConvertFrom-Json
if ($configuration.Endpoint -notmatch '^https://[a-z0-9]+\.codesigning\.azure\.net/?$' -or
    !$configuration.CodeSigningAccountName -or !$configuration.CertificateProfileName) { throw 'Invalid Artifact Signing metadata' }
$results=@()
foreach ($name in $File) {
    $path=[IO.Path]::GetFullPath($name)
    if (!(Test-Path -LiteralPath $path -PathType Leaf) -or (Get-Item -LiteralPath $path).Attributes.HasFlag([IO.FileAttributes]::ReparsePoint)) {
        throw "Signing target missing or linked: $path"
    }
    $before=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()
    $signature=Get-AuthenticodeSignature -LiteralPath $path
    $existing=$signature.Status -eq 'Valid'
    if (!$existing) {
        & $SignTool sign /v /fd SHA256 /tr http://timestamp.acs.microsoft.com /td SHA256 /dlib $Dlib /dmdf $Metadata $path
        if ($LASTEXITCODE) { throw "Windows signing failed: $path" }
        & $SignTool verify /pa /all /v $path
        if ($LASTEXITCODE) { throw "Windows signature verification failed: $path" }
        $signature=Get-AuthenticodeSignature -LiteralPath $path
        if ($signature.Status -ne 'Valid' -or !$signature.TimeStamperCertificate) { throw "Valid timestamped signature required: $path" }
    }
    $results+=@{path=$path;before_sha256=$before;sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant();
        retained_existing_signature=$existing;publisher=$signature.SignerCertificate.Subject;timestamped=[bool]$signature.TimeStamperCertificate}
}
@{profile=$configuration.CertificateProfileName;account=$configuration.CodeSigningAccountName;files=$results} |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReceiptPath -Encoding utf8
