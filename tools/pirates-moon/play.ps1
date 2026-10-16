param(
    [string]$Installation='MW3-PiratesMoon',
    [string]$Build='build/pirates-moon-native-r1',
    [int]$Frames=0,
    [int]$Dump=0,
    [string]$Script='',
    [int]$Clock=0,
    [string]$MediaDrive='',
    [string]$Registry='games/mw3-pirates-moon/config/native-registry.txt',
    [switch]$NoFmv,
    [switch]$Hidden
)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Set-Location $root
$runningGames=@(Get-Process -Name entry_commandline,pirates_moon_native,Mech3 -ErrorAction SilentlyContinue)
if($runningGames.Count){throw ('A game session is already running: '+(($runningGames | ForEach-Object {"$($_.ProcessName) PID $($_.Id)"}) -join ', ')+'. Close it normally first.')}
$source=(Resolve-Path -LiteralPath $Installation).Path
$exe=(Resolve-Path -LiteralPath (Join-Path $Build 'shared-host/pirates_moon_native.exe')).Path
& python -B (Join-Path $PSScriptRoot 'target.py') $source --native-assets | Out-Null
if($LASTEXITCODE){throw 'PM input identity check failed'}
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$stage=Join-Path $root "local/pirates-moon/play-$stamp"
$out=Join-Path $root "reports/pirates-moon/play-$stamp"
if((Test-Path -LiteralPath $stage) -or (Test-Path -LiteralPath $out)){throw 'Fresh PM run namespace required'}
New-Item -ItemType Directory -Path $stage | Out-Null
New-Item -ItemType Directory -Path $out | Out-Null
# Only this run's root files are writable. Original media and asset banks remain local.
Get-ChildItem -LiteralPath $source -File | ForEach-Object {Copy-Item -LiteralPath $_.FullName -Destination $stage}
Get-ChildItem -LiteralPath $source -Directory | ForEach-Object {New-Item -ItemType Junction -Path (Join-Path $stage $_.Name) -Target $_.FullName | Out-Null}
$env:MW34_FRAME_BUDGET="$Frames"
$env:MW34_FRAME_DUMP="$Dump"
$env:MW34_HIDE_WINDOW=if($Hidden){'1'}else{'0'}
$env:MW34_GPU_HUD='0'
$env:MW34_PM_NOFMV=if($NoFmv){'1'}else{'0'}
$env:MW34_REG_OVERLAY=Join-Path $stage 'mw34-registry.txt'
if($Registry){Copy-Item -LiteralPath (Resolve-Path -LiteralPath $Registry).Path -Destination $env:MW34_REG_OVERLAY}
$env:MW34_STARTUP='loader'
$env:MW34_SEED='host'
# Diagnostics and configuration from base-MW3 scripted/codec experiments must be selected for PM separately.
Remove-Item Env:MW34_INPUT_SCRIPT,Env:MW34_VIRTUAL_CLOCK,Env:MW34_SEH_TEST,Env:MW34_MUSIC_PACK -ErrorAction SilentlyContinue
if($Script){$env:MW34_INPUT_SCRIPT=(Resolve-Path -LiteralPath $Script).Path}
if($Clock){if(-not $Script -or $Clock -lt 1 -or $Clock -gt 1000){throw 'PM virtual clock requires -Script and -Clock 1..1000'};$env:MW34_VIRTUAL_CLOCK="$Clock"}
$launchArguments=@('"'+$stage+'"','"'+(Join-Path $out 'execution')+'"')
$mediaTarget=''
try {
 if($MediaDrive){
  # The retail check opens the first matching CD file before checking its contents.
  # A user-level DOS alias orders the selected actual CD before the base-MW3 CD.
  # Windows still supplies drive enumeration/type and the original code checks media.
  if($MediaDrive -notmatch '^[A-Za-z]:\\?$'){throw '-MediaDrive must be a mounted CD drive, such as H:'}
  if(-not ('MW34PmMedia' -as [type])){Add-Type -TypeDefinition @'
using System; using System.Text; using System.Runtime.InteropServices;
public static class MW34PmMedia {
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern uint GetDriveType(string root);
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern uint QueryDosDevice(string name,StringBuilder value,int size);
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern bool DefineDosDevice(uint flags,string name,string target);
}
'@}
  $drive=$MediaDrive.Substring(0,2).ToUpperInvariant()
  if([MW34PmMedia]::GetDriveType($drive+'\') -ne 5){throw 'Selected media must be an actual mounted CD volume'}
  $query=[Text.StringBuilder]::new(4096)
  if(-not [MW34PmMedia]::QueryDosDevice($drive,$query,4096)){throw 'Selected CD device is unavailable'}
  $selected=$query.ToString()
  if([MW34PmMedia]::QueryDosDevice('B:',[Text.StringBuilder]::new(4096),4096)){throw 'B: is occupied; no media alias was changed'}
  if([Runtime.InteropServices.Marshal]::GetLastWin32Error() -ne 2){throw 'Could not establish that B: is unused; no media alias was changed'}
  if(-not [MW34PmMedia]::DefineDosDevice(9,'B:',$selected)){throw 'Could not create a user-level alias of the selected CD'}
  $mediaTarget=$selected
  Write-Output "PM media: B: aliases $drive ($selected) for this run; launcher waits for shutdown"
 }
 $process=Start-Process -FilePath $exe -ArgumentList $launchArguments -WorkingDirectory $stage -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $out 'stdout.log') -RedirectStandardError (Join-Path $out 'stderr.log')
 Write-Output "PM native PID $($process.Id); output $out; writable installation $stage"
 if($mediaTarget){$process.WaitForExit();Write-Output "PM native exit=$($process.ExitCode)"}
} finally {
 if($mediaTarget -and -not [MW34PmMedia]::DefineDosDevice(15,'B:',$mediaTarget)){Write-Warning 'The PM media alias B: could not be removed'}
}
