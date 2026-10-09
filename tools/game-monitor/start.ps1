param(
    [ValidateSet('baseline','hook','attach')][string]$Mode = 'baseline',
    [string]$Game = 'D:/Projects/MW34Recomp/MW3/Mech3.exe',
    [string]$Python = 'C:/Python314/python.exe',
    [string]$HookRun,
    [int]$GamePid,
    [switch]$DebugAttach,
    [switch]$Passive
)
$ErrorActionPreference = 'Stop'
$mwRoot = (Resolve-Path "$PSScriptRoot/../..").Path
if ($Mode -ne 'attach') {
    $mwResolvedGame = (Resolve-Path -LiteralPath $Game).Path
    $mwExistingGame = Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -eq $mwResolvedGame }
    if ($mwExistingGame) { throw 'MW3 is already running; use -Mode attach -GamePid <PID>' }
}
$mwSession = "$mwRoot/reports/mw3-monitor/$(Get-Date -Format 'yyyyMMdd-HHmmss')-$([guid]::NewGuid().ToString('N').Substring(0,8))"
# Arguments are quoted as separate Windows process arguments, not shell code.
function Quote-MWArgument([string]$Value) {
    if ($Value.Contains('"') -or $Value.EndsWith('\')) { throw 'Unsupported quoted or trailing-backslash argument' }
    return '"' + $Value + '"'
}
$mwArgs = @("$PSScriptRoot/monitor.py", $(if ($Mode -eq 'attach') {'attach'} else {'launch'}),
            '--game', $Game, '--session', $mwSession)
if ($Mode -eq 'attach') {
    if ($GamePid -le 0) { throw 'Attach needs -GamePid' }
    $mwArgs += @('--pid', [string]$GamePid)
    if ($DebugAttach) { $mwArgs += '--debug' }
} else {
    $mwArgs += @('--mode', $Mode)
    if ($Passive) { $mwArgs += '--no-debug' }
}
if ($HookRun) { $mwArgs += @('--hook-run', $HookRun) }
if ($Mode -eq 'hook' -and -not $HookRun) { throw 'Hook mode needs a prepared -HookRun directory' }
$mwLogs = "$mwRoot/reports/mw3-monitor-launchers"
New-Item -ItemType Directory -Path $mwLogs -Force | Out-Null
$mwTag = [IO.Path]::GetFileName($mwSession)
$mwArguments = ($mwArgs | ForEach-Object { Quote-MWArgument $_ }) -join ' '
$mwCollector = Start-Process -FilePath $Python -ArgumentList $mwArguments -WorkingDirectory $mwRoot `
    -WindowStyle Hidden -PassThru -RedirectStandardOutput "$mwLogs/$mwTag.stdout.log" `
    -RedirectStandardError "$mwLogs/$mwTag.stderr.log"
Write-Output "Collector PID: $($mwCollector.Id)"
Write-Output "Session: $mwSession"
Write-Output "Status: & '$Python' '$PSScriptRoot/monitor.py' status '$mwSession'"
