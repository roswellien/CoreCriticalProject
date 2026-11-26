param([Parameter(Mandatory)][string]$Trust)
$ErrorActionPreference = 'Stop'
try {
    $utf8 = [Text.UTF8Encoding]::new($false, $true)
    [Console]::InputEncoding = $utf8
    [Console]::OutputEncoding = $utf8
    $raw = [Console]::In.ReadToEnd()
    if ($raw.Length -gt 1500000) { throw 'Catalog envelope exceeds limit' }
    $envelope = $raw | ConvertFrom-Json -AsHashtable -Depth 4
    if ($envelope.Count -ne 3 -or $envelope.key_id -isnot [string] -or
        $envelope.payload -isnot [string] -or $envelope.signature -isnot [string]) {
        throw 'Malformed catalog envelope'
    }
    $trusted = Get-Content -LiteralPath $Trust -Raw | ConvertFrom-Json -AsHashtable
    $pem = $trusted.public_keys[$envelope.key_id]
    if ($pem -isnot [string]) { throw 'Untrusted catalog key' }
    $payload = [Convert]::FromBase64String($envelope.payload)
    $signature = [Convert]::FromBase64String($envelope.signature)
    if ($payload.Length -gt 1048576) { throw 'Catalog payload exceeds limit' }
    $rsa = [Security.Cryptography.RSA]::Create()
    try {
        $rsa.ImportFromPem($pem)
        if ($rsa.KeySize -lt 3072 -or !$rsa.VerifyData(
                $payload, $signature, [Security.Cryptography.HashAlgorithmName]::SHA256,
                [Security.Cryptography.RSASignaturePadding]::Pss
            )) {
            throw 'Invalid catalog signature'
        }
        Write-Output ($utf8.GetString($payload))
    } finally {
        $rsa.Dispose()
    }
} catch {
    [Console]::Error.WriteLine('Unable to verify signed release catalog')
    exit 1
}
