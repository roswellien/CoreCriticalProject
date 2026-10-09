param([Parameter(Mandatory=$true)][string]$OutputDirectory,[Parameter(Mandatory=$true)][string]$ExtractionDirectory)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major-lt7){throw 'PowerShell7 required before any output mutation'}
$spiRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$spiOut=[IO.Path]::GetFullPath($OutputDirectory);$spiExtract=[IO.Path]::GetFullPath($ExtractionDirectory)
if([IO.Path]::GetDirectoryName($spiOut)-ne(Join-Path $spiRoot 'reports/m4-spi-workarea')){throw 'Assigned immediate private report folder required'}
$spiName=Split-Path $spiOut -Leaf;if($spiName-notmatch '^[a-z0-9-]+$'){throw 'Simple fresh report name required'}
$spiBuild32=Join-Path $spiRoot "build/m4-spi-$spiName-x86";$spiBuild0=Join-Path $spiRoot "build/m4-spi-$spiName-O0";$spiBuild2=Join-Path $spiRoot "build/m4-spi-$spiName-O2"
foreach($spiPath in @($spiOut,$spiBuild32,$spiBuild0,$spiBuild2)){if(Test-Path -LiteralPath $spiPath){throw 'Existing report or derived build directory rejected before writes'}}
function SPI-Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$spiSources=[ordered]@{};foreach($spiPath in @($PSScriptRoot,(Join-Path $spiRoot 'runtime'),(Join-Path $spiRoot 'tools/m4-startup'))){foreach($spiFile in Get-ChildItem -LiteralPath $spiPath -Recurse -File){if($spiFile.Extension-in @('.h','.hpp','.cpp','.py','.ps1','.txt','.asm') -and $spiFile.FullName-notmatch '__pycache__'){$spiSources[$spiFile.FullName]=SPI-Hash $spiFile.FullName}}}
foreach($spiFile in Get-ChildItem -LiteralPath $spiExtract -File){$spiSources[$spiFile.FullName]=SPI-Hash $spiFile.FullName}
$spiCommands=[Collections.Generic.List[object]]::new();$spiTools=[ordered]@{};$spiPassed=$false
New-Item -ItemType Directory -Path $spiOut|Out-Null
foreach($spiPair in $spiSources.GetEnumerator()){$spiTarget=Join-Path $spiOut ('sources/'+[IO.Path]::GetRelativePath($spiRoot,$spiPair.Key));New-Item -ItemType Directory -Path (Split-Path $spiTarget -Parent) -Force|Out-Null;Copy-Item -LiteralPath $spiPair.Key -Destination $spiTarget}
function SPI-Run([string]$Program,[string[]]$Arguments,[string]$Log){$spiTools[$Program]=SPI-Hash $Program;$spiSaved=$ErrorActionPreference;$ErrorActionPreference='Continue';try{&$Program @Arguments 2>&1|Tee-Object -FilePath (Join-Path $spiOut $Log);$spiExit=$LASTEXITCODE}finally{$ErrorActionPreference=$spiSaved};$spiCommands.Add([ordered]@{program=$Program;arguments=$Arguments;exit_code=$spiExit;log=(Join-Path $spiOut $Log);log_sha256=(SPI-Hash (Join-Path $spiOut $Log))});if($spiExit-ne0){throw "SPI command failed exit=$spiExit log=$Log"}}
$spiVS='C:/Program Files/Microsoft Visual Studio/18/Community';$spiCMake=Join-Path $spiVS 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
try{
    Import-Module (Join-Path $spiVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $spiVS -SkipAutomaticLocation -DevCmdArguments '-arch=x86 -host_arch=x64'|Out-Null
    SPI-Run $spiCMake @('-S',$PSScriptRoot,'-B',$spiBuild32,'-G','Visual Studio 18 2026','-A','Win32',"-DMW34_SPI_INCLUDE=$spiExtract") 'x86-configure.log'
    SPI-Run $spiCMake @('--build',$spiBuild32,'--config','Release','--verbose') 'x86-build.log'
    foreach($spiTool in @('cl.exe','ml.exe','link.exe')){$spiPath=(Get-Command $spiTool).Source;$spiTools[$spiPath]=SPI-Hash $spiPath}
    Enter-VsDevShell -VsInstallPath $spiVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
    $spiClang=Join-Path $spiRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe';$spiRemill=Join-Path $spiRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include';$spiTools[$spiClang]=SPI-Hash $spiClang
    foreach($spiLevel in @('O0','O2')){$spiBuild=if($spiLevel-eq'O0'){$spiBuild0}else{$spiBuild2};$spiFlags=if($spiLevel-eq'O0'){'/Od /DNDEBUG -Wno-invalid- offsetof'}else{'/O2 /DNDEBUG -Wno-invalid- offsetof'};$spiFlags=$spiFlags.Replace('-Wno-invalid- offsetof','-Wno-invalid-offset'+'of')
        SPI-Run $spiCMake @('-S',$PSScriptRoot,'-B',$spiBuild,'-G','Ninja',"-DCMAKE_CXX_COMPILER=$spiClang",'-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_CXX_FLAGS_RELEASE=$spiFlags","-DMW34_SPI_INCLUDE=$spiExtract","-DMW34_REMILL_INCLUDE=$spiRemill") "$spiLevel-configure.log"
        SPI-Run $spiCMake @('--build',$spiBuild,'--parallel','8','--verbose') "$spiLevel-build.log"
    }
    foreach($spiPair in $spiSources.GetEnumerator()){if((SPI-Hash $spiPair.Key)-ne$spiPair.Value){throw 'Source changed during compile'}};$spiPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $spiOut 'failure.txt');throw}
finally{
    $spiArtifacts=[ordered]@{};foreach($spiFolder in @($spiOut,$spiBuild32,$spiBuild0,$spiBuild2)){if(Test-Path -LiteralPath $spiFolder){foreach($spiFile in Get-ChildItem -LiteralPath $spiFolder -Recurse -File){$spiArtifacts[$spiFile.FullName]=SPI-Hash $spiFile.FullName}}}
    [ordered]@{passed=$spiPassed;scope='Separate original/provider and typed native query compile only; no worker execution or connected startup credit';sources=$spiSources;commands=$spiCommands;tools=$spiTools;artifacts=$spiArtifacts;workers=@{original=(Join-Path $spiBuild32 'Release/mw34_spi_original.exe');O0=(Join-Path $spiBuild0 'mw34_spi_native.exe');O2=(Join-Path $spiBuild2 'mw34_spi_native.exe')};extraction=$spiExtract}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $spiOut 'build.json')
}
