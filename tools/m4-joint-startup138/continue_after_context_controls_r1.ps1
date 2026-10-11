# Serialize the next original138 run behind the currently admitted controls.
# This only launches the original worker if all 16 controls and their semantic
# verifier pass. It never opens a capture archive itself.
$ErrorActionPreference = 'Stop'
$project = 'D:\Projects\MW34Recomp'
$python = 'C:\Python314\python.exe'
$pidToWait = 22552
$expectedProcess = 'run_context_controls_v3.py.*context-controls-execution-r1'
$watch = Get-CimInstance Win32_Process -Filter "ProcessId=$pidToWait"
if (-not $watch -or $watch.CommandLine -notmatch $expectedProcess) {
    throw 'The expected admitted controls controller is not running; no follow-on worker launched.'
}
Write-Output 'Waiting for the admitted 16-case context controls batch to exit.'
while ($null -ne $watch) {
    Start-Sleep -Seconds 15
    $watch = Get-CimInstance Win32_Process -Filter "ProcessId=$pidToWait"
    if ($watch -and $watch.CommandLine -notmatch $expectedProcess) {
        throw 'The watched PID changed identity; no follow-on worker launched.'
    }
}

$controls = Join-Path $project 'reports\m4-joint-startup138\context-controls-execution-r1\report.json'
if (-not (Test-Path -LiteralPath $controls -PathType Leaf)) {
    throw 'Controls controller exited without a terminal report; no follow-on worker launched.'
}
$controlReceipt = Get-Content -LiteralPath $controls -Raw | ConvertFrom-Json
if (-not $controlReceipt.passed -or $controlReceipt.actual_workers_launched -ne 16 -or
    -not $controlReceipt.all_workers_terminal -or $controlReceipt.archive_reader_opened -or
    @($controlReceipt.runs | Where-Object { -not $_.passed }).Count -ne 0) {
    throw 'Controls did not pass all 16 runs; no follow-on worker launched.'
}
$controlSha = (Get-FileHash -LiteralPath $controls -Algorithm SHA256).Hash.ToLowerInvariant()
$checker = Join-Path $project 'tools\m4-joint-startup138\check_context_controls_v4.py'
Write-Output 'Running the independent whole-byteflow and retry verifier.'
& $python -B $checker $controls $controlSha 'context-controls-verification-r1'
if ($LASTEXITCODE -ne 0) { throw 'Independent controls verification failed; no original worker launched.' }

$build = Join-Path $project 'reports\m4-startup138-original\build-r4\build.json'
$buildSha = '748e6404963be6b5ef0a0aaeac80447023814ce46ff316962ea83a749b70ab69'
$review = Join-Path $project 'reports\m4-tree-review\original138-prelaunch-r5\report.json'
$reviewSha = 'efaa5d25802440f8cd47092d16a0368084cf5ea744d8c2cda5c826522f96122a'
$controller = Join-Path $project 'tools\m4-startup138-original\run_v2.py'
Write-Output 'Controls passed. Starting the reviewed six-sequence original138 capture.'
& $python -B $controller $build $buildSha $review $reviewSha 'original-execution-r1'
if ($LASTEXITCODE -ne 0) { throw 'Original138 capture did not pass its worker stage; validation remains pending.' }
Write-Output 'Original138 worker stage passed. Source and strict capture validation remain pending.'
