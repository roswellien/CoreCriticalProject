param(
    [Parameter(Mandatory=$true)][string]$TrialRoot,
    [Parameter(Mandatory=$true)][int]$ProducerId,
    [Parameter(Mandatory=$true)][string]$ProducerCreatedUtc
)
$ErrorActionPreference='Stop'
# Private sequential continuation only: wait for the existing producer, never
# start a second generation or deploy anything into the user's working runtime.
$trial=[IO.Path]::GetFullPath($TrialRoot)
$finish=Join-Path $trial 'FinishTrial'
$manifest=Get-Content -Raw -LiteralPath (Join-Path $finish 'inputs.json') | ConvertFrom-Json
function Check-Pin($pin) {
    if ((Get-FileHash -LiteralPath $pin.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.sha256) {
        throw "Private continuation input changed: $($pin.path)"
    }
}
try {
    foreach($pin in $manifest.files){Check-Pin $pin}
    Set-Content -LiteralPath (Join-Path $finish 'status.txt') -Value 'Waiting for the existing full body producer.'
    $deadline=[DateTime]::UtcNow.AddHours(8)
    while($true) {
        $producer=Get-CimInstance Win32_Process -Filter "ProcessId=$ProducerId"
        if (-not $producer) {break}
        if ($producer.CreationDate.ToUniversalTime().ToString('o') -ne $ProducerCreatedUtc) {break}
        if ([DateTime]::UtcNow -ge $deadline) {throw 'Full body preparation did not finish within the private trial window.'}
        Start-Sleep -Seconds 10
    }
    $receipt=Get-Content -Raw -LiteralPath (Join-Path $trial 'Bodies/generation.json') | ConvertFrom-Json
    if ($receipt.completed -ne 37201 -or -not $receipt.full_selected_body_set -or
        $receipt.recipe_sha256 -ne $manifest.body_recipe_sha256) {
        throw 'The complete selected body preparation did not succeed.'
    }
    foreach($pin in $manifest.files){Check-Pin $pin}
    Set-Content -LiteralPath (Join-Path $finish 'status.txt') -Value 'Full body generation succeeded. Linking private test runtime.'
    $vs='C:/Program Files/Microsoft Visual Studio/18/Community'
    Import-Module (Join-Path $vs 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')
    Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
    $arguments=@((Join-Path $finish 'local_link.py'),'link','--plan',(Join-Path $finish 'plan.json'),
        '--linker',$manifest.linker,'--output',(Join-Path $trial 'LinkedRuntime'))
    $process=Start-Process -FilePath $manifest.python -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru `
        -RedirectStandardOutput (Join-Path $finish 'link.stdout.log') -RedirectStandardError (Join-Path $finish 'link.stderr.log')
    if($process.ExitCode -ne 0){throw 'Private native link failed; inspect link logs.'}
    Set-Content -LiteralPath (Join-Path $finish 'status.txt') -Value 'Private native link succeeded. Actual startup test and distributable installer work remain pending. Working launcher unchanged.'
} catch {
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $finish 'failure.txt')
    Set-Content -LiteralPath (Join-Path $finish 'status.txt') -Value 'Private continuation stopped. Working launcher unchanged.'
    exit 1
}
