param([string]$LLVMRoot, [string]$RemillRoot,
      [string]$VSRoot = 'C:/Program Files/Microsoft Visual Studio/18/Community',
      [string]$Python = 'C:/Python314/python.exe')
$ErrorActionPreference = 'Stop'
$mwPowerShell = (Get-Process -Id $PID).Path
foreach ($mwKind in @('add', 'branch', 'memory', 'shift')) {
    # Each developer-shell setup stays inside its child process. Repeating it
    # in one session otherwise accumulates PATH/SDK entries until cmd exceeds
    # its command-line limit, especially when a game build follows this suite.
    $mwArguments = @('-NoProfile', '-File', "$PSScriptRoot/build_fixture.ps1",
                     '-FixtureKind', $mwKind, '-RunComparison',
                     '-VSRoot', $VSRoot, '-Python', $Python)
    if ($LLVMRoot) { $mwArguments += @('-LLVMRoot', $LLVMRoot) }
    if ($RemillRoot) { $mwArguments += @('-RemillRoot', $RemillRoot) }
    & $mwPowerShell @mwArguments
    if ($LASTEXITCODE -ne 0) { throw "Fixture suite failed: $mwKind" }
}
& $Python "$PSScriptRoot/verify_fixture_suite.py"
if ($LASTEXITCODE -ne 0) { throw 'Fixture evidence verification failed' }
