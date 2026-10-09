param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major-lt7){throw 'PowerShell7 required'}
$spiRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$spiOut=[IO.Path]::GetFullPath($OutputDirectory)
if([IO.Path]::GetDirectoryName($spiOut)-ne(Join-Path $spiRoot 'reports/m4-spi-workarea') -or (Test-Path -LiteralPath $spiOut)){throw 'Fresh immediate private output required'}
function SPI-Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$spiSources=[ordered]@{};foreach($spiPath in @((Join-Path $spiRoot 'tools/m4-spi-workarea'),$PSScriptRoot,(Join-Path $spiRoot 'runtime'),(Join-Path $spiRoot 'tools/m4-startup'))){foreach($spiFile in Get-ChildItem -LiteralPath $spiPath -Recurse -File){if($spiFile.Extension-in @('.h','.hpp','.cpp','.py','.ps1','.txt','.asm') -and $spiFile.FullName-notmatch '__pycache__'){$spiSources[$spiFile.FullName]=SPI-Hash $spiFile.FullName}}}
$spiSpec=Join-Path $spiRoot 'reports/m4-spi-workarea/static-r1/spec.hpp';$spiSources[$spiSpec]=SPI-Hash $spiSpec
$spiVS='C:/Program Files/Microsoft Visual Studio/18/Community';Import-Module (Join-Path $spiVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $spiVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
$spiClang=Join-Path $spiRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe'
New-Item -ItemType Directory -Path $spiOut|Out-Null
foreach($spiPair in $spiSources.GetEnumerator()){$spiTarget=Join-Path $spiOut ('sources/'+[IO.Path]::GetRelativePath($spiRoot,$spiPair.Key));New-Item -ItemType Directory -Path (Split-Path $spiTarget -Parent) -Force|Out-Null;Copy-Item -LiteralPath $spiPair.Key -Destination $spiTarget}
$spiCommands=[Collections.Generic.List[object]]::new();$spiPassed=$false
try{foreach($spiLevel in @('O0','O2')){
    $spiFolder=Join-Path $spiOut $spiLevel;New-Item -ItemType Directory -Path $spiFolder|Out-Null;$spiExe=Join-Path $spiFolder 'bridge-controls.exe'
    $spiFlags=if($spiLevel-eq'O0'){'/Od'}else{'/O2'}
    $spiArgs=@('/nologo','/std:c++20','/EHsc','/MD',$spiFlags,'-Wno-invalid- offsetof'.Replace(' ','') ,'/DADDRESS_SIZE_BITS=32','/DHAS_FEATURE_AVX=0','/DHAS_FEATURE_AVX512=0',('/I'+(Join-Path $spiRoot 'reports/m4-spi-workarea/static-r1')),('/I'+(Join-Path $spiRoot 'tools/m4-spi-workarea')),('/I'+(Join-Path $spiRoot 'tools/m4-startup')),('/I'+(Join-Path $spiRoot 'runtime')),('/I'+(Join-Path $spiRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include')),('/Fo'+$spiFolder+'/'),('/Fe'+$spiExe),(Join-Path $PSScriptRoot 'bridge_controls.cpp'),(Join-Path $spiRoot 'tools/m4-startup/image_loader.cpp'),(Join-Path $spiRoot 'runtime/memory/guest_memory.cpp'),'/link','bcrypt.lib','user32.lib')
    &$spiClang @spiArgs 2>&1|Tee-Object -FilePath (Join-Path $spiFolder 'build.log');$spiExit=$LASTEXITCODE;$spiCommands.Add([ordered]@{command=@($spiClang)+$spiArgs;exit_code=$spiExit});if($spiExit-ne0){throw 'Authored control compile failed'}
    &$spiExe (Join-Path $spiRoot 'reports/m4-spi-workarea/static-r1/pack.bin') (Join-Path $spiRoot 'MW3/Mech3.exe') (Join-Path $spiFolder 'fixture-outputs') 2>&1|Tee-Object -FilePath (Join-Path $spiFolder 'controls.log');$spiExit=$LASTEXITCODE;$spiCommands.Add([ordered]@{command=@($spiExe,(Join-Path $spiRoot 'reports/m4-spi-workarea/static-r1/pack.bin'),(Join-Path $spiRoot 'MW3/Mech3.exe'),(Join-Path $spiFolder 'fixture-outputs'));exit_code=$spiExit});if($spiExit-ne0){throw 'Authored control execution failed'}
};foreach($spiPair in $spiSources.GetEnumerator()){if((SPI-Hash $spiPair.Key)-ne$spiPair.Value){throw 'Authored control source changed'}};$spiPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $spiOut 'failure.txt');throw}
finally{$spiArtifacts=[ordered]@{};foreach($spiFile in Get-ChildItem -LiteralPath $spiOut -Recurse -File){$spiArtifacts[$spiFile.FullName]=SPI-Hash $spiFile.FullName};[ordered]@{passed=$spiPassed;scope='Authored fault-injection query fixtures and real output ownership helper; no actual provider/game execution';sources=$spiSources;tools=@{$spiClang=(SPI-Hash $spiClang)};commands=$spiCommands;artifacts=$spiArtifacts}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $spiOut 'build.json')}
