param([Parameter(Mandatory=$true)][string]$AuthorBuild,[Parameter(Mandatory=$true)][string]$AuthorBuildSha,[Parameter(Mandatory=$true)][string]$FixtureDirectory,[Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$arRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'));$arBase=Join-Path $arRoot 'reports/m4-crt-locale-batch-review';$arOut=[IO.Path]::GetFullPath($OutputDirectory);$arFixture=[IO.Path]::GetFullPath($FixtureDirectory);$arAuthor=[IO.Path]::GetFullPath($AuthorBuild)
if([IO.Path]::GetDirectoryName($arOut)-ne$arBase-or(Test-Path -LiteralPath $arOut)-or[IO.Path]::GetDirectoryName($arFixture)-ne$arBase){throw 'Fresh reviewer compilation and owned fixture paths required'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
if((Hash $arAuthor)-ne$AuthorBuildSha){throw 'Externally frozen authored build identity required'}
$arBuild=Get-Content -Raw -LiteralPath $arAuthor|ConvertFrom-Json;$arGeneration=Join-Path $arFixture 'report.json';$arGen=Get-Content -Raw -LiteralPath $arGeneration|ConvertFrom-Json
if(-not$arBuild.passed-or-not$arGen.passed){throw 'Passed compiled author and independent fixture generation required'}
$arDefinitions=[ordered]@{};foreach($arCommand in $arBuild.commands){foreach($arArgument in $arCommand.arguments){if($arArgument-match'^[/-]D(MW34_(?:INITTERM_SOURCE|MAINARGS_RECOVERY|REPLAY_INPUT)_SHA)=(.+)$'){$arDefinitions[$Matches[1]]=$Matches[2].Trim('"')}}}
if($arDefinitions.Count-ne3){throw 'Three exact authored provenance macro definitions required'}
foreach($arPair in $arGen.files.PSObject.Properties){if((Hash $arPair.Name)-ne$arPair.Value){throw 'Independent fixture input changed'}}
$arObjects=[ordered]@{};foreach($arPair in $arBuild.entry_objects.PSObject.Properties){if((Hash $arPair.Name)-ne$arPair.Value){throw 'Authored literal guest COFF changed'};$arObjects[$arPair.Name]=$arPair.Value}
if($arObjects.Count-ne166){throw 'Exactly166 frozen literal guest COFFs required'}
$arLibraries=[ordered]@{};foreach($arPair in $arBuild.libraries.PSObject.Properties){if((Hash $arPair.Name)-ne$arPair.Value){throw 'Frozen FDIV library changed'};$arLibraries[$arPair.Name]=$arPair.Value}
if($arLibraries.Count-ne2){throw 'Exactly two prior FDIV libraries required'}
$arWriterPath=Join-Path $arRoot 'reports/m4-capture-direct/build-r4/build.json';$arWriter=Get-Content -Raw -LiteralPath $arWriterPath|ConvertFrom-Json
foreach($arPair in $arWriter.sources.PSObject.Properties){if((Hash $arPair.Name)-ne$arPair.Value){throw 'Canonical checked writer source changed'}}
foreach($arPair in $arWriter.objects.PSObject.Properties){if((Hash $arPair.Name)-ne$arPair.Value){throw 'Canonical checked writer object changed'}}
$arSources=[ordered]@{};foreach($arPair in $arBuild.sources.PSObject.Properties){if([IO.Path]::GetExtension($arPair.Name)-in@('.cpp','.hpp','.inc','.s','.ll')-or[IO.Path]::GetFileName($arPair.Name)-eq'CMakeLists.txt'){if((Hash $arPair.Name)-ne$arPair.Value){throw 'Frozen actual compile source changed'};$arSources[$arPair.Name]=$arPair.Value}}
foreach($arFile in Get-ChildItem -LiteralPath $arFixture -File|Where-Object{$_.Extension-in@('.cpp','.hpp','.inc')}){$arSources[$arFile.FullName]=Hash $arFile.FullName}
foreach($arPath in @((Join-Path $PSScriptRoot 'build.ps1'),(Join-Path $arRoot 'tools/m4-guest-cw/guest_cw.cpp'))){$arSources[$arPath]=Hash $arPath}
New-Item -ItemType Directory -Path $arOut|Out-Null
foreach($arPair in $arSources.GetEnumerator()){$arCopy=Join-Path $arOut ('sources/'+[IO.Path]::GetRelativePath($arRoot,$arPair.Key));New-Item -ItemType Directory -Force -Path (Split-Path $arCopy -Parent)|Out-Null;Copy-Item -LiteralPath $arPair.Key -Destination $arCopy;if((Hash $arCopy)-ne$arPair.Value){throw 'Exact private source snapshot'}}
$arVS='C:/Program Files/Microsoft Visual Studio/18/Community';$arLLVM=Join-Path $arRoot 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';$arClang=Join-Path $arLLVM 'clang-cl.exe';$arAsm=Join-Path $arLLVM 'clang.exe';$arLink=Join-Path $arLLVM 'lld-link.exe';$arCommands=[Collections.Generic.List[object]]::new();$arTools=[ordered]@{};$arWorkers=[ordered]@{};$arArtifacts=[ordered]@{};$arHeaders=[ordered]@{};$arPassed=$false
foreach($arPath in @($arClang,$arAsm,$arLink,(Join-Path $arVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll'),(Get-Process -Id $PID).Path)){$arTools[$arPath]=Hash $arPath}
function Run([string]$p,[string[]]$a,[string]$label){$arLog=Join-Path $arOut "$label.log";[IO.File]::WriteAllBytes($arLog,[byte[]]::new(0));&$p @a 2>&1|Tee-Object -FilePath $arLog|Out-Null;$arExit=$LASTEXITCODE;$arCommands.Add([ordered]@{program=$p;arguments=$a;exit_code=$arExit;log_path=$arLog;log_sha256=(Hash $arLog)});if($arExit-ne0){throw "Independent actual compiler failed: $label"}}
try{
 Import-Module (Join-Path $arVS 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll');Enter-VsDevShell -VsInstallPath $arVS -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64'|Out-Null
 foreach($arLevel in @('O0','O2')){
  $arFlag=if($arLevel-eq'O0'){'/Od'}else{'/O2'};$arEntry=@($arObjects.Keys|Where-Object{$_-match"candidate-$arLevel.obj$"});$arControl=@($arObjects.Keys|Where-Object{$_-match"control-$arLevel.obj$"});if($arEntry.Count-ne1-or$arControl.Count-ne1){throw 'Unique exact entry/control object identity'}
  $arCommon=@('/nologo','/std:c++20','/EHs','/MD','/showIncludes',$arFlag,'/DADDRESS_SIZE_BITS=32','/DHAS_FEATURE_AVX=0','/DHAS_FEATURE_AVX512=0',('/DMW34_ENTRY_OBJECT_SHA="{0}"'-f$arObjects[$arEntry[0]]),('/DMW34_CONTROL_OBJECT_SHA="{0}"'-f$arObjects[$arControl[0]]));foreach($arPair in $arDefinitions.GetEnumerator()){$arCommon+=('/D{0}="{1}"'-f$arPair.Key,$arPair.Value)}
  foreach($arDir in @($arFixture,(Join-Path $arRoot 'tools/m4-crt-locale-batch'),(Join-Path $arRoot 'tools/m4-capture-direct'),(Join-Path $arRoot 'tools/m4-crt'),(Join-Path $arRoot 'tools/m4-crt-fdiv'),(Join-Path $arRoot 'tools/m4-crt-commandline-native'),(Join-Path $arRoot 'tools/m4-runtime'),(Join-Path $arRoot 'tools/m4-startup'),(Join-Path $arRoot 'tools/m4-guest-cw'),(Join-Path $arRoot 'runtime'),(Join-Path $arRoot 'local/tools/remill-v6.0.1/remill-6.0.1/include'))){$arCommon+="/I$arDir"}
  $arFixtureObject=Join-Path $arOut "fixture-$arLevel.obj";$arCrtObject=Join-Path $arOut "crt-$arLevel.obj";$arCWObject=Join-Path $arOut "cw-$arLevel.obj";$arCapture=Join-Path $arOut "capture-$arLevel.obj";$arExe=Join-Path $arOut "locale_batch_review-$arLevel.exe"
  Run $arClang ($arCommon+@('/c',(Join-Path $arFixture 'composition.cpp'),"/Fo$arFixtureObject")) "fixture-$arLevel"
  Run $arClang ($arCommon+@('/c',(Join-Path $arFixture 'crt_services.cpp'),"/Fo$arCrtObject")) "crt-$arLevel"
  Run $arClang ($arCommon+@('/c',(Join-Path $arRoot 'tools/m4-guest-cw/guest_cw.cpp'),"/Fo$arCWObject")) "cw-$arLevel"
  Run $arAsm @('--target=x86_64-pc-windows-msvc','-c',(Join-Path $arRoot 'tools/m4-crt-allocation/capture.s'),'-o',$arCapture) "capture-$arLevel"
  $arArgs=@('/nologo',"/out:$arExe",$arFixtureObject,$arCrtObject,$arCWObject,$arCapture,(Join-Path $arRoot "reports/m4-capture-direct/build-r4/capture_direct-$arLevel.obj"),(Join-Path $arRoot 'reports/m4-capture-direct/build-r4/preserve.obj'),'bcrypt.lib','kernel32.lib')
  $arArgs+=@($arObjects.Keys|Where-Object{$_-match"-$arLevel.obj$"});$arArgs+=@($arLibraries.Keys|Where-Object{$_-match"-$arLevel/|-$arLevel\\"});foreach($arDir in($env:LIB-split';')){$arArgs+="/libpath:$arDir"};Run $arLink $arArgs "link-$arLevel";$arWorkers[$arLevel]=$arExe
 }
 foreach($arPair in $arSources.GetEnumerator()){if((Hash $arPair.Key)-ne$arPair.Value){throw 'Compile dependency changed during build'}};$arPassed=$true
}catch{$_|Out-String|Set-Content -LiteralPath (Join-Path $arOut 'failure.txt');throw}
finally{
 foreach($arLog in Get-ChildItem -LiteralPath $arOut -Filter '*.log' -File){foreach($arLine in Get-Content -LiteralPath $arLog.FullName){if($arLine-match'Note: including file:\s*(.+?)\s*$'){$arPath=$Matches[1].Trim();if(Test-Path -LiteralPath $arPath){$arHeaders[[IO.Path]::GetFullPath($arPath)]=Hash $arPath}}}}
 foreach($arFile in Get-ChildItem -LiteralPath $arOut -Recurse -File){$arArtifacts[$arFile.FullName]=Hash $arFile.FullName}
 [ordered]@{passed=$arPassed;author_build=$arAuthor;author_build_sha256=$AuthorBuildSha;fixture_report=$arGeneration;fixture_report_sha256=(Hash $arGeneration);writer_build=$arWriterPath;writer_build_sha256=(Hash $arWriterPath);sources=$arSources;tools=$arTools;entry_objects=$arObjects;libraries=$arLibraries;compiler_read_headers=$arHeaders;artifacts=$arArtifacts;workers=$arWorkers;commands=@($arCommands);native_executed=$false;source_bodies_modified=$false;API_response_injection=$false;scope='Fresh independent source/ABI compilation;166 literal guest COFFs unchanged; checked native direct transport; no execution'}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $arOut 'build.json')
}
